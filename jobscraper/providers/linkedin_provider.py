from __future__ import annotations

import asyncio
from typing import Any, Sequence

from jobscraper.models import JobRow, JobSearchRequest
from jobscraper.settings import ScraperSettings


class LinkedInScraperProvider:
    """Adapter for joeyism/linkedin_scraper.

    This is intentionally lazy-loaded so the default Indeed pipeline does not require
    Playwright/browser dependencies until LinkedIn scraping is enabled.
    """

    name = "linkedin"

    def __init__(self, settings: ScraperSettings) -> None:
        self.settings = settings

    async def fetch(self, request: JobSearchRequest) -> Sequence[JobRow]:
        if self.settings.linkedin_session_path is None:
            raise RuntimeError(
                "LINKEDIN_SESSION_PATH is required when JOB_PROVIDERS includes linkedin"
            )

        return await self._fetch_async(request)

    async def _fetch_async(self, request: JobSearchRequest) -> list[JobRow]:
        try:
            from linkedin_scraper import (
                BrowserManager,
                JobScraper as LinkedInJobScraper,
                JobSearchScraper,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Install linkedin_scraper from "
                "https://github.com/joeyism/linkedin_scraper.git to enable LinkedIn"
            ) from exc

        async with BrowserManager(headless=self.settings.linkedin_headless) as browser:
            await browser.load_session(str(self.settings.linkedin_session_path))
            search_scraper = JobSearchScraper(browser.page)
            job_urls = await search_scraper.search(
                keywords=request.search_term,
                location=request.location,
                limit=request.results_wanted,
            )

            job_scraper = LinkedInJobScraper(browser.page)
            rows: list[JobRow] = []
            for job_url in job_urls:
                try:
                    job = await job_scraper.scrape(job_url)
                except Exception as exc:
                    rows.append(
                        {
                            "site": self.name,
                            "job_url_direct": job_url,
                            "scrape_error": str(exc),
                        }
                    )
                    continue

                rows.append(self._normalize_job(job, request))

        return rows

    def _normalize_job(self, job: Any, request: JobSearchRequest) -> JobRow:
        if hasattr(job, "model_dump"):
            raw = job.model_dump()
        elif hasattr(job, "__dict__"):
            raw = dict(job.__dict__)
        else:
            raw = {"raw": repr(job)}

        return {
            "site": self.name,
            "title": raw.get("job_title", raw.get("title", "")),
            "company": raw.get("company", ""),
            "company_linkedin_url": raw.get("company_linkedin_url", ""),
            "location": raw.get("location", request.location),
            "is_remote": raw.get("is_remote", ""),
            "job_type": raw.get("job_type", raw.get("employment_type", "")),
            "date_posted": raw.get("posted_date", raw.get("date_posted", "")),
            "job_url_direct": raw.get(
                "linkedin_url", raw.get("job_url", raw.get("url", ""))
            ),
            "min_amount": raw.get("min_amount", ""),
            "max_amount": raw.get("max_amount", ""),
            "description": raw.get("job_description", raw.get("description", "")),
            "applicant_count": raw.get("applicant_count", ""),
            "benefits": raw.get("benefits", ""),
            "raw": raw,
        }
