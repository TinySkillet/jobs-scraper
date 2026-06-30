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
            exclusion_reason({"title": "Staff Software Engineer", "description": ""}),
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

    def test_exclusion_reason_detects_restricted_eligibility(self):
        restricted_descriptions = [
            "Need US CITIZENS for this role.",
            "U.S. Citizenship required.",
            "Applicants must be a U.S. person due to export-controlled work.",
            "This role is ITAR restricted and requires U.S. person status.",
            "Active Secret clearance required.",
            "Top-Secret security clearance is required.",
            "TS/SCI with polygraph required.",
            "Ability to obtain and maintain a Federal Security Clearance.",
            "Security Clearance Level: Public Trust.",
            "US citizenship with ability to obtain Public Trust Suitability.",
        ]

        for description in restricted_descriptions:
            with self.subTest(description=description):
                self.assertEqual(
                    exclusion_reason(
                        {"title": "Software Engineer", "description": description}
                    ),
                    "requires_clearance",
                )

    def test_exclusion_reason_detects_veteran_only_requirements(self):
        self.assertEqual(
            exclusion_reason(
                {
                    "title": "Software Engineer",
                    "description": "Applicants must be veterans for this program.",
                }
            ),
            "requires_veteran_status",
        )
        self.assertEqual(
            exclusion_reason(
                {
                    "title": "Software Engineer",
                    "description": "This fellowship is limited to veterans only.",
                }
            ),
            "requires_veteran_status",
        )

    def test_exclusion_reason_allows_standard_work_auth_and_eeo_language(self):
        allowed_descriptions = [
            "Applicants must be authorized to work in the United States.",
            "We use E-Verify to verify employment eligibility.",
            "Offer is contingent on a background check.",
            "All qualified applicants are considered without regard to protected veteran status.",
            "Veterans are encouraged to apply.",
            "Must possess a valid fingerprint clearance card within 90 days.",
        ]

        for description in allowed_descriptions:
            with self.subTest(description=description):
                self.assertIsNone(
                    exclusion_reason(
                        {"title": "Software Engineer", "description": description}
                    )
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

    def test_security_roles_have_relevance_filters(self):
        self.assertTrue(
            is_relevant(
                {
                    "title": "Application Security Engineer",
                    "description": "Review secure code and OWASP vulnerabilities.",
                },
                "application_security",
            )
        )
        self.assertTrue(
            is_relevant(
                {
                    "title": "Penetration Tester",
                    "description": "Perform web application testing with Burp Suite.",
                },
                "penetration_tester",
            )
        )
        self.assertTrue(
            is_relevant(
                {
                    "title": "Cybersecurity Analyst",
                    "description": "Monitor SIEM alerts and incident response.",
                },
                "cybersecurity",
            )
        )
