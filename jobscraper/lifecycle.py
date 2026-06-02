from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from jobscraper.database import source_key_for_row
from jobscraper.filters import (
    ALLOWED_JOB_TYPES,
    exclusion_reason,
    is_relevant,
    parse_posted_at,
)
from jobscraper.settings import ScraperSettings
from jobscraper.storage import FINAL_SOURCE_COLUMNS
from jobscraper.tags import extract_tags


@dataclass(frozen=True)
class JobRowLifecycleResult:
    source_rows: list[dict[str, Any]]
    normalized_rows: list[dict[str, Any]]
    reasons: Counter


class JobRowLifecycle:
    def __init__(self, settings: ScraperSettings) -> None:
        self.settings = settings

    def process(
        self,
        rows: list[dict[str, Any]],
        *,
        role: str,
        provider: str,
        now: datetime | None = None,
    ) -> JobRowLifecycleResult:
        now = _utc_now(now)
        source_rows, reasons = self.prepare_source_rows(rows, provider)
        normalized_rows, filter_reasons = self.normalize_source_rows(
            source_rows,
            role=role,
            provider=provider,
            now=now,
        )
        reasons.update(filter_reasons)
        return JobRowLifecycleResult(
            source_rows=source_rows,
            normalized_rows=normalized_rows,
            reasons=reasons,
        )

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

    def normalize_source_rows(
        self,
        rows: list[dict[str, Any]],
        *,
        role: str,
        provider: str,
        now: datetime,
    ) -> tuple[list[dict[str, Any]], Counter]:
        normalized_rows: list[dict[str, Any]] = []
        reasons = Counter()

        for row in rows:
            normalized_row = self._normalize_source_row(
                row,
                role=role,
                provider=provider,
                now=now,
                reasons=reasons,
            )
            if normalized_row is None:
                continue

            normalized_rows.append(normalized_row)
            reasons["kept_before_dedupe"] += 1

        return normalized_rows, reasons

    def _normalize_source_row(
        self,
        row: dict[str, Any],
        *,
        role: str,
        provider: str,
        now: datetime,
        reasons: Counter,
    ) -> dict[str, Any] | None:
        posted_at = parse_posted_at(row.get("date_posted"), now=now)
        if not posted_at:
            reasons["missing_or_invalid_date_posted"] += 1
            return None

        if posted_at < now - timedelta(hours=self.settings.hours_old):
            reasons["outside_hours_old_window"] += 1
            return None

        direct_url = str(row.get("job_url_direct") or "").strip()
        if not direct_url:
            reasons["missing_direct_url"] += 1
            return None

        job_type = str(row.get("job_type") or "").strip().lower()
        if job_type not in ALLOWED_JOB_TYPES:
            reasons["excluded_job_type"] += 1
            return None

        reason = exclusion_reason(row)
        if reason:
            reasons[reason] += 1
            return None

        if not is_relevant(row, role):
            reasons["not_relevant"] += 1
            return None

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
        return cleaned_row


def _utc_now(now: datetime | None) -> datetime:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC)
    return now.astimezone(UTC)
