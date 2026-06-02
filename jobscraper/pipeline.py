from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from jobscraper.database import (
    JobRepository,
    create_engine,
    create_session_factory,
    source_key_for_row,
)
from jobscraper.filters import (
    ALLOWED_JOB_TYPES,
    exclusion_reason,
    is_relevant,
    parse_posted_at,
)
from jobscraper.models import JobProvider, JobSearchRequest, RoleSearchConfig
from jobscraper.roles import ROLE_CATALOG
from jobscraper.settings import ScraperSettings
from jobscraper.storage import FINAL_SOURCE_COLUMNS, CsvJobStore
from jobscraper.tags import extract_tags


class JobScraper:
    def __init__(
        self,
        *,
        settings: ScraperSettings,
        providers: dict[str, JobProvider],
        role_catalog: dict[str, RoleSearchConfig] | None = None,
    ) -> None:
        self.settings = settings
        self.providers = providers
        self.role_catalog = role_catalog or ROLE_CATALOG
        self.store = CsvJobStore(
            temp_dir=self.settings.temp_dir,
            final_dir=self.settings.final_dir,
        )
        self.engine = (
            create_engine(self.settings.database_url)
            if self.settings.database_enabled
            else None
        )
        self.session_factory = (
            create_session_factory(self.engine) if self.engine is not None else None
        )

    async def run(self) -> None:
        final_rows_by_role = await self.scrape_searches()
        await self.write_final_csvs(final_rows_by_role)
        if self.engine is not None:
            await self.engine.dispose()

    async def scrape_searches(self) -> dict[str, list[dict[str, Any]]]:
        final_rows_by_role = {}
        for role_config in self.role_catalog.values():
            final_rows_by_role[role_config.role] = await self.scrape_role(role_config)
        return final_rows_by_role

    async def scrape_role(self, role_config: RoleSearchConfig) -> list[dict[str, Any]]:
        role_rows: list[dict[str, Any]] = []
        for search in role_config.searches:
            if search.provider not in self.settings.enabled_providers:
                continue

            provider = self.providers.get(search.provider)
            if provider is None:
                raise ValueError(f"No provider registered for {search.provider!r}")
            request = JobSearchRequest(
                role=role_config.role,
                search_name=search.name,
                search_term=search.term,
                provider=search.provider,
                location=self.settings.location,
                results_wanted=self.settings.results_wanted,
                hours_old=self.settings.hours_old,
                country_indeed=self.settings.country_indeed,
            )
            output = self.store.raw_output_path(role_config.role, search)

            print(f"\n=== Running {role_config.role}: {search.name} ({search.provider}) ===")
            print(search.term)
            rows = [dict(row) for row in await provider.fetch(request)]
            print(f"Found {len(rows)} jobs for {role_config.role}: {search.name}")

            source_rows, reasons = self.prepare_source_rows(rows, request.provider)
            normalized_rows, filter_reasons = self.filter_rows(
                source_rows,
                role_config.role,
                request.provider,
            )
            reasons.update(filter_reasons)
            if self.session_factory is not None:
                async with self.session_factory() as session:
                    repository = JobRepository(session)
                    run = await repository.start_search_run(request)
                    await repository.upsert_raw_jobs(run=run, rows=source_rows)
                    await repository.finish_search_run(run.id, len(source_rows))
                    await repository.upsert_normalized_jobs(
                        run=run,
                        rows=normalized_rows,
                    )
                    await repository.expire_old_jobs()
                    await session.commit()

            role_rows.extend(row for row in normalized_rows if row["is_active"])
            written = self.store.write_raw(output, source_rows)
            if written:
                print(f"Saved {output}")

            print(f"\n{output.name}")
            for key, value in reasons.items():
                print(f"{key}={value}")

        return role_rows

    async def write_final_csvs(
        self,
        final_rows_by_role: dict[str, list[dict[str, Any]]],
    ) -> None:
        for role_config in self.role_catalog.values():
            rows = final_rows_by_role.get(role_config.role, [])
            final_rows = self._dedupe_and_sort(rows)
            final_output = role_config.final_output_path(self.settings.final_dir)
            self.store.write_final(final_output, final_rows)

            print(f"\n=== Final CSV: {role_config.role} ===")
            print(f"candidate_rows_before_dedupe={len(rows)}")
            print(f"final_rows={len(final_rows)}")
            print(f"exact_direct_url_duplicates_removed={len(rows) - len(final_rows)}")
            print(f"output={final_output}")

    def prepare_source_rows(
        self,
        rows: list[dict[str, Any]],
        provider: str,
    ) -> tuple[list[dict[str, Any]], Counter]:
        source_rows: list[dict[str, Any]] = []
        reasons = Counter()

        for row in rows:
            direct_url = str(row.get("job_url_direct") or "").strip()
            if not direct_url:
                reasons["missing_direct_url"] += 1
                continue

            source_key = source_key_for_row(provider, row)
            if not source_key:
                reasons["missing_source_key"] += 1
                continue

            source_rows.append({**row, "source_key": source_key})

        return source_rows, reasons

    def filter_rows(
        self,
        rows: list[dict[str, Any]],
        role: str,
        provider: str,
    ) -> tuple[list[dict[str, Any]], Counter]:
        normalized_rows: list[dict[str, Any]] = []
        reasons = Counter()
        now = datetime.now(UTC)

        for row in rows:
            posted_at = parse_posted_at(row.get("date_posted"), now=now)
            if not posted_at:
                reasons["missing_or_invalid_date_posted"] += 1
                continue

            direct_url = str(row.get("job_url_direct") or "").strip()
            if not direct_url:
                reasons["missing_direct_url"] += 1
                continue

            job_type = str(row.get("job_type") or "").strip().lower()
            if job_type not in ALLOWED_JOB_TYPES:
                reasons["excluded_job_type"] += 1
                continue

            reason = exclusion_reason(row)
            if reason:
                reasons[reason] += 1
                continue

            if not is_relevant(row, role):
                reasons["not_relevant"] += 1
                continue

            cleaned_row = {
                column: str(row.get(column) or "").strip()
                for column in FINAL_SOURCE_COLUMNS
            }
            expires_at = posted_at + timedelta(hours=self.settings.max_job_age_hours)
            is_active = expires_at > now
            cleaned_row["provider"] = provider
            cleaned_row["source_key"] = row["source_key"]
            cleaned_row["date_posted"] = posted_at.date()
            cleaned_row["posted_at"] = posted_at
            cleaned_row["expires_at"] = expires_at
            cleaned_row["is_active"] = is_active
            cleaned_row["expired_at"] = None if is_active else now
            cleaned_row["inactive_reason"] = None if is_active else "posted_age_exceeded"
            cleaned_row["tags"] = extract_tags(provider, row)
            normalized_rows.append(cleaned_row)
            reasons["kept_before_dedupe"] += 1

        return normalized_rows, reasons

    def _dedupe_and_sort(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_url: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = f"{row.get('provider', '')}:{row['source_key']}"
            if key not in by_url:
                by_url[key] = row
                continue

            existing = by_url[key]
            for column in FINAL_SOURCE_COLUMNS:
                if not existing.get(column) and row.get(column):
                    existing[column] = row[column]

        final_rows = list(by_url.values())
        final_rows.sort(
            key=lambda row: (
                row.get("date_posted").isoformat() if row.get("date_posted") else "",
                row.get("company") or "",
                row.get("title") or "",
                row.get("location") or "",
            ),
            reverse=True,
        )
        return [
            {
                **row,
                "date_posted": row["date_posted"].isoformat()
                if row.get("date_posted")
                else "",
            }
            for row in final_rows
        ]
