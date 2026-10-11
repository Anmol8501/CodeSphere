"""code execution: problem limits, hidden harness code, judged submissions

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-10

Adds columns and indexes only; no existing data is removed.
  * problems.time_limit_ms / memory_limit_kb (per-problem judge limits)
  * starter_codes.driver_code (hidden harness for function-style problems)
  * submissions: test counts, safe error message, per-test results, finished_at
  * submission_status: COMPILATION_ERROR renamed to COMPILE_ERROR, and
    RUNNING / MEMORY_LIMIT_EXCEEDED / OUTPUT_LIMIT_EXCEEDED / SYSTEM_ERROR /
    EXECUTION_TIMEOUT added
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_STATUSES = ("RUNNING", "MEMORY_LIMIT_EXCEEDED", "OUTPUT_LIMIT_EXCEEDED", "SYSTEM_ERROR", "EXECUTION_TIMEOUT")
OLD_STATUSES = ("PENDING", "ACCEPTED", "WRONG_ANSWER", "TIME_LIMIT_EXCEEDED", "RUNTIME_ERROR", "COMPILATION_ERROR")


def upgrade() -> None:
    op.add_column("problems", sa.Column("time_limit_ms", sa.Integer(), server_default="2000", nullable=False))
    op.add_column("problems", sa.Column("memory_limit_kb", sa.Integer(), server_default="262144", nullable=False))
    op.add_column("starter_codes", sa.Column("driver_code", sa.Text(), nullable=True))

    op.add_column("submissions", sa.Column("passed_tests", sa.Integer(), server_default="0", nullable=False))
    op.add_column("submissions", sa.Column("total_tests", sa.Integer(), server_default="0", nullable=False))
    op.add_column("submissions", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("submissions", sa.Column("results", sa.JSON(), server_default=sa.text("'[]'"), nullable=False))
    op.add_column("submissions", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_submissions_submitted_at", "submissions", ["submitted_at"])
    op.create_index("ix_test_cases_problem_hidden", "test_cases", ["problem_id", "is_hidden"])

    # PostgreSQL 12+ allows these inside the migration transaction.
    op.execute("ALTER TYPE submission_status RENAME VALUE 'COMPILATION_ERROR' TO 'COMPILE_ERROR'")
    for value in NEW_STATUSES:
        op.execute(f"ALTER TYPE submission_status ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Map statuses that did not exist before onto the closest old ones, then
    # rebuild the old enum type (PostgreSQL cannot drop enum values).
    op.execute(
        "UPDATE submissions SET status = 'PENDING' "
        "WHERE status::text IN ('RUNNING', 'SYSTEM_ERROR', 'EXECUTION_TIMEOUT')"
    )
    op.execute(
        "UPDATE submissions SET status = 'RUNTIME_ERROR' "
        "WHERE status::text IN ('MEMORY_LIMIT_EXCEEDED', 'OUTPUT_LIMIT_EXCEEDED')"
    )
    op.execute("ALTER TYPE submission_status RENAME TO submission_status_v4")
    old_values = ", ".join(f"'{v}'" for v in OLD_STATUSES)
    op.execute(f"CREATE TYPE submission_status AS ENUM ({old_values})")
    op.execute(
        "ALTER TABLE submissions ALTER COLUMN status TYPE submission_status USING "
        "(CASE status::text WHEN 'COMPILE_ERROR' THEN 'COMPILATION_ERROR' ELSE status::text END)::submission_status"
    )
    op.execute("DROP TYPE submission_status_v4")

    op.drop_index("ix_test_cases_problem_hidden", table_name="test_cases")
    op.drop_index("ix_submissions_submitted_at", table_name="submissions")
    for column in ("finished_at", "results", "error_message", "total_tests", "passed_tests"):
        op.drop_column("submissions", column)
    op.drop_column("starter_codes", "driver_code")
    op.drop_column("problems", "memory_limit_kb")
    op.drop_column("problems", "time_limit_ms")
