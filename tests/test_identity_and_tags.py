from datetime import UTC, date, datetime, timedelta
from unittest import TestCase

from jobscraper.database import canonical_url_key, source_key_for_row
from jobscraper.filters import parse_posted_at
from jobscraper.tags import extract_tags


class SourceIdentityTests(TestCase):
    def test_canonical_url_key_removes_tracking_and_fragment(self):
        self.assertEqual(
            canonical_url_key(
                "indeed",
                "HTTPS://Example.com/jobs/123/?utm_source=x&jk=abc#details",
            ),
            "indeed:url:https://example.com/jobs/123?jk=abc",
        )

    def test_source_key_requires_stable_url_or_id(self):
        self.assertIsNone(source_key_for_row("indeed", {"title": "Java Engineer"}))
        self.assertEqual(
            source_key_for_row("linkedin", {"id": "ABC123"}),
            "linkedin:id:abc123",
        )


class PostedTimeTests(TestCase):
    def test_date_only_values_are_end_of_day_utc(self):
        self.assertEqual(
            parse_posted_at("2026-06-02"),
            datetime(2026, 6, 2, 23, 59, 59, 999999, tzinfo=UTC),
        )

    def test_relative_hours_use_current_time(self):
        now = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)
        self.assertEqual(
            parse_posted_at("3 hours ago", now=now),
            now - timedelta(hours=3),
        )


class TagExtractionTests(TestCase):
    def test_extracts_source_remote_and_explicit_senior_tags(self):
        tags = {
            (tag.namespace, tag.slug)
            for tag in extract_tags(
                "indeed",
                {
                    "title": "Senior Java Engineer",
                    "location": "Remote",
                    "is_remote": "True",
                    "description": "Requires 5 years of professional experience.",
                },
            )
        }

        self.assertIn(("source", "indeed"), tags)
        self.assertIn(("work_mode", "remote"), tags)
        self.assertIn(("experience", "experience_required"), tags)
        self.assertIn(("experience_level", "senior"), tags)

    def test_omits_uncertain_tags(self):
        tags = {
            (tag.namespace, tag.slug)
            for tag in extract_tags(
                "indeed",
                {
                    "title": "Java Engineer",
                    "location": "New York, NY",
                    "is_remote": "",
                    "description": "Build APIs.",
                },
            )
        }

        self.assertEqual(tags, {("source", "indeed")})

