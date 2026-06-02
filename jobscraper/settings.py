from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw_value!r}") from exc


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw_value!r}") from exc


def _env_csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if not raw_value:
        return default

    values = tuple(value.strip() for value in raw_value.split(",") if value.strip())
    return values or default


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.lower() not in {"0", "false", "no"}


@dataclass(frozen=True)
class ScraperSettings:
    location: str = "USA"
    country_indeed: str = "USA"
    hours_old: int = 24
    max_job_age_hours: int = 72
    results_wanted: int = 1000
    enabled_providers: tuple[str, ...] = ("indeed",)
    final_dir: Path = Path("final")
    temp_dir: Path = Path("temp")
    database_url: str = "postgresql+asyncpg://jobscraper:jobscraper@localhost:5432/jobscraper"
    database_enabled: bool = True
    provider_fetch_retries: int = 2
    provider_retry_backoff_seconds: float = 2.0
    linkedin_session_path: Path | None = None
    linkedin_headless: bool = True

    @classmethod
    def from_env(cls) -> "ScraperSettings":
        session_path = os.getenv("LINKEDIN_SESSION_PATH")
        return cls(
            location=os.getenv("LOCATION", "USA"),
            country_indeed=os.getenv("COUNTRY_INDEED", "USA"),
            hours_old=_env_int("HOURS_OLD", 24),
            max_job_age_hours=_env_int("MAX_JOB_AGE_HOURS", 72),
            results_wanted=_env_int("RESULTS_WANTED", 1000),
            enabled_providers=_env_csv("JOB_PROVIDERS", ("indeed",)),
            final_dir=Path(os.getenv("FINAL_DIR", "final")),
            temp_dir=Path(os.getenv("TEMP_DIR", "temp")),
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://jobscraper:jobscraper@localhost:5432/jobscraper",
            ),
            database_enabled=_env_bool("DATABASE_ENABLED", True),
            provider_fetch_retries=_env_int("PROVIDER_FETCH_RETRIES", 2),
            provider_retry_backoff_seconds=_env_float(
                "PROVIDER_RETRY_BACKOFF_SECONDS",
                2.0,
            ),
            linkedin_session_path=Path(session_path) if session_path else None,
            linkedin_headless=os.getenv("LINKEDIN_HEADLESS", "1").lower()
            not in {"0", "false", "no"},
        )
