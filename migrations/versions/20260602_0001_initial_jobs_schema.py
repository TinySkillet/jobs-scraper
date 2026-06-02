"""initial jobs schema

Revision ID: 20260602_0001
Revises: 
Create Date: 2026-06-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260602_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_search_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("search_name", sa.String(length=200), nullable=False),
        sa.Column("search_term", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_search_runs")),
    )
    op.create_index(
        op.f("ix_job_search_runs_provider"),
        "job_search_runs",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_search_runs_role"),
        "job_search_runs",
        ["role"],
        unique=False,
    )

    op.create_table(
        "raw_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("search_name", sa.String(length=200), nullable=False),
        sa.Column("source_key", sa.String(length=1024), nullable=False),
        sa.Column("job_url_direct", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("first_seen_run_id", sa.Integer(), nullable=False),
        sa.Column("last_seen_run_id", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["first_seen_run_id"],
            ["job_search_runs.id"],
            name=op.f("fk_raw_jobs_first_seen_run_id_job_search_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["last_seen_run_id"],
            ["job_search_runs.id"],
            name=op.f("fk_raw_jobs_last_seen_run_id_job_search_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_jobs")),
        sa.UniqueConstraint(
            "provider",
            "source_key",
            name="uq_raw_jobs_provider_source_key",
        ),
    )
    op.create_index(op.f("ix_raw_jobs_provider"), "raw_jobs", ["provider"], unique=False)
    op.create_index(op.f("ix_raw_jobs_role"), "raw_jobs", ["role"], unique=False)

    op.create_table(
        "normalized_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("is_remote", sa.Text(), nullable=False),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("date_posted", sa.Date(), nullable=True),
        sa.Column("job_url_direct", sa.Text(), nullable=False),
        sa.Column("min_amount", sa.Text(), nullable=False),
        sa.Column("max_amount", sa.Text(), nullable=False),
        sa.Column("last_seen_run_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["last_seen_run_id"],
            ["job_search_runs.id"],
            name=op.f("fk_normalized_jobs_last_seen_run_id_job_search_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_normalized_jobs")),
        sa.UniqueConstraint(
            "provider",
            "job_url_direct",
            name="uq_normalized_jobs_provider_job_url_direct",
        ),
    )
    op.create_index(
        op.f("ix_normalized_jobs_provider"),
        "normalized_jobs",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_normalized_jobs_role"),
        "normalized_jobs",
        ["role"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_normalized_jobs_role"), table_name="normalized_jobs")
    op.drop_index(op.f("ix_normalized_jobs_provider"), table_name="normalized_jobs")
    op.drop_table("normalized_jobs")
    op.drop_index(op.f("ix_raw_jobs_role"), table_name="raw_jobs")
    op.drop_index(op.f("ix_raw_jobs_provider"), table_name="raw_jobs")
    op.drop_table("raw_jobs")
    op.drop_index(op.f("ix_job_search_runs_role"), table_name="job_search_runs")
    op.drop_index(op.f("ix_job_search_runs_provider"), table_name="job_search_runs")
    op.drop_table("job_search_runs")

