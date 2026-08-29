"""Canonicalize research job states and required timestamps.

Revision ID: 20260830_0002
Revises: 20260730_0001
"""

from alembic import op
import sqlalchemy as sa

revision = "20260830_0002"
down_revision = "20260730_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE research_jobs SET status = 'queued' WHERE status IS NULL OR status = 'pending'")
    op.execute("UPDATE research_jobs SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")

    op.alter_column("research_jobs", "status", existing_type=sa.String(), nullable=False, server_default="queued")
    op.alter_column("research_jobs", "created_at", existing_type=sa.DateTime(), nullable=False)
    op.create_check_constraint(
        "ck_research_jobs_status",
        "research_jobs",
        "status IN ('queued', 'in_progress', 'completed', 'failed')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_research_jobs_status", "research_jobs", type_="check")
    op.alter_column("research_jobs", "created_at", existing_type=sa.DateTime(), nullable=True)
    op.alter_column("research_jobs", "status", existing_type=sa.String(), nullable=True, server_default=None)
