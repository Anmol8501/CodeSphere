"""Submission history and detail. Every query is scoped to the signed-in student.

Per-test results come from `submission_test_results`. Hidden tests are
returned with their status, runtime and memory only: their input, expected
output and the program's output on them are never stored or returned.
"""

from datetime import timedelta
from typing import Any, Literal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.clock import local_today, start_of_day_utc
from app.core.exceptions import AppError
from app.core.languages import LANGUAGES
from app.models.problem import Problem, ProgrammingLanguage
from app.models.submission import (
    INFRASTRUCTURE_STATUSES,
    Submission,
    SubmissionStatus,
    SubmissionTestResult,
)
from app.models.user import User
from app.schemas.common import Page, total_pages
from app.schemas.workspace import (
    SubmissionDetail,
    SubmissionPerformance,
    SubmissionProblemRef,
    SubmissionSummary,
    TestResultOut,
)
from app.services.judging.runner import limits_for
from app.utils.slug import escape_like

SUBMISSION_NOT_FOUND = "Submission not found."
# Percentiles are shown only when this many OTHER students have an accepted
# solution in the same language for the same problem (otherwise: not shown).
MIN_PERCENTILE_SAMPLE = 10

Period = Literal["today", "7d", "30d", "all"]
_PERIOD_DAYS = {"today": 1, "7d": 7, "30d": 30}


# ------------------------------------------------------------------ history
def _summary(submission: Submission) -> SubmissionSummary:
    return SubmissionSummary(
        id=submission.id,
        problem=SubmissionProblemRef.model_validate(submission.problem),
        language=submission.language,
        status=submission.status,
        passed_tests=submission.passed_tests,
        total_tests=submission.total_tests,
        runtime_ms=submission.runtime_ms,
        memory_kb=submission.memory_kb,
        is_first_accepted=submission.is_first_accepted,
        submitted_at=submission.submitted_at,
    )


