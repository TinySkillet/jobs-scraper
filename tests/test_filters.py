from datetime import date
from unittest import TestCase

from jobscraper.filters import (
    exclusion_reason,
    is_relevant,
    parse_date_posted,
    posted_within_hours,
)


class FilterTests(TestCase):
    def test_parse_date_posted_accepts_iso_date(self):
        self.assertEqual(parse_date_posted("2026-06-02"), date(2026, 6, 2))

    def test_parse_date_posted_accepts_relative_linkedin_dates(self):
        self.assertEqual(
            parse_date_posted("2 days ago", today=date(2026, 6, 2)),
            date(2026, 5, 31),
        )
        self.assertEqual(
            parse_date_posted("3 weeks ago", today=date(2026, 6, 2)),
            date(2026, 5, 12),
        )

    def test_posted_within_hours_keeps_today_and_yesterday_for_24h_indeed_rows(self):
        self.assertTrue(
            posted_within_hours(
                {"date_posted": "2026-06-01"},
                hours_old=24,
                today=date(2026, 6, 2),
            )
        )
        self.assertFalse(
            posted_within_hours(
                {"date_posted": "2026-05-30"},
                hours_old=24,
                today=date(2026, 6, 2),
            )
        )

    def test_exclusion_reason_detects_leadership_and_clearance(self):
        self.assertEqual(
            exclusion_reason({"title": "Lead Java Engineer", "description": ""}),
            "excluded_title_leadership",
        )
        self.assertEqual(
            exclusion_reason(
                {
                    "title": "Java Engineer",
                    "description": "This role requires active security clearance.",
                }
            ),
            "requires_clearance",
        )

    def test_role_relevance_allows_generic_java_engineer_with_java_body(self):
        self.assertTrue(
            is_relevant(
                {
                    "title": "Software Engineer",
                    "description": "Build services with Java and Spring Boot.",
                },
                "java",
            )
        )
