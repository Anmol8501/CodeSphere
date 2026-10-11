"""Global leaderboard, computed from user_problem_progress with SQL window ranking.

Ranking rule (also returned by the API and documented in docs/ANALYTICS.md):
  1. problems solved (distinct published problems with an ACCEPTED submission), high to low
  2. acceptance rate (accepted / judged submissions), high to low
  Students equal on both share a rank ("1, 2, 2, 4": standard competition ranking).
  Within a shared rank, the student who reached their solved count first is
  listed first (then by name). Only active students with >= 1 solved problem
  are ranked. Only the name, rank, solved count and acceptance rate are exposed.
"""

from sqlalchemy import Select, and_, case, func, select
from sqlalchemy.orm import Session

from app.models.problem import Problem, ProblemStatus
from app.models.progress import UserProblemProgress
from app.models.user import User, UserRole
from app.schemas.common import total_pages
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardPage
from app.services.progress_service import rate

RANKING_RULE = (
    "Ranked by problems solved, then acceptance rate. Students equal on both share a rank (1, 2, 2, 4); "
    "within a tie, whoever reached that solved count first is listed first. "
    "Only active students with at least one solved problem are ranked."
)


def ranked_students() -> Select:
    """One row per ranked student: user_id, name, solved, attempts, accepted, last_solved_at, rank."""
    solved_published = and_(UserProblemProgress.solved_at.is_not(None), Problem.status == ProblemStatus.PUBLISHED)
    totals = (
        select(
            User.id.label("user_id"),
            User.full_name.label("name"),
            func.sum(case((solved_published, 1), else_=0)).label("solved"),
            func.sum(UserProblemProgress.attempt_count).label("attempts"),
            func.sum(UserProblemProgress.accepted_count).label("accepted"),
            func.max(case((solved_published, UserProblemProgress.solved_at))).label("last_solved_at"),
        )
        .join(UserProblemProgress, UserProblemProgress.user_id == User.id)
        .join(Problem, Problem.id == UserProblemProgress.problem_id)
        .where(User.role == UserRole.STUDENT, User.is_active.is_(True))
        .group_by(User.id, User.full_name)
        .subquery()
    )
    acceptance = (totals.c.accepted * 1.0) / func.nullif(totals.c.attempts, 0)
    return (
        select(
            totals.c.user_id,
            totals.c.name,
            totals.c.solved,
            totals.c.attempts,
            totals.c.accepted,
            totals.c.last_solved_at,
            func.rank().over(order_by=(totals.c.solved.desc(), acceptance.desc())).label("rank"),
        )
        .where(totals.c.solved > 0)
    )


def _entry(row, current_user_id: int | None) -> LeaderboardEntry:
    return LeaderboardEntry(
        rank=row.rank,
        name=row.name,
        solved=int(row.solved),
        acceptance_rate=rate(int(row.accepted or 0), int(row.attempts or 0)),
        is_current_user=row.user_id == current_user_id,
    )


def top(db: Session, limit: int):
    """The first `limit` ranked rows (with user_id, for staff views)."""
    ranked = ranked_students().subquery()
    return db.execute(
        select(ranked)
        .order_by(ranked.c.rank, ranked.c.last_solved_at, ranked.c.name, ranked.c.user_id)
        .limit(limit)
    ).all()


def leaderboard(db: Session, current_user: User, *, page: int = 1, limit: int = 20) -> LeaderboardPage:
    ranked = ranked_students().subquery()
    total = db.scalar(select(func.count()).select_from(ranked)) or 0
    rows = db.execute(
        select(ranked)
        .order_by(ranked.c.rank, ranked.c.last_solved_at, ranked.c.name, ranked.c.user_id)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    mine = db.execute(select(ranked).where(ranked.c.user_id == current_user.id)).first()
    return LeaderboardPage(
        items=[_entry(r, current_user.id) for r in rows],
        page=page,
        page_size=limit,
        total=total,
        total_pages=total_pages(total, limit),
        current_user=_entry(mine, current_user.id) if mine else None,
        ranking_rule=RANKING_RULE,
    )
