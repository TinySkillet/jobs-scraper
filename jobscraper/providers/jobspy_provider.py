from __future__ import annotations

import asyncio
from typing import Any, Sequence

from jobscraper.async_utils import run_blocking
from jobscraper.models import JobRow, JobSearchRequest, ProviderFetchError
from jobscraper.settings import ScraperSettings


def prefer_recent_indeed_results() -> None:
    """JobSpy defaults Indeed pagination to relevance; date sort keeps short runs fresh."""
    try:
        import jobspy.indeed as indeed_module
        import jobspy.indeed.constant as indeed_constant
    except ImportError:
        return

    for module in (indeed_module, indeed_constant):
        query = getattr(module, "job_search_query", "")
        if "sort: RELEVANCE" in query:
            module.job_search_query = query.replace("sort: RELEVANCE", "sort: DATE")


class JobSpyProvider:
    name = "indeed"

    def __init__(self, settings: ScraperSettings | None = None) -> None:
        self.fetch_retries = 2 if settings is None else settings.provider_fetch_retries
        self.retry_backoff_seconds = (
            2.0 if settings is None else settings.provider_retry_backoff_seconds
        )
        prefer_recent_indeed_results()

    async def fetch(self, request: JobSearchRequest) -> Sequence[JobRow]:
        attempts = max(0, self.fetch_retries) + 1
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return await run_blocking(self._fetch_sync, request)
            except _transient_fetch_errors() as exc:
                last_error = exc
                if attempt == attempts:
                    break
                delay = self.retry_backoff_seconds * attempt
                print(
                    f"{self.name} fetch failed for {request.search_name} "
                    f"(attempt {attempt}/{attempts}): {exc}; retrying in {delay:g}s"
                )
                await asyncio.sleep(delay)

        raise ProviderFetchError(
            provider=self.name,
            search_name=request.search_name,
            attempts=attempts,
            cause=last_error or RuntimeError("unknown fetch failure"),
        )

    def _fetch_sync(self, request: JobSearchRequest) -> Sequence[JobRow]:
        from jobspy import scrape_jobs

        jobs = scrape_jobs(
            site_name=[self.name],
            search_term=request.search_term,
            location=request.location,
            verbose=1,
            results_wanted=request.results_wanted,
            hours_old=request.hours_old,
            country_indeed=request.country_indeed,
        )

        if jobs.empty:
            return []

        records: list[dict[str, Any]] = jobs.fillna("").to_dict("records")
        for record in records:
            record.setdefault("site", self.name)
        return records


def _transient_fetch_errors() -> tuple[type[BaseException], ...]:
    try:
        import requests
        import urllib3
    except ImportError:
        return (TimeoutError,)

    return (
        TimeoutError,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.ChunkedEncodingError,
        urllib3.exceptions.TimeoutError,
    )
