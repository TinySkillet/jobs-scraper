from datetime import UTC, datetime
from pathlib import Path
from unittest import TestCase

from jobscraper.lifecycle import JobRowLifecycle
from jobscraper.settings import ScraperSettings


def settings_for_lifecycle(*, hours_old: int = 24, max_job_age_hours: int = 72):
    return ScraperSettings(
        temp_dir=Path("temp"),
        final_dir=Path("final"),
        hours_old=hours_old,
        max_job_age_hours=max_job_age_hours,
        database_enabled=False,
    )


class JobRowLifecycleTests(TestCase):
    def test_process_builds_source_and_normalized_rows_with_tags(self):
        lifecycle = JobRowLifecycle(settings_for_lifecycle())
        result = lifecycle.process(
            [
                {
                    "title": "Senior Java Engineer",
                    "company": "Acme",
                    "location": "Remote",
                    "is_remote": "True",
                    "job_type": "fulltime",
                    "date_posted": "3 hours ago",
                    "job_url_direct": "https://example.com/jobs/1?utm_source=test",
                    "description": "Java Spring Boot APIs. Requires 5 years experience.",
                }
            ],
            role="java",
            provider="indeed",
            now=datetime(2026, 6, 2, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(result.reasons["kept_before_dedupe"], 1)
        self.assertEqual(len(result.source_rows), 1)
        self.assertEqual(len(result.normalized_rows), 1)
        row = result.normalized_rows[0]
        self.assertTrue(row["is_active"])
        self.assertEqual(row["provider"], "indeed")
        self.assertEqual(
            row["source_key"],
            "indeed:url:https://example.com/jobs/1",
        )
        self.assertEqual(
            {(tag.namespace, tag.slug) for tag in row["tags"]},
            {
                ("source", "indeed"),
                ("work_mode", "remote"),
                ("experience", "experience_required"),
                ("experience_level", "senior"),
            },
        )

    def test_process_marks_expired_rows_inactive(self):
        lifecycle = JobRowLifecycle(
            settings_for_lifecycle(hours_old=72, max_job_age_hours=24)
        )
        result = lifecycle.process(
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
            role="java",
            provider="indeed",
            now=datetime(2026, 6, 2, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(result.reasons["missing_direct_url"], 1)
        self.assertEqual(len(result.normalized_rows), 1)
        self.assertFalse(result.normalized_rows[0]["is_active"])
        self.assertEqual(
            result.normalized_rows[0]["inactive_reason"],
            "posted_age_exceeded",
        )
        self.assertEqual(result.reasons["kept_before_dedupe"], 1)

    def test_process_excludes_rows_outside_hours_old_window(self):
        lifecycle = JobRowLifecycle(
            settings_for_lifecycle(hours_old=24, max_job_age_hours=72)
        )
        result = lifecycle.process(
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
            role="java",
            provider="indeed",
            now=datetime(2026, 6, 2, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(result.source_rows[0]["job_url_direct"], "https://example.com/two-days-old")
        self.assertEqual(result.normalized_rows, [])
        self.assertEqual(result.reasons["outside_hours_old_window"], 1)
