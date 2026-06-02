from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta
from typing import Mapping

ALLOWED_JOB_TYPES = {"fulltime", "contract", ""}
EXCLUDED_TITLE_RE = re.compile(
    r"\b(lead|leader|manager|director|head|vp|vice president|chief)\b",
    re.I,
)
CLEARANCE_REQUIREMENT_RE = re.compile(
    r"\bactive\b.{0,80}\b(?:security\s+)?clearance\b|"
    r"\b(?:security\s+)?clearance\b.{0,80}\bactive\b|"
    r"\bclearance\s+required\b|"
    r"\brequires?\b.{0,80}\b(?:security\s+)?clearance\b|"
    r"\b(?:security\s+)?clearance\b.{0,80}\brequired\b|"
    r"\btop\s+secret\b|"
    r"\bts/sci\b|"
    r"\bsecret\s+clearance\b|"
    r"\bactive\b.{0,80}\b(?:secret|top secret|ts/sci|sci)\b",
    re.I | re.S,
)
JAVA_TITLE_RELEVANCE_RE = re.compile(r"\bjava\b|\bspring\b", re.I)
JAVA_BODY_RELEVANCE_RE = re.compile(
    r"\bjava\b|\bspring\b|\bspring\s+boot\b|\bj2ee\b|\bjvm\b", re.I
)
FULLSTACK_TITLE_RELEVANCE_RE = re.compile(r"\bfull[\s-]?stack\b|\bfullstack\b", re.I)
FULLSTACK_BODY_RELEVANCE_RE = re.compile(
    r"\bfull[\s-]?stack\b|\bfullstack\b|\bfrontend\b|\bfront-end\b|\bbackend\b|\bback-end\b",
    re.I,
)
DATA_ENGINEER_TITLE_RELEVANCE_RE = re.compile(
    r"\bdata engineer(?:ing)?\b|\bbig data engineer\b|\betl (?:developer|engineer)\b|\banalytics engineer\b|\bBI engineer\b|\bdata (?:pipeline|platform|warehouse|infrastructure) engineer\b|\bplatform data engineer\b|\bstreaming data engineer\b",
    re.I,
)
DATA_ENGINEER_BODY_RELEVANCE_RE = re.compile(
    r"\bdata pipeline\b|\betl\b|\bspark\b|\bairflow\b|\bdatabricks\b|\bsnowflake\b|\bdbt\b|\bbigquery\b|\bredshift\b|\bdata warehouse\b|\bdata lake\b|\blakehouse\b|\bdelta\b|\biceberg\b|\bhudi\b|\bkafka\b|\bflink\b|\bkinesis\b|\bdata factory\b|\bsynapse\b|\bfabric\b",
    re.I,
)
FRONTEND_RE = re.compile(
    r"\breact\b|\bangular\b|\bvue\b|\bnext\.?js\b|\bnuxt\.?js\b|\bjavascript\b|\btypescript\b",
    re.I,
)
BACKEND_RE = re.compile(
    r"\bnode\b|\bexpress\b|\bapi\b|\bbackend\b|\bback-end\b|\bjava\b|\bspring\b|\.net\b|\bc#\b|\bpython\b|\bdjango\b|\bflask\b|\bfastapi\b|\bgraphql\b",
    re.I,
)
DATA_ENGINEER_SKILL_RE = re.compile(
    r"\bsql\b|\bpython\b|\bspark\b|\bpyspark\b|\bairflow\b|\bdbt\b|\bdatabricks\b|\bsnowflake\b|\bbigquery\b|\bredshift\b|\baws\b|\bazure\b|\bgcp\b|\bglue\b|\bdata factory\b|\bsynapse\b|\bfabric\b|\bkafka\b|\bflink\b|\bkinesis\b",
    re.I,
)
GENERIC_ENGINEER_TITLE_RE = re.compile(
    r"\b(software engineer|developer|engineer)\b", re.I
)
RELATIVE_DATE_RE = re.compile(
    r"\b(\d+)\s+(hour|day|week|month)s?\s+ago\b",
    re.I,
)


def parse_date_posted(value: object, *, today: date | None = None) -> date | None:
    posted_at = parse_posted_at(value, now=None if today is None else _end_of_day(today))
    if posted_at is not None:
        return posted_at.date()

    return None


def parse_posted_at(value: object, *, now: datetime | None = None) -> datetime | None:
    now = now or datetime.now(UTC)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    if isinstance(value, date):
        return _end_of_day(value)

    value = str(value or "").strip()
    if not value:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return _end_of_day(date.fromisoformat(value))

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        parsed = None

    if parsed is not None:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    try:
        return _end_of_day(date.fromisoformat(value))
    except ValueError:
        pass

    normalized = value.lower()
    if normalized in {"today", "just now"} or "hour" in normalized:
        hour_match = RELATIVE_DATE_RE.search(normalized)
        if hour_match and hour_match.group(2).lower() == "hour":
            return now - timedelta(hours=int(hour_match.group(1)))
        return now

    match = RELATIVE_DATE_RE.search(normalized)
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2).lower()
    if unit == "day":
        days = amount
    elif unit == "week":
        days = amount * 7
    elif unit == "month":
        days = amount * 30
    else:
        days = 0

    return now - timedelta(days=days)


def posted_within_hours(
    row: Mapping[str, object],
    *,
    hours_old: int,
    today: date | None = None,
) -> bool:
    now = _end_of_day(today) if today is not None else datetime.now(UTC)
    posted_at = parse_posted_at(row.get("date_posted"), now=now)
    if not posted_at:
        return False

    cutoff = now - timedelta(hours=hours_old)
    return posted_at >= cutoff


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value, time.max, tzinfo=UTC)


def is_relevant(row: Mapping[str, object], role: str) -> bool:
    title = str(row.get("title") or "")
    description = str(row.get("description") or "")

    if role == "java":
        if JAVA_TITLE_RELEVANCE_RE.search(title):
            return True

        return bool(
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and JAVA_BODY_RELEVANCE_RE.search(description)
        )

    if role == "fullstack":
        if FULLSTACK_TITLE_RELEVANCE_RE.search(title):
            return True

        return bool(
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and FULLSTACK_BODY_RELEVANCE_RE.search(description)
            and FRONTEND_RE.search(description)
            and BACKEND_RE.search(description)
        )

    if role == "data_engineer":
        if DATA_ENGINEER_TITLE_RELEVANCE_RE.search(title):
            return True

        return bool(
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and DATA_ENGINEER_BODY_RELEVANCE_RE.search(description)
            and DATA_ENGINEER_SKILL_RE.search(description)
        )

    raise ValueError(f"Unknown role: {role}")


def exclusion_reason(row: Mapping[str, object]) -> str | None:
    title = str(row.get("title") or "")
    description = str(row.get("description") or "")

    if EXCLUDED_TITLE_RE.search(title):
        return "excluded_title_leadership"

    if CLEARANCE_REQUIREMENT_RE.search(f"{title}\n{description}"):
        return "requires_clearance"

    return None
