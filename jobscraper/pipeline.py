from __future__ import annotations

from typing import Any

from jobscraper.database import (
    JobRepository,
    create_engine,
    create_session_factory,
)
from jobscraper.lifecycle import JobRowLifecycle
from jobscraper.models import (
    JobProvider,
    JobSearchRequest,
    ProviderFetchError,
    RoleSearchConfig,
)
from jobscraper.roles import ROLE_CATALOG
from jobscraper.settings import ScraperSettings
from jobscraper.storage import FINAL_SOURCE_COLUMNS, CsvJobStore


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
        self.lifecycle = JobRowLifecycle(self.settings)
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
            try:
                rows = [dict(row) for row in await provider.fetch(request)]
            except ProviderFetchError as exc:
                self.store.write_raw(output, [])
                print(f"Fetch failed; skipping search: {exc}")
                print(f"\n{output.name}")
                print("fetch_error=1")
                continue
            print(f"Found {len(rows)} jobs for {role_config.role}: {search.name}")

            lifecycle_result = self.lifecycle.process(
                rows,
                role=role_config.role,
                provider=request.provider,
            )
            if self.session_factory is not None:
                async with self.session_factory() as session:
                    repository = JobRepository(session)
                    run = await repository.start_search_run(request)
                    await repository.upsert_raw_jobs(
                        run=run,
                        rows=lifecycle_result.source_rows,
                    )
                    await repository.finish_search_run(
                        run.id,
                        len(lifecycle_result.source_rows),
                    )
                    await repository.upsert_normalized_jobs(
                        run=run,
                        rows=lifecycle_result.normalized_rows,
                    )
                    await repository.expire_old_jobs()
                    await session.commit()

            role_rows.extend(
                row for row in lifecycle_result.normalized_rows if row["is_active"]
            )
            written = self.store.write_raw(output, lifecycle_result.source_rows)
            if written:
                print(f"Saved {output}")

            print(f"\n{output.name}")
            for key, value in lifecycle_result.reasons.items():
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
