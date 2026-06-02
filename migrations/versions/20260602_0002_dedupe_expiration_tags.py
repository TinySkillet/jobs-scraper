"""dedupe expiration tags

Revision ID: 20260602_0002
Revises: 20260602_0001
Create Date: 2026-06-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260602_0002"
down_revision = "20260602_0001"
branch_labels = None
depends_on = None


BUILTIN_TAGS = (
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


def upgrade() -> None:
    op.add_column(
        "normalized_jobs",
        sa.Column("source_key", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "normalized_jobs",
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "normalized_jobs",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "normalized_jobs",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "normalized_jobs",
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "normalized_jobs",
        sa.Column("inactive_reason", sa.Text(), nullable=True),
    )

    op.execute(
        """
        UPDATE normalized_jobs
        SET
            source_key = provider || ':url:' || lower(regexp_replace(job_url_direct, '/$', '')),
            posted_at = CASE
                WHEN date_posted IS NULL THEN NULL
                ELSE ((date_posted::timestamp + interval '1 day' - interval '1 microsecond') AT TIME ZONE 'UTC')
            END,
            expires_at = CASE
                WHEN date_posted IS NULL THEN NULL
                ELSE (((date_posted::timestamp + interval '1 day' - interval '1 microsecond') AT TIME ZONE 'UTC') + interval '72 hours')
            END
        WHERE source_key IS NULL
        """
    )
    op.alter_column("normalized_jobs", "source_key", nullable=False)
    op.drop_constraint(
        "uq_normalized_jobs_provider_job_url_direct",
        "normalized_jobs",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_normalized_jobs_provider_source_key",
        "normalized_jobs",
        ["provider", "source_key"],
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("namespace", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tags")),
        sa.UniqueConstraint("namespace", "slug", name="uq_tags_namespace_slug"),
    )
    op.create_table(
        "normalized_job_tags",
        sa.Column("normalized_job_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["normalized_job_id"],
            ["normalized_jobs.id"],
            name=op.f("fk_normalized_job_tags_normalized_job_id_normalized_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
            name=op.f("fk_normalized_job_tags_tag_id_tags"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "normalized_job_id",
            "tag_id",
            name=op.f("pk_normalized_job_tags"),
        ),
    )

    tags_table = sa.table(
        "tags",
        sa.column("namespace", sa.String),
        sa.column("slug", sa.String),
        sa.column("display_name", sa.String),
    )
    op.bulk_insert(
        tags_table,
        [
            {"namespace": namespace, "slug": slug, "display_name": display_name}
            for namespace, slug, display_name in BUILTIN_TAGS
        ],
    )


def downgrade() -> None:
    op.drop_table("normalized_job_tags")
    op.drop_table("tags")
    op.drop_constraint(
        "uq_normalized_jobs_provider_source_key",
        "normalized_jobs",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_normalized_jobs_provider_job_url_direct",
        "normalized_jobs",
        ["provider", "job_url_direct"],
    )
    op.drop_column("normalized_jobs", "inactive_reason")
    op.drop_column("normalized_jobs", "expired_at")
    op.drop_column("normalized_jobs", "is_active")
    op.drop_column("normalized_jobs", "expires_at")
    op.drop_column("normalized_jobs", "posted_at")
    op.drop_column("normalized_jobs", "source_key")

