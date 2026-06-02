import csv
import io
import tempfile
from datetime import date
from unittest import IsolatedAsyncioTestCase
from contextlib import redirect_stdout
from pathlib import Path

from jobscraper.database import json_safe
from jobscraper.models import JobSearchRequest, RoleSearchConfig, SearchSpec
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
                "date_posted": "2026-06-02",
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
                "date_posted": "2026-06-02",
                "job_url_direct": "",
                "description": "Java Spring Boot APIs",
            },
            {
                "title": "Java Engineer",
                "company": "Acme",
                "location": "Remote",
                "is_remote": "True",
                "job_type": "fulltime",
                "date_posted": "2026-06-02",
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
                "date_posted": "2026-06-02",
                "job_url_direct": "https://example.com/2",
                "description": "Java Spring Boot APIs",
            },
        ]


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

    async def test_filter_marks_expired_rows_inactive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = ScraperSettings(
                temp_dir=root / "temp",
                final_dir=root / "final",
                hours_old=72,
                max_job_age_hours=24,
                database_enabled=False,
            )
            scraper = JobScraper(settings=settings, providers={})
            source_rows, source_reasons = scraper.prepare_source_rows(
                [
                    {
                        "title": "Java Engineer",
                        "company": "Acme",
                        "location": "Remote",
                        "is_remote": "True",
                        "job_type": "fulltime",
                        "date_posted": "2 days ago",
                        "job_url_direct": "https://example.com/old",
                        "description": "Java Spring Boot APIs",
                    },
                    {
                        "title": "Java Engineer",
                        "job_url_direct": "",
                    },
                ],
                "indeed",
            )
            rows, reasons = scraper.filter_rows(source_rows, "java", "indeed")

            self.assertEqual(source_reasons["missing_direct_url"], 1)
            self.assertEqual(len(rows), 1)
            self.assertFalse(rows[0]["is_active"])
            self.assertEqual(rows[0]["inactive_reason"], "posted_age_exceeded")
            self.assertEqual(reasons["kept_before_dedupe"], 1)

    async def test_filter_excludes_rows_outside_hours_old_window(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = ScraperSettings(
                temp_dir=root / "temp",
                final_dir=root / "final",
                hours_old=24,
                max_job_age_hours=72,
                database_enabled=False,
            )
            scraper = JobScraper(settings=settings, providers={})
            source_rows, source_reasons = scraper.prepare_source_rows(
                [
                    {
                        "title": "Java Engineer",
                        "company": "Acme",
                        "location": "Remote",
                        "is_remote": "True",
                        "job_type": "fulltime",
                        "date_posted": "2 days ago",
                        "job_url_direct": "https://example.com/two-days-old",
                        "description": "Java Spring Boot APIs",
                    },
                ],
                "indeed",
            )
            rows, reasons = scraper.filter_rows(source_rows, "java", "indeed")

            self.assertEqual(source_reasons["missing_direct_url"], 0)
            self.assertEqual(rows, [])
            self.assertEqual(reasons["outside_hours_old_window"], 1)


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