def list_for_user(
    db: Session,
    user: User,
    *,
    problem_slug: str | None = None,
    problem_id: int | None = None,
    language: ProgrammingLanguage | None = None,
    status: SubmissionStatus | None = None,
    search: str | None = None,
    period: Period = "all",
    page: int = 1,
    limit: int = 20,
) -> Page[SubmissionSummary]:
    query = select(Submission).where(Submission.user_id == user.id)
    if problem_id is not None:
        query = query.where(Submission.problem_id == problem_id)
    if problem_slug:
        query = query.where(Submission.problem_id.in_(select(Problem.id).where(Problem.slug == problem_slug)))
    if language:
        query = query.where(Submission.language == language)
    if status:
        query = query.where(Submission.status == status)
    if search and search.strip():
        pattern = f"%{escape_like(search.strip())}%"
        query = query.where(
            Submission.problem_id.in_(
                select(Problem.id).where(
                    or_(Problem.title.ilike(pattern, escape="\\"), Problem.slug.ilike(pattern, escape="\\"))
                )
            )
        )
    if period in _PERIOD_DAYS:
        # Calendar days in the application timezone: "today" starts at local midnight.
        since = local_today() - timedelta(days=_PERIOD_DAYS[period] - 1)
        query = query.where(Submission.submitted_at >= start_of_day_utc(since))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.options(selectinload(Submission.problem))
        .order_by(Submission.submitted_at.desc(), Submission.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return Page[SubmissionSummary](
        items=[_summary(s) for s in rows], page=page, page_size=limit, total=total, total_pages=total_pages(total, limit)
    )


def get_for_user(db: Session, user: User, submission_id: int) -> Submission:
    """The user's own submission. Someone else's id looks exactly like a missing one."""
    submission = db.scalar(
        select(Submission)
        .where(Submission.id == submission_id, Submission.user_id == user.id)
        .options(selectinload(Submission.problem), selectinload(Submission.test_results))
    )
    if submission is None:
        raise AppError(404, SUBMISSION_NOT_FOUND)
    return submission


# ------------------------------------------------------------------ detail
def result_out(row: SubmissionTestResult) -> TestResultOut:
    base = TestResultOut(
        index=row.position,
        kind="hidden" if row.is_hidden else "public",
        status=row.status,
        runtime_ms=row.runtime_ms,
        memory_kb=row.memory_kb,
    )
    if row.is_hidden:
        return base  # status / runtime / memory only, never test data
    return base.model_copy(
        update={
            "input": row.input_data,
            "expected_output": row.expected_output,
            "actual_output": row.actual_output,
            "stderr": row.error_message,
        }
    )


def _effective_limits(submission: Submission) -> tuple[int | None, int | None]:
    if submission.time_limit_ms is not None and submission.memory_limit_kb is not None:
        return submission.time_limit_ms, submission.memory_limit_kb
    # Judged before limits were recorded: derive them from the problem's current limits.
    problem = submission.problem
    if problem is None:
        return None, None
    limits = limits_for(LANGUAGES[submission.language], problem.time_limit_ms, problem.memory_limit_kb, max_output_kb=1024)
    return round(limits.cpu_time_s * 1000), limits.memory_kb


def performance(db: Session, submission: Submission) -> SubmissionPerformance | None:
    """Runtime / memory percentiles for an ACCEPTED submission, from real data only.

    Compared with each OTHER student's best accepted runtime / memory for the
    same problem and language. "Faster than X%" = share of those students whose
    best runtime is strictly slower. Returned as None unless at least
    MIN_PERCENTILE_SAMPLE students can be compared (no invented numbers).
    """
    if submission.status != SubmissionStatus.ACCEPTED:
        return None
    accepted = (
        select(
            Submission.user_id,
            func.min(case((Submission.runtime_ms >= 0, Submission.runtime_ms))).label("runtime"),
            func.min(case((Submission.memory_kb >= 0, Submission.memory_kb))).label("memory"),
        )
        .where(
            Submission.problem_id == submission.problem_id,
            Submission.language == submission.language,
            Submission.status == SubmissionStatus.ACCEPTED,
            Submission.user_id != submission.user_id,
        )
        .group_by(Submission.user_id)
        .subquery()
    )
    runtime, memory = submission.runtime_ms, submission.memory_kb
    counts: Any = db.execute(
        select(
            func.count(),
            func.count(accepted.c.runtime),
            func.sum(case((accepted.c.runtime > (runtime if runtime is not None else -1), 1), else_=0)),
            func.count(accepted.c.memory),
            func.sum(case((accepted.c.memory > (memory if memory is not None else -1), 1), else_=0)),
        ).select_from(accepted)
    ).one()
    sample, runtime_n, slower, memory_n, heavier = counts

    def percentile(value: int | None, n: int, beaten: int | None) -> float | None:
        if value is None or value < 0 or n < MIN_PERCENTILE_SAMPLE:
            return None
        return round(int(beaten or 0) * 100 / n, 1)

    return SubmissionPerformance(
        runtime_percentile=percentile(runtime, runtime_n, slower),
        memory_percentile=percentile(memory, memory_n, heavier),
        compared_with=sample,
        min_sample=MIN_PERCENTILE_SAMPLE,
    )


def to_detail(db: Session, submission: Submission) -> SubmissionDetail:
    results = [result_out(r) for r in submission.test_results]
    judged_tests = submission.status not in (*INFRASTRUCTURE_STATUSES, SubmissionStatus.COMPILE_ERROR)
    time_limit_ms, memory_limit_kb = _effective_limits(submission)
    return SubmissionDetail(
        **_summary(submission).model_dump(),
        error_message=submission.error_message,
        results=results,
        # Judging stops at the first failing test: the rest were not executed.
        not_run_tests=max(submission.total_tests - len(results), 0) if judged_tests else 0,
        time_limit_ms=time_limit_ms,
        memory_limit_kb=memory_limit_kb,
        performance=performance(db, submission),
        finished_at=submission.finished_at,
        source_code=submission.source_code,
    )
