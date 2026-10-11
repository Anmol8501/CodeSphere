"""code drafts: per-user, per-problem, per-language editor drafts

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-09

Only adds the code_drafts table. Existing tables and data are untouched.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "code_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "problem_id", sa.Integer(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
        ),
        # The enum type already exists (created in 0002).
        sa.Column(
            "language",
            sa.Enum("CPP", "JAVA", "PYTHON", name="programming_language", create_type=False),
            nullable=False,
        ),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "problem_id", "language", name="uq_code_drafts_user_problem_language"),
    )
    # user_id lookups use the unique index (user_id is its first column).
    op.create_index("ix_code_drafts_problem_id", "code_drafts", ["problem_id"])
    op.create_index("ix_code_drafts_updated_at", "code_drafts", ["updated_at"])


def downgrade() -> None:
    op.drop_table("code_drafts")
