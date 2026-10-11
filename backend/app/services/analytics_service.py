"""Staff / admin analytics foundation, computed from real submissions only.

Scope: every student account (classrooms do not exist yet). Access is
enforced by the routes (STAFF or ADMIN). Rules:

  active student      >= 1 judged submission in the last ACTIVE_WINDOW_DAYS days.
  average acceptance  mean of per-student acceptance rates over students with
                      >= 1 judged submission (each student weighs the same).
  needs attention     STUCK: >= STUCK_MIN_ATTEMPTS judged submissions and no
                      solved problem; INACTIVE: has submitted before but not in
                      the last INACTIVE_AFTER_DAYS days.
"""

from datetime import timedelta
from typing import Any

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.core.clock import as_date, local_date_expr, local_today, start_of_day_utc, to_utc
from app.core.config import settings
from app.core.exceptions import AppError
from app.models.problem import Problem, ProblemStatus
from app.models.progress import UserProblemProgress
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.schemas.analytics import (
    AnalyticsOverview,
    AttentionItem,
    DailyCount,
    ProblemInsight,
    SolvedProblemOut,
    StudentAnalyticsDetail,
    StudentAnalyticsRow,
    StudentProfileOut,
    StudentSort,
    TopStudent,
)
from app.schemas.common import Page, total_pages
from app.schemas.progress import ProblemRef
from app.services import leaderboard_service, progress_service
from app.services.progress_service import judged, rate
from app.utils.slug import escape_like

ACTIVE_WINDOW_DAYS = 7
INACTIVE_AFTER_DAYS = 14
STUCK_MIN_ATTEMPTS = 3
DAILY_WINDOW_DAYS = 14
STUDENT_NOT_FOUND = "Student not found."


def _student_totals():
    """Per-student totals from progress rows (solved counts published problems only)."""
    solved_published = and_(UserProblemProgress.solved_at.is_not(None), Problem.status == ProblemStatus.PUBLISHED)
    return (
        select(
            UserProblemProgress.user_id.label("user_id"),
            func.sum(case((solved_published, 1), else_=0)).label("solved"),
            func.sum(UserProblemProgress.attempt_count).label("attempts"),
            func.sum(UserProblemProgress.accepted_count).label("accepted"),
            func.max(UserProblemProgress.last_attempt_at).label("last_active_at"),
        )
        .join(Problem, Problem.id == UserProblemProgress.problem_id)
        .group_by(UserProblemProgress.user_id)
        .subquery()
    )


# ------------------------------------------------------------------ overview
def overview(db: Session) -> AnalyticsOverview:
    today = local_today()
    today_start = start_of_day_utc(today)
    accepted = Submission.status == SubmissionStatus.ACCEPTED
    students = select(User.id).where(User.role == UserRole.STUDENT)
    student_submission = and_(judged(), Submission.user_id.in_(students))

    total_students = db.scalar(select(func.count()).select_from(students.subquery())) or 0
    active_students = db.scalar(
        select(func.count(func.distinct(Submission.user_id))).where(
            student_submission,
            Submission.submitted_at >= start_of_day_utc(today - timedelta(days=ACTIVE_WINDOW_DAYS - 1)),
        )
    ) or 0
    counts: Any = db.execute(
        select(
            func.count(),
            func.coalesce(func.sum(case((accepted, 1), else_=0)), 0),
            func.coalesce(func.sum(case((Submission.submitted_at >= today_start, 1), else_=0)), 0),
            func.coalesce(func.sum(case((and_(accepted, Submission.submitted_at >= today_start), 1), else_=0)), 0),
        ).where(student_submission)
    ).one()
    total, accepted_total, today_total, accepted_today = counts

    totals = _student_totals()
    student_rows: Any = db.execute(
        select(User.id, User.full_name, totals.c.solved, totals.c.attempts, totals.c.accepted, totals.c.last_active_at)
        .join(totals, totals.c.user_id == User.id)
        .where(User.role == UserRole.STUDENT)
    ).all()
    with_submissions = [r for r in student_rows if (r.attempts or 0) > 0]
    average = (
        round(sum(int(r.accepted or 0) * 100 / int(r.attempts) for r in with_submissions) / len(with_submissions), 1)
        if with_submissions
        else 0.0
    )
    problems_solved = sum(int(r.solved or 0) for r in student_rows)

    return AnalyticsOverview(
        total_students=total_students,
        active_students=active_students,
        students_with_submissions=len(with_submissions),
        problems_solved=problems_solved,
        total_submissions=int(total),
        submissions_today=int(today_total),
        accepted_submissions=int(accepted_total),
        accepted_today=int(accepted_today),
        average_acceptance_rate=average,
        active_window_days=ACTIVE_WINDOW_DAYS,
        timezone=settings.APP_TIMEZONE,
        daily=_daily(db, today),
        top_students=[
            TopStudent(
                id=r.user_id,
                full_name=r.name,
                rank=r.rank,
                solved=int(r.solved),
                acceptance_rate=rate(int(r.accepted or 0), int(r.attempts or 0)),
            )
            for r in leaderboard_service.top(db, 5)
        ],
        needs_attention=_needs_attention(student_rows, today),
        problems=_problem_insights(db),
    )


