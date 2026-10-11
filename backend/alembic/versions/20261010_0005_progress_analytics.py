"""progress & analytics: per-test results, per-problem progress, first accepted

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-10

No submission is removed or changed in a way that loses information.
  * submission_test_results (new): one row per executed official test. The
    per-test results that Phase 5 kept in the JSON column submissions.results
    are copied into it, then that column is dropped (downgrade copies them back).
  * user_problem_progress (new): attempts, accepted count, solved_at, best
    runtime / memory per student and problem, computed from existing judged
    submissions (INSERT ... ON CONFLICT DO UPDATE: re-running gives the same
    rows, never duplicates).
  * submissions: is_first_accepted (unique per student + problem through a
    partial unique index), effective time/memory limit snapshot, and an index
    for per-student history by time.
"""
import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEST_STATUSES = (
    "PASSED", "FAILED", "COMPILE_ERROR", "RUNTIME_ERROR", "TIME_LIMIT_EXCEEDED",
    "MEMORY_LIMIT_EXCEEDED", "OUTPUT_LIMIT_EXCEEDED", "SYSTEM_ERROR", "EXECUTED",
)
# Verdicts on the student's code (in-progress and infrastructure statuses excluded).
JUDGED = (
    "ACCEPTED", "WRONG_ANSWER", "COMPILE_ERROR", "RUNTIME_ERROR", "TIME_LIMIT_EXCEEDED",
    "MEMORY_LIMIT_EXCEEDED", "OUTPUT_LIMIT_EXCEEDED",
)
# Phase 5 per-test verdict -> per-test status (and back for downgrade).
STATUS_FOR_VERDICT = {
    "ACCEPTED": "PASSED",
    "WRONG_ANSWER": "FAILED",
    "RUNTIME_ERROR": "RUNTIME_ERROR",
    "TIME_LIMIT_EXCEEDED": "TIME_LIMIT_EXCEEDED",
    "MEMORY_LIMIT_EXCEEDED": "MEMORY_LIMIT_EXCEEDED",
    "OUTPUT_LIMIT_EXCEEDED": "OUTPUT_LIMIT_EXCEEDED",
    "SYSTEM_ERROR": "SYSTEM_ERROR",
    "EXECUTION_TIMEOUT": "SYSTEM_ERROR",
}
VERDICT_FOR_STATUS = {
    "PASSED": "ACCEPTED",
    "FAILED": "WRONG_ANSWER",
    "RUNTIME_ERROR": "RUNTIME_ERROR",
    "TIME_LIMIT_EXCEEDED": "TIME_LIMIT_EXCEEDED",
    "MEMORY_LIMIT_EXCEEDED": "MEMORY_LIMIT_EXCEEDED",
    "OUTPUT_LIMIT_EXCEEDED": "OUTPUT_LIMIT_EXCEEDED",
    "SYSTEM_ERROR": "SYSTEM_ERROR",
    "COMPILE_ERROR": "COMPILE_ERROR",
}
_JUDGED_SQL = ", ".join(f"'{s}'" for s in JUDGED)


