from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ExtractedTag:
    namespace: str
    slug: str
    display_name: str
    evidence: dict[str, Any]


BUILTIN_TAGS: tuple[tuple[str, str, str], ...] = (
    ("source", "indeed", "Indeed"),
    ("source", "linkedin", "LinkedIn"),
    ("source", "direct", "Direct"),
    ("work_mode", "remote", "Remote"),
    ("work_mode", "on_site", "On-site"),
    ("work_mode", "hybrid", "Hybrid"),
    ("experience", "experience_required", "Experience required"),
    ("experience_level", "junior", "Junior"),
    ("experience_level", "mid", "Mid level"),
    ("experience_level", "senior", "Senior"),
    ("experience_level", "staff", "Staff"),
    ("experience_level", "principal", "Principal"),
)

REMOTE_RE = re.compile(r"\bremote\b", re.I)
HYBRID_RE = re.compile(r"\bhybrid\b", re.I)
ON_SITE_RE = re.compile(r"\b(on[\s-]?site|in[\s-]?office)\b", re.I)
EXPERIENCE_REQUIRED_RE = re.compile(
    r"\b(\d{1,2})\+?\s*(?:years?|yrs?)\b.{0,40}\b(experience|professional)\b|"
    r"\b(experience|professional)\b.{0,40}\b(\d{1,2})\+?\s*(?:years?|yrs?)\b",
    re.I | re.S,
)
LEVEL_PATTERNS = (
    ("principal", "Principal", re.compile(r"\bprincipal\b", re.I)),
    ("staff", "Staff", re.compile(r"\bstaff\b", re.I)),
    ("senior", "Senior", re.compile(r"\b(senior|sr\.?)\b", re.I)),
    ("mid", "Mid level", re.compile(r"\b(mid[\s-]?level|intermediate)\b", re.I)),
    (
        "junior",
        "Junior",
        re.compile(r"\b(junior|jr\.?|entry[\s-]?level|new grad|early career)\b", re.I),
    ),
)


def extract_tags(provider: str, row: Mapping[str, Any]) -> list[ExtractedTag]:
    tags: dict[tuple[str, str], ExtractedTag] = {}

    def add(namespace: str, slug: str, display_name: str, evidence: dict[str, Any]):
        tags[(namespace, slug)] = ExtractedTag(namespace, slug, display_name, evidence)

    provider_slug = provider.lower().strip()
    provider_display = {
        "indeed": "Indeed",
        "linkedin": "LinkedIn",
        "direct": "Direct",
    }.get(provider_slug, provider_slug.title())
    add("source", provider_slug, provider_display, {"field": "provider", "value": provider})

    title = str(row.get("title") or "")
    location = str(row.get("location") or "")
    description = str(row.get("description") or "")
    combined = "\n".join(value for value in (title, location, description) if value)
    is_remote = str(row.get("is_remote") or "").strip().lower()

    if is_remote in {"true", "1", "yes"}:
        add("work_mode", "remote", "Remote", {"field": "is_remote", "value": row.get("is_remote")})
    elif HYBRID_RE.search(combined):
        add("work_mode", "hybrid", "Hybrid", {"pattern": "hybrid"})
    elif ON_SITE_RE.search(combined):
        add("work_mode", "on_site", "On-site", {"pattern": "on-site"})
    elif REMOTE_RE.search(combined):
        add("work_mode", "remote", "Remote", {"pattern": "remote"})

    if EXPERIENCE_REQUIRED_RE.search(combined):
        add(
            "experience",
            "experience_required",
            "Experience required",
            {"pattern": "years_experience"},
        )

    for slug, display_name, pattern in LEVEL_PATTERNS:
        if pattern.search(combined):
            add("experience_level", slug, display_name, {"pattern": slug})
            break

    return list(tags.values())

