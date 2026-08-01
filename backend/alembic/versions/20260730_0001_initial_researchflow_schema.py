"""initial researchflow schema

Revision ID: 20260730_0001
Revises:
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa


revision = "20260730_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("research_jobs.id"), nullable=True),
        sa.Column("markdown", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "research_steps",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("research_jobs.id"), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=True),
        sa.Column("agent_name", sa.String(), nullable=True, index=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("input", sa.Text(), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("research_jobs.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sources")
    op.drop_table("research_steps")
    op.drop_table("reports")
    op.drop_table("research_jobs")
