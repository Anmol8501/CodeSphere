"""problem database: topics, tags, problems, examples, starter code, test cases, submissions

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-02

Only adds new tables. The users table from 0001 is referenced, never altered.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

problem_difficulty = sa.Enum("EASY", "MEDIUM", "HARD", name="problem_difficulty")
problem_status = sa.Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="problem_status")
programming_language = sa.Enum("CPP", "JAVA", "PYTHON", name="programming_language")
submission_status = sa.Enum(
    "PENDING",
    "ACCEPTED",
    "WRONG_ANSWER",
    "TIME_LIMIT_EXCEEDED",
    "RUNTIME_ERROR",
    "COMPILATION_ERROR",
    name="submission_status",
)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("icon", sa.String(length=40), nullable=True),
        sa.Column("learning_outcomes", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "parent_topic_id",
            sa.Integer(),
            sa.ForeignKey("topics.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamps(),
    )
    op.create_index("ix_topics_slug", "topics", ["slug"], unique=True)
    op.create_index("ix_topics_order_index", "topics", ["order_index"])
    op.create_index("ix_topics_parent_topic_id", "topics", ["parent_topic_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tags_slug", "tags", ["slug"], unique=True)

    op.create_table(
        "problems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", problem_difficulty, nullable=False),
        sa.Column(
            "topic_id", sa.Integer(), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("constraints", sa.Text(), nullable=False),
        sa.Column("input_format", sa.Text(), nullable=False),
        sa.Column("output_format", sa.Text(), nullable=False),
        sa.Column("status", problem_status, nullable=False),
        sa.Column(
            "created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        *_timestamps(),
    )
    op.create_index("ix_problems_slug", "problems", ["slug"], unique=True)
    op.create_index("ix_problems_topic_id", "problems", ["topic_id"])
    op.create_index("ix_problems_difficulty", "problems", ["difficulty"])
    op.create_index("ix_problems_status", "problems", ["status"])
    op.create_index("ix_problems_created_by", "problems", ["created_by"])

    op.create_table(
        "problem_tags",
        sa.Column(
            "problem_id",
            sa.Integer(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    op.create_index("ix_problem_tags_tag_id", "problem_tags", ["tag_id"])

    op.create_table(
        "problem_examples",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "problem_id",
            sa.Integer(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
    )
    op.create_index("ix_problem_examples_problem_id", "problem_examples", ["problem_id"])

    op.create_table(
        "starter_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "problem_id",
            sa.Integer(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language", programming_language, nullable=False),
        sa.Column("starter_code", sa.Text(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("problem_id", "language", name="uq_starter_codes_problem_language"),
    )
    op.create_index("ix_starter_codes_problem_id", "starter_codes", ["problem_id"])

    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "problem_id",
            sa.Integer(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("input_data", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_test_cases_problem_id", "test_cases", ["problem_id"])

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "problem_id",
            sa.Integer(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # The enum type already exists (created with starter_codes).
        sa.Column(
            "language",
            sa.Enum("CPP", "JAVA", "PYTHON", name="programming_language", create_type=False),
            nullable=False,
        ),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("status", submission_status, nullable=False),
        sa.Column("runtime_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_submissions_user_problem", "submissions", ["user_id", "problem_id"])
    op.create_index("ix_submissions_problem_id", "submissions", ["problem_id"])
    op.create_index("ix_submissions_status", "submissions", ["status"])


def downgrade() -> None:
    # Children first, then parents. The users table is left untouched.
    op.drop_table("submissions")
    op.drop_table("test_cases")
    op.drop_table("starter_codes")
    op.drop_table("problem_examples")
    op.drop_table("problem_tags")
    op.drop_table("problems")
    op.drop_table("tags")
    op.drop_table("topics")

    bind = op.get_bind()
    for enum_type in (submission_status, programming_language, problem_status, problem_difficulty):
        enum_type.drop(bind, checkfirst=True)