def upgrade() -> None:
    op.create_table(
        "submission_test_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_case_id", sa.Integer(), sa.ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False),
        sa.Column("status", sa.Enum(*TEST_STATUSES, name="test_result_status"), nullable=False),
        sa.Column("runtime_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("input_data", sa.Text(), nullable=True),
        sa.Column("expected_output", sa.Text(), nullable=True),
        sa.Column("actual_output", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("submission_id", "position", name="uq_submission_test_results_position"),
    )
    op.create_index("ix_submission_test_results_test_case", "submission_test_results", ["test_case_id"])

    op.create_table(
        "user_problem_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("problem_id", sa.Integer(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("accepted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("first_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("solved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("best_runtime_ms", sa.Integer(), nullable=True),
        sa.Column("best_memory_kb", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "problem_id", name="uq_user_problem_progress_user_problem"),
    )
    op.create_index("ix_user_problem_progress_problem", "user_problem_progress", ["problem_id"])

    op.add_column("submissions", sa.Column("is_first_accepted", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("submissions", sa.Column("time_limit_ms", sa.Integer(), nullable=True))
    op.add_column("submissions", sa.Column("memory_limit_kb", sa.Integer(), nullable=True))
    op.create_index("ix_submissions_user_submitted", "submissions", ["user_id", "submitted_at"])

    _copy_json_results_into_table()
    _compute_progress_and_first_accepted()

    op.create_index(
        "uq_submissions_first_accepted",
        "submissions",
        ["user_id", "problem_id"],
        unique=True,
        postgresql_where=sa.text("is_first_accepted"),
    )
    op.drop_column("submissions", "results")


def _copy_json_results_into_table() -> None:
    bind = op.get_bind()
    test_cases: dict[int, list[tuple[int, bool]]] = {}
    rows = bind.execute(
        sa.text("SELECT id, problem_id, total_tests, results FROM submissions ORDER BY id")
    ).all()
    for submission_id, problem_id, total_tests, results in rows:
        if isinstance(results, str):
            results = json.loads(results)
        entries = [r for r in results or [] if r.get("kind") in ("public", "hidden") and r.get("verdict") in STATUS_FOR_VERDICT]
        if not entries:
            continue
        if problem_id not in test_cases:
            test_cases[problem_id] = [
                (tc_id, hidden)
                for tc_id, hidden in bind.execute(
                    sa.text("SELECT id, is_hidden FROM test_cases WHERE problem_id = :p ORDER BY order_index, id"),
                    {"p": problem_id},
                ).all()
            ]
        current = test_cases[problem_id]
        # Link to the test case only when the problem still has exactly the
        # tests it was judged with (same count, same public/hidden order).
        kinds = [r["kind"] == "hidden" for r in entries]
        linkable = len(current) == total_tests and [hidden for _, hidden in current[: len(kinds)]] == kinds
        for position, entry in enumerate(entries, start=1):
            hidden = entry["kind"] == "hidden"
            bind.execute(
                sa.text(
                    "INSERT INTO submission_test_results (submission_id, test_case_id, position, is_hidden, status,"
                    " runtime_ms, memory_kb, input_data, expected_output, actual_output, error_message)"
                    " VALUES (:submission_id, :test_case_id, :position, :is_hidden, :status, :runtime_ms, :memory_kb,"
                    " :input_data, :expected_output, :actual_output, :error_message)"
                ),
                {
                    "submission_id": submission_id,
                    "test_case_id": current[position - 1][0] if linkable else None,
                    "position": position,
                    "is_hidden": hidden,
                    "status": STATUS_FOR_VERDICT[entry["verdict"]],
                    "runtime_ms": entry.get("runtime_ms"),
                    "memory_kb": entry.get("memory_kb"),
                    # Hidden tests never carry test data.
                    "input_data": None if hidden else entry.get("input"),
                    "expected_output": None if hidden else entry.get("expected_output"),
                    "actual_output": None if hidden else entry.get("actual_output"),
                    "error_message": None if hidden else entry.get("stderr"),
                },
            )


def _compute_progress_and_first_accepted() -> None:
    op.execute(
        f"""
        INSERT INTO user_problem_progress
            (user_id, problem_id, attempt_count, accepted_count, first_attempt_at, last_attempt_at,
             solved_at, best_runtime_ms, best_memory_kb)
        SELECT user_id, problem_id,
               count(*),
               count(*) FILTER (WHERE status = 'ACCEPTED'),
               min(submitted_at),
               max(submitted_at),
               min(submitted_at) FILTER (WHERE status = 'ACCEPTED'),
               min(runtime_ms) FILTER (WHERE status = 'ACCEPTED' AND runtime_ms >= 0),
               min(memory_kb) FILTER (WHERE status = 'ACCEPTED' AND memory_kb >= 0)
        FROM submissions
        WHERE status::text IN ({_JUDGED_SQL})
        GROUP BY user_id, problem_id
        ON CONFLICT (user_id, problem_id) DO UPDATE SET
            attempt_count = EXCLUDED.attempt_count,
            accepted_count = EXCLUDED.accepted_count,
            first_attempt_at = EXCLUDED.first_attempt_at,
            last_attempt_at = EXCLUDED.last_attempt_at,
            solved_at = EXCLUDED.solved_at,
            best_runtime_ms = EXCLUDED.best_runtime_ms,
            best_memory_kb = EXCLUDED.best_memory_kb,
            updated_at = now()
        """
    )
    op.execute("UPDATE submissions SET is_first_accepted = false WHERE is_first_accepted")
    op.execute(
        """
        UPDATE submissions SET is_first_accepted = true
        WHERE id IN (
            SELECT DISTINCT ON (user_id, problem_id) id
            FROM submissions
            WHERE status = 'ACCEPTED'
            ORDER BY user_id, problem_id, submitted_at, id
        )
        """
    )


def downgrade() -> None:
    op.add_column("submissions", sa.Column("results", sa.JSON(), server_default=sa.text("'[]'"), nullable=False))
    bind = op.get_bind()
    by_submission: dict[int, list[dict]] = {}
    for row in bind.execute(
        sa.text(
            "SELECT submission_id, is_hidden, status, runtime_ms, memory_kb, input_data, expected_output,"
            " actual_output, error_message FROM submission_test_results ORDER BY submission_id, position"
        )
    ).mappings():
        entries = by_submission.setdefault(row["submission_id"], [])
        kind = "hidden" if row["is_hidden"] else "public"
        entries.append(
            {
                "index": sum(1 for e in entries if e["kind"] == kind) + 1,
                "kind": kind,
                "verdict": VERDICT_FOR_STATUS.get(row["status"], "SYSTEM_ERROR"),
                "runtime_ms": row["runtime_ms"],
                "memory_kb": row["memory_kb"],
                "input": row["input_data"],
                "expected_output": row["expected_output"],
                "actual_output": row["actual_output"],
                "stderr": row["error_message"],
            }
        )
    for submission_id, entries in by_submission.items():
        bind.execute(
            sa.text("UPDATE submissions SET results = CAST(:results AS JSON) WHERE id = :id"),
            {"results": json.dumps(entries), "id": submission_id},
        )

    op.drop_index("uq_submissions_first_accepted", table_name="submissions")
    op.drop_index("ix_submissions_user_submitted", table_name="submissions")
    op.drop_column("submissions", "memory_limit_kb")
    op.drop_column("submissions", "time_limit_ms")
    op.drop_column("submissions", "is_first_accepted")
    op.drop_index("ix_user_problem_progress_problem", table_name="user_problem_progress")
    op.drop_table("user_problem_progress")
    op.drop_index("ix_submission_test_results_test_case", table_name="submission_test_results")
    op.drop_table("submission_test_results")
    sa.Enum(name="test_result_status").drop(bind, checkfirst=True)
