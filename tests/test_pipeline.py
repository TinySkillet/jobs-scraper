import csv
import io
import tempfile
from datetime import date
from contextlib import redirect_stdout
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from jobscraper.database import json_safe
from jobscraper.models import (
    JobSearchRequest,
    ProviderFetchError,
    RoleSearchConfig,
    SearchSpec,
)
from jobscraper.pipeline import JobScraper
from jobscraper.settings import ScraperSettings


class FakeProvider:
    name = "indeed"

    async def fetch(self, request: JobSearchRequest):
        return [
            {
                "title": "Java Engineer",
                "company": "Acme",
                "location": "Remote",
                "is_remote": "True",
                "job_type": "fulltime",
                "date_posted": "today",
                "job_url_direct": "https://example.com/1",
                "min_amount": "100000",
                "max_amount": "140000",
                "description": "Java Spring Boot APIs",
            },
            {
                "title": "Java Engineer",
                "company": "Acme",
                "location": "Remote",
                "is_remote": "True",
                "job_type": "fulltime",
                "date_posted": "today",
                "job_url_direct": "",
                "description": "Java Spring Boot APIs",
            },
            {
                "title": "Java Engineer",
                "company": "Acme",
                "location": "Remote",
                "is_remote": "True",
                "job_type": "fulltime",
                "date_posted": "today",
                "job_url_direct": "https://example.com/1",
                "min_amount": "",
                "max_amount": "",
                "description": "Java Spring Boot APIs",
            },
            {
                "title": "Lead Java Engineer",
                "company": "Acme",
                "location": "Remote",
                "is_remote": "True",
                "job_type": "fulltime",
                "date_posted": "today",
                "job_url_direct": "https://example.com/2",
                "description": "Java Spring Boot APIs",
            },
        ]


class FailingProvider:
    name = "indeed"

    async def fetch(self, request: JobSearchRequest):
        raise ProviderFetchError(
            provider=request.provider,
            search_name=request.search_name,
            attempts=3,
            cause=TimeoutError("read timed out"),
        )


class PipelineTests(IsolatedAsyncioTestCase):
    async def test_pipeline_writes_deduped_final_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = ScraperSettings(
                temp_dir=root / "temp",
                final_dir=root / "final",
                hours_old=24,
                enabled_providers=("indeed",),
                database_enabled=False,
            )
            catalog = {
                "java": RoleSearchConfig(
                    role="java",
                    final_output_name="jobs_final_java.csv",
                    searches=(SearchSpec("java_test", "java"),),
                )
            }

            scraper = JobScraper(
                settings=settings,
                providers={"indeed": FakeProvider()},
                role_catalog=catalog,
            )

            with redirect_stdout(io.StringIO()):
                await scraper.run()

            final_output = root / "final" / "jobs_final_java.csv"
            with final_output.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["Title"], "Java Engineer")
            self.assertEqual(rows[0]["Direct URL"], "https://example.com/1")

    async def test_pipeline_skips_failed_provider_search_and_writes_empty_final_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = ScraperSettings(
                temp_dir=root / "temp",
                final_dir=root / "final",
                enabled_providers=("indeed",),
                database_enabled=False,
            )
            catalog = {
                "java": RoleSearchConfig(
                    role="java",
                    final_output_name="jobs_final_java.csv",
                    searches=(SearchSpec("java_test", "java"),),
                )
            }
            raw_output = root / "temp" / "jobs_java_java_test.csv"
            raw_output.parent.mkdir()
            raw_output.write_text("stale,data\n", encoding="utf-8")
            scraper = JobScraper(
                settings=settings,
                providers={"indeed": FailingProvider()},
                role_catalog=catalog,
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                await scraper.run()

            final_output = root / "final" / "jobs_final_java.csv"
            with final_output.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            self.assertIn("fetch_error=1", stdout.getvalue())
            self.assertFalse(raw_output.exists())
            self.assertEqual(rows, [])


class DatabaseSerializationTests(IsolatedAsyncioTestCase):
    async def test_json_safe_converts_date_values_recursively(self):
        payload = json_safe(
            {
                "date_posted": date(2026, 6, 2),
                "nested": {"dates": [date(2026, 6, 1)]},
            }
        )

        self.assertEqual(payload["date_posted"], "2026-06-02")
        self.assertEqual(payload["nested"]["dates"], ["2026-06-01"])
