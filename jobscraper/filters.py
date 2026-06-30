from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta
from typing import Mapping

ALLOWED_JOB_TYPES = {"fulltime", "contract", ""}
EXCLUDED_TITLE_RE = re.compile(
    r"\b(staff|lead|leader|manager|director|head|vp|vice president|chief)\b",
    re.I,
)
CLEARANCE_REQUIREMENT_RE = re.compile(
    r"\bactive\b.{0,80}\b(?:security\s+)?clearance\b|"
    r"\b(?:security\s+)?clearance\b.{0,80}\bactive\b|"
    r"\b(?:current|existing)\b.{0,80}\b(?:security\s+)?clearance\b|"
    r"\b(?:security\s+)?clearance\b.{0,80}\b(?:current|existing)\b|"
    r"\bclearance\s+required\b|"
    r"\brequires?\b.{0,80}\b(?:security\s+)?clearance\b|"
    r"\bmust\b.{0,80}\b(?:have|possess|hold)\b.{0,80}\b(?:security|secret|top[-\s]+secret|ts\s*/\s*sci|sci|poly|dod|federal)\s+clearance\b|"
    r"\b(?:security\s+)?clearance\b.{0,80}\brequired\b|"
    r"\b(?:ability|able|eligible|required|must|willing)\b.{0,100}\b(?:obtain|get|maintain|hold)\b.{0,100}\b(?:security\s+)?clearance\b|"
    r"\b(?:obtain|get|maintain|hold)\b.{0,100}\b(?:security\s+)?clearance\b|"
    r"\btop[-\s]+secret\b|"
    r"\bts\s*/\s*sci\b|"
    r"\bsecret\s+clearance\b|"
    r"\bactive\b.{0,80}\b(?:secret|top[-\s]+secret|ts\s*/\s*sci|sci)\b|"
    r"\b(?:dod|federal)\s+(?:security\s+)?clearance\b|"
    r"\bpublic\s+trust\b.{0,80}\b(?:required|requirement|level|clearance|suitability|investigation|eligible|obtain|maintain)\b|"
    r"\b(?:required|requirement|level|clearance|suitability|investigation|eligible|obtain|maintain)\b.{0,80}\bpublic\s+trust\b",
    re.I | re.S,
)
CITIZENSHIP_REQUIREMENT_RE = re.compile(
    r"\b(?:must\s+be|need(?:s|ed)?|requires?|requirement[s]?:?|only|limited\s+to|applicants?\s+must\s+be|candidates?\s+must\s+be)\b.{0,100}\b(?:u\.?\s*s\.?|us|united states)\s+citizens?(?:hip)?\b|"
    r"\b(?:u\.?\s*s\.?|us|united states)\s+citizens?(?:hip)?\b.{0,100}\b(?:required|requirement|only|must|need(?:s|ed)?|prerequisite)\b|"
    r"\b(?:u\.?\s*s\.?|us|united states)\s+citizenship\s+required\??\b|"
    r"\b(?:u\.?\s*s\.?|us|united states)\s+citizen\s+eligible\b",
    re.I | re.S,
)
US_PERSON_REQUIREMENT_RE = re.compile(
    r"\b(?:must\s+be|requires?|requirement[s]?:?|only|limited\s+to)\b.{0,100}\bu\.?\s*s\.?\s+persons?\b|"
    r"\bu\.?\s*s\.?\s+persons?\b.{0,100}\b(?:required|requirement|only|must|eligible|qualify|export[-\s]?control(?:led)?)\b|"
    r"\b(?:itar|ear|export[-\s]?control(?:led)?)\b.{0,120}\b(?:u\.?\s*s\.?\s+persons?|citizenship|citizens?|permanent\s+resident|green\s+card|visa\s+does\s+not\s+qualify)\b|"
    r"\bworking\s+on\s+a\s+u\.?\s*s\.?\s+visa\s+does\s+not\s+qualify\b",
    re.I | re.S,
)
VETERAN_REQUIREMENT_RE = re.compile(
    r"\bveterans?\s+only\b|"
    r"\bonly\s+veterans?\b|"
    r"\blimited\s+to\s+veterans?\b|"
    r"\b(?:must\s+be|requires?)\s+(?:a\s+)?veterans?\b|"
    r"\bveteran\s+status\s+(?:is\s+)?required\b|"
    r"\bveterans?\s+preference\s+eligible\s+(?:is\s+)?required\b",
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
APPLICATION_SECURITY_TITLE_RELEVANCE_RE = re.compile(
    r"\bapplication security\b|\bappsec\b|\bproduct security\b|\bsecure code\b|\bsecurity engineer\b",
    re.I,
)
APPLICATION_SECURITY_BODY_RELEVANCE_RE = re.compile(
    r"\bapplication security\b|\bappsec\b|\bsecure code\b|\bsecure coding\b|\bsast\b|\bdast\b|\bsoftware composition analysis\b|\bsca\b|\bthreat model(?:ing)?\b|\bcode review\b|\bvulnerability management\b|\bowasp\b|\bapi security\b|\bweb application security\b",
    re.I,
)
PENETRATION_TESTER_TITLE_RELEVANCE_RE = re.compile(
    r"\bpenetration tester\b|\bpenetration testing\b|\bpen tester\b|\bpentest(?:er|ing)?\b|\bred team\b|\boffensive security\b|\bethical hacker\b",
    re.I,
)
PENETRATION_TESTER_BODY_RELEVANCE_RE = re.compile(
    r"\bpenetration test(?:er|ing)?\b|\bpen test(?:er|ing)?\b|\bpentest(?:er|ing)?\b|\bred team\b|\boffensive security\b|\bethical hacking\b|\bburp suite\b|\bmetasploit\b|\bnmap\b|\bweb app testing\b|\bnetwork testing\b|\bvulnerability assessment\b",
    re.I,
)
CYBERSECURITY_TITLE_RELEVANCE_RE = re.compile(
    r"\bcyber ?security\b|\binformation security\b|\binfosec\b|\bsecurity analyst\b|\bsecurity engineer\b|\bsecurity specialist\b|\bsoc analyst\b|\bcloud security\b",
    re.I,
)
CYBERSECURITY_BODY_RELEVANCE_RE = re.compile(
    r"\bcyber ?security\b|\binformation security\b|\binfosec\b|\bsiem\b|\bsoc\b|\bincident response\b|\bthreat detection\b|\bthreat hunting\b|\bvulnerability management\b|\bcloud security\b|\biam\b|\bsecurity operations\b|\bedr\b|\bxdr\b|\bsplunk\b|\bsentinel\b",
    re.I,
)
GENERIC_ENGINEER_TITLE_RE = re.compile(
    r"\b(software engineer|developer|engineer|analyst|specialist|consultant)\b", re.I
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

    if role == "application_security":
        if APPLICATION_SECURITY_TITLE_RELEVANCE_RE.search(title):
            return True

        return bool(
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and APPLICATION_SECURITY_BODY_RELEVANCE_RE.search(description)
        )

    if role == "penetration_tester":
        if PENETRATION_TESTER_TITLE_RELEVANCE_RE.search(title):
            return True

        return bool(
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and PENETRATION_TESTER_BODY_RELEVANCE_RE.search(description)
        )

    if role == "cybersecurity":
        if CYBERSECURITY_TITLE_RELEVANCE_RE.search(title):
            return True

        return bool(
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and CYBERSECURITY_BODY_RELEVANCE_RE.search(description)
        )

    raise ValueError(f"Unknown role: {role}")


def exclusion_reason(row: Mapping[str, object]) -> str | None:
    title = str(row.get("title") or "")
    description = str(row.get("description") or "")
    searchable_text = f"{title}\n{description}"

    if EXCLUDED_TITLE_RE.search(title):
        return "excluded_title_leadership"

    if (
        CLEARANCE_REQUIREMENT_RE.search(searchable_text)
        or CITIZENSHIP_REQUIREMENT_RE.search(searchable_text)
        or US_PERSON_REQUIREMENT_RE.search(searchable_text)
    ):
        return "requires_clearance"

    if VETERAN_REQUIREMENT_RE.search(searchable_text):
        return "requires_veteran_status"

    return None
