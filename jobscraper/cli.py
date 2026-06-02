from __future__ import annotations

import asyncio

from jobscraper.pipeline import JobScraper
from jobscraper.providers import JobSpyProvider, LinkedInScraperProvider
from jobscraper.settings import ScraperSettings


def build_scraper(settings: ScraperSettings | None = None) -> JobScraper:
    settings = settings or ScraperSettings.from_env()
    providers = {
        "indeed": JobSpyProvider(),
        "linkedin": LinkedInScraperProvider(settings),
    }
    return JobScraper(settings=settings, providers=providers)


def main() -> None:
    asyncio.run(build_scraper().run())