def _daily(db: Session, today) -> list[DailyCount]:
    start = today - timedelta(days=DAILY_WINDOW_DAYS - 1)
    day = local_date_expr(db, Submission.submitted_at)
    rows: Any = db.execute(
        select(day, func.count(), func.sum(case((Submission.status == SubmissionStatus.ACCEPTED, 1), else_=0)))
        .where(judged(), Submission.submitted_at >= start_of_day_utc(start))
        .group_by(day)
    ).all()
    counts = {as_date(d): (int(n), int(a or 0)) for d, n, a in rows}
    return [
        DailyCount(date=d, submissions=counts.get(d, (0, 0))[0], accepted=counts.get(d, (0, 0))[1])
        for d in (start + timedelta(days=i) for i in range(DAILY_WINDOW_DAYS))
    ]


def _needs_attention(student_rows, today, limit: int = 10) -> list[AttentionItem]:
    inactive_before = start_of_day_utc(today - timedelta(days=INACTIVE_AFTER_DAYS - 1))
    items: list[AttentionItem] = []
    for r in student_rows:
        attempts, solved = int(r.attempts or 0), int(r.solved or 0)
        last = to_utc(r.last_active_at) if r.last_active_at else None
        if attempts >= STUCK_MIN_ATTEMPTS and solved == 0:
            reason, message = "STUCK", f"{attempts} attempts without a solved problem."
        elif last is not None and last < inactive_before:
            reason, message = "INACTIVE", f"No submissions in the last {INACTIVE_AFTER_DAYS} days."
        else:
            continue
        items.append(
            AttentionItem(
                id=r.id, full_name=r.full_name, reason=reason, message=message, solved=solved, attempts=attempts,
                last_active_at=last,
            )
        )
    # Stuck students first, then the longest inactive.
    items.sort(key=lambda i: (i.reason != "STUCK", i.last_active_at or inactive_before))
    return items[:limit]


def _problem_insights(db: Session, limit: int = 5) -> list[ProblemInsight]:
    rows: Any = db.execute(
        select(
            Problem.id,
            Problem.slug,
            Problem.title,
            Problem.difficulty,
            func.sum(UserProblemProgress.attempt_count).label("attempts"),
            func.sum(UserProblemProgress.accepted_count).label("accepted"),
            func.sum(case((UserProblemProgress.solved_at.is_not(None), 1), else_=0)).label("solved_by"),
        )
        .join(UserProblemProgress, UserProblemProgress.problem_id == Problem.id)
        .where(Problem.status == ProblemStatus.PUBLISHED)
        .group_by(Problem.id, Problem.slug, Problem.title, Problem.difficulty)
        .having(func.sum(UserProblemProgress.attempt_count) > 0)
        .order_by(func.sum(UserProblemProgress.attempt_count).desc(), Problem.id)
        .limit(limit)
    ).all()
    return [
        ProblemInsight(
            problem=ProblemRef(id=r.id, slug=r.slug, title=r.title, difficulty=r.difficulty),
            attempts=int(r.attempts),
            solved_by=int(r.solved_by),
            acceptance_rate=rate(int(r.accepted or 0), int(r.attempts)) if r.attempts else None,
        )
        for r in rows
    ]


