from __future__ import annotations

from typing import Any, Sequence

from jobscraper.async_utils import run_blocking
from jobscraper.models import JobRow, JobSearchRequest


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

    def __init__(self) -> None:
        prefer_recent_indeed_results()

    async def fetch(self, request: JobSearchRequest) -> Sequence[JobRow]:
        return await run_blocking(self._fetch_sync, request)

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
