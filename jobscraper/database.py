from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    delete,
    select,
    tuple_,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from jobscraper.models import JobSearchRequest, SearchRunRecord
from jobscraper.tags import BUILTIN_TAGS, ExtractedTag


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class JobSearchRun(Base):
    __tablename__ = "job_search_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    search_name: Mapped[str] = mapped_column(String(200), nullable=False)
    search_term: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class RawJob(Base):
    __tablename__ = "raw_jobs"
    __table_args__ = (
        UniqueConstraint("provider", "source_key", name="uq_raw_jobs_provider_source_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    search_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    job_url_direct: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    first_seen_run_id: Mapped[int] = mapped_column(
        ForeignKey("job_search_runs.id"),
        nullable=False,
    )
    last_seen_run_id: Mapped[int] = mapped_column(
        ForeignKey("job_search_runs.id"),
        nullable=False,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class NormalizedJob(Base):
    __tablename__ = "normalized_jobs"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "source_key",
            name="uq_normalized_jobs_provider_source_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    is_remote: Mapped[str] = mapped_column(Text, nullable=False, default="")
    job_type: Mapped[str] = mapped_column(Text, nullable=False, default="")
    date_posted: Mapped[date | None] = mapped_column(Date)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    job_url_direct: Mapped[str] = mapped_column(Text, nullable=False)
    min_amount: Mapped[str] = mapped_column(Text, nullable=False, default="")
    max_amount: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inactive_reason: Mapped[str | None] = mapped_column(Text)
    last_seen_run_id: Mapped[int] = mapped_column(
        ForeignKey("job_search_runs.id"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("namespace", "slug", name="uq_tags_namespace_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    namespace: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)


normalized_job_tags = Table(
    "normalized_job_tags",
    Base.metadata,
    Column(
        "normalized_job_id",
        ForeignKey("normalized_jobs.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("evidence", JSONB, nullable=False),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    ),
)


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> sessionmaker[AsyncSession]:
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start_search_run(self, request: JobSearchRequest) -> SearchRunRecord:
        run = JobSearchRun(
            provider=request.provider,
            role=request.role,
            search_name=request.search_name,
            search_term=request.search_term,
        )
        self.session.add(run)
        await self.session.flush()
        return SearchRunRecord(
            id=run.id,
            provider=run.provider,
            role=run.role,
            search_name=run.search_name,
            search_term=run.search_term,
        )

    async def finish_search_run(self, run_id: int, raw_count: int) -> None:
        run = await self.session.get(JobSearchRun, run_id)
        if run is None:
            raise ValueError(f"Unknown search run id: {run_id}")

        run.raw_count = raw_count
        run.finished_at = datetime.now(UTC)

    async def upsert_raw_jobs(
        self,
        *,
        run: SearchRunRecord,
        rows: list[dict[str, Any]],
    ) -> None:
        if not rows:
            return

        now = datetime.now(UTC)
        values_by_key = {}
        for row in rows:
            source_key = source_key_for_row(run.provider, row)
            if source_key is None:
                continue
            values_by_key[(run.provider, source_key)] = {
                "provider": run.provider,
                "role": run.role,
                "search_name": run.search_name,
                "source_key": source_key,
                "job_url_direct": _optional_str(row.get("job_url_direct")),
                "payload": json_safe(row),
                "first_seen_run_id": run.id,
                "last_seen_run_id": run.id,
                "first_seen_at": now,
                "last_seen_at": now,
            }

        values = list(values_by_key.values())
        if not values:
            return

        statement = insert(RawJob).values(values)
        statement = statement.on_conflict_do_update(
            constraint="uq_raw_jobs_provider_source_key",
            set_={
                "role": statement.excluded.role,
                "search_name": statement.excluded.search_name,
                "job_url_direct": statement.excluded.job_url_direct,
                "payload": statement.excluded.payload,
                "last_seen_run_id": statement.excluded.last_seen_run_id,
                "last_seen_at": now,
            },
        )
        await self.session.execute(statement)

    async def upsert_normalized_jobs(
        self,
        *,
        run: SearchRunRecord,
        rows: list[dict[str, Any]],
    ) -> None:
        if not rows:
            return

        now = datetime.now(UTC)
        values_by_url = {}
        for row in rows:
            source_key = row["source_key"]
            values_by_url[(run.provider, source_key)] = {
                "provider": run.provider,
                "role": run.role,
                "source_key": source_key,
                "title": row.get("title", ""),
                "company": row.get("company", ""),
                "location": row.get("location", ""),
                "is_remote": row.get("is_remote", ""),
                "job_type": row.get("job_type", ""),
                "date_posted": row.get("date_posted"),
                "posted_at": row.get("posted_at"),
                "expires_at": row.get("expires_at"),
                "job_url_direct": row["job_url_direct"],
                "min_amount": row.get("min_amount", ""),
                "max_amount": row.get("max_amount", ""),
                "is_active": row.get("is_active", True),
                "expired_at": row.get("expired_at"),
                "inactive_reason": row.get("inactive_reason"),
                "last_seen_run_id": run.id,
                "updated_at": now,
            }

        values = list(values_by_url.values())
        if not values:
            return

        statement = insert(NormalizedJob).values(values)
        statement = statement.on_conflict_do_update(
            constraint="uq_normalized_jobs_provider_source_key",
            set_={
                "role": statement.excluded.role,
                "title": statement.excluded.title,
                "company": statement.excluded.company,
                "location": statement.excluded.location,
                "is_remote": statement.excluded.is_remote,
                "job_type": statement.excluded.job_type,
                "date_posted": statement.excluded.date_posted,
                "posted_at": statement.excluded.posted_at,
                "expires_at": statement.excluded.expires_at,
                "min_amount": statement.excluded.min_amount,
                "max_amount": statement.excluded.max_amount,
                "is_active": statement.excluded.is_active,
                "expired_at": statement.excluded.expired_at,
                "inactive_reason": statement.excluded.inactive_reason,
                "last_seen_run_id": statement.excluded.last_seen_run_id,
                "updated_at": now,
            },
        ).returning(NormalizedJob.id, NormalizedJob.source_key)
        result = await self.session.execute(statement)
        job_ids_by_source_key = {
            row.source_key: row.id
            for row in result
        }
        await self.replace_tags(job_ids_by_source_key, rows)

    async def replace_tags(
        self,
        job_ids_by_source_key: dict[str, int],
        rows: list[dict[str, Any]],
    ) -> None:
        job_ids = list(job_ids_by_source_key.values())
        if not job_ids:
            return

        await self.session.execute(
            delete(normalized_job_tags).where(
                normalized_job_tags.c.normalized_job_id.in_(job_ids)
            )
        )

        tag_values = [
            {"namespace": namespace, "slug": slug, "display_name": display_name}
            for namespace, slug, display_name in BUILTIN_TAGS
        ]
        tag_statement = insert(Tag).values(tag_values)
        tag_statement = tag_statement.on_conflict_do_nothing(
            constraint="uq_tags_namespace_slug"
        )
        await self.session.execute(tag_statement)

        row_tags_by_key: dict[tuple[int, str, str], tuple[int, ExtractedTag]] = {}
        required_keys = set()
        for row in rows:
            job_id = job_ids_by_source_key.get(row["source_key"])
            if job_id is None:
                continue
            for tag in row.get("tags", []):
                required_keys.add((tag.namespace, tag.slug))
                row_tags_by_key[(job_id, tag.namespace, tag.slug)] = (job_id, tag)

        row_tags = list(row_tags_by_key.values())
        if not row_tags:
            return

        tag_rows = await self.session.execute(
            select(Tag).where(
                tuple_(Tag.namespace, Tag.slug).in_(required_keys)
            )
        )
        tag_ids = {
            (tag.namespace, tag.slug): tag.id
            for tag in tag_rows.scalars()
        }
        now = datetime.now(UTC)
        await self.session.execute(
            insert(normalized_job_tags).values(
                [
                    {
                        "normalized_job_id": job_id,
                        "tag_id": tag_ids[(tag.namespace, tag.slug)],
                        "evidence": json_safe(tag.evidence),
                        "created_at": now,
                    }
                    for job_id, tag in row_tags
                    if (tag.namespace, tag.slug) in tag_ids
                ]
            )
        )

    async def expire_old_jobs(self, *, now: datetime | None = None) -> None:
        now = now or datetime.now(UTC)
        await self.session.execute(
            update(NormalizedJob)
            .where(NormalizedJob.is_active.is_(True))
            .where(NormalizedJob.expires_at <= now)
            .values(
                is_active=False,
                expired_at=now,
                inactive_reason="posted_age_exceeded",
                updated_at=now,
            )
        )


def source_key_for_row(provider: str, row: Mapping[str, Any]) -> str | None:
    for key in ("job_url_direct", "job_url", "linkedin_url"):
        value = _optional_str(row.get(key))
        if value:
            return canonical_url_key(provider, value)

    for key in ("id", "job_id", "source_id"):
        value = _optional_str(row.get(key))
        if value:
            return f"{provider}:id:{value.casefold()}"

    return None


def canonical_url_key(provider: str, value: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    parsed = urlsplit(value.strip())
    if not parsed.scheme or not parsed.netloc:
        return f"{provider}:url:{value.strip().casefold()}"

    query = urlencode(
        sorted(
            (key, val)
            for key, val in parse_qsl(parsed.query, keep_blank_values=False)
            if not key.lower().startswith(("utm_", "fbclid", "gclid"))
        )
    )
    normalized = urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            query,
            "",
        )
    )
    return f"{provider}:url:{normalized}"


def _optional_str(value: object) -> str | None:
    value = str(value or "").strip()
    return value or None


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value

    if isinstance(value, datetime | date):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}

    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [json_safe(item) for item in value]

    return str(value)