# ------------------------------------------------------------------ students
def students(
    db: Session,
    *,
    search: str | None = None,
    sort: StudentSort = "solved",
    descending: bool = True,
    page: int = 1,
    limit: int = 20,
) -> Page[StudentAnalyticsRow]:
    totals = _student_totals()
    solved = func.coalesce(totals.c.solved, 0)
    attempts = func.coalesce(totals.c.attempts, 0)
    acceptance = (totals.c.accepted * 1.0) / func.nullif(totals.c.attempts, 0)
    query = (
        select(User, totals.c.solved, totals.c.attempts, totals.c.accepted, totals.c.last_active_at)
        .outerjoin(totals, totals.c.user_id == User.id)
        .where(User.role == UserRole.STUDENT)
    )
    if search and search.strip():
        pattern = f"%{escape_like(search.strip())}%"
        query = query.where(or_(User.full_name.ilike(pattern, escape="\\"), User.email.ilike(pattern, escape="\\")))
    column = {
        "solved": solved,
        "attempts": attempts,
        "acceptance": acceptance,
        "last_active": totals.c.last_active_at,
        "name": func.lower(User.full_name),
    }[sort]
    ordered = column.desc() if descending else column.asc()
    if sort in ("acceptance", "last_active"):
        ordered = ordered.nulls_last()
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows: Any = db.execute(query.order_by(ordered, User.id).offset((page - 1) * limit).limit(limit)).all()
    streaks = progress_service.current_streaks(db, [r[0].id for r in rows])
    items = [
        StudentAnalyticsRow(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            solved=int(s or 0),
            attempts=int(a or 0),
            accepted=int(acc or 0),
            acceptance_rate=rate(int(acc or 0), int(a)) if a else None,
            last_active_at=to_utc(last) if last else None,
            current_streak=streaks.get(user.id, 0),
        )
        for user, s, a, acc, last in rows
    ]
    return Page[StudentAnalyticsRow](
        items=items, page=page, page_size=limit, total=total, total_pages=total_pages(total, limit)
    )


def student_detail(db: Session, student_id: int) -> StudentAnalyticsDetail:
    user = db.get(User, student_id)
    if user is None or user.role != UserRole.STUDENT:
        raise AppError(404, STUDENT_NOT_FOUND)
    solved_rows: Any = db.execute(
        select(UserProblemProgress, Problem)
        .join(Problem, Problem.id == UserProblemProgress.problem_id)
        .where(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.solved_at.is_not(None),
            Problem.status == ProblemStatus.PUBLISHED,
        )
        .order_by(UserProblemProgress.solved_at.desc())
    ).all()
    return StudentAnalyticsDetail(
        student=StudentProfileOut(
            id=user.id, full_name=user.full_name, email=user.email, is_active=user.is_active, joined_at=user.created_at
        ),
        overview=progress_service.overview(db, user.id),
        difficulty=progress_service.difficulty_progress(db, user.id),
        topics=progress_service.topic_progress(db, user.id),
        languages=progress_service.language_stats(db, user.id),
        streak=progress_service.streak(db, user.id),
        heatmap=progress_service.heatmap(db, user.id, days=182),
        recent_activity=progress_service.activity(db, user.id, limit=10),
        solved_problems=[
            SolvedProblemOut(
                problem=ProblemRef(id=p.id, slug=p.slug, title=p.title, difficulty=p.difficulty),
                solved_at=to_utc(progress.solved_at),
                attempts=progress.attempt_count,
                best_runtime_ms=progress.best_runtime_ms,
                best_memory_kb=progress.best_memory_kb,
            )
            for progress, p in solved_rows
        ],
    )
