"""Builds dashboard payloads from real data only."""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    AdminDashboard,
    DashboardUser,
    ServiceStatus,
    StaffDashboard,
    StaffStatistics,
    StudentDashboard,
    StudentStatistics,
    TopicProgress,
)
from app.services import execution_service, learning_service, progress_service, user_service

# Topics shown in the student dashboard "Learning Progress" card.
DASHBOARD_TOPIC_LIMIT = 8

logger = logging.getLogger("codearena")


def build_student_dashboard(db: Session, user: User) -> StudentDashboard:
    # Everything comes from the database: published problems and the student's
    # judged submissions (solved = ACCEPTED; judge failures are ignored). With
    # no submissions the honest values are zero / empty lists. The heatmap,
    # activity feed and recent submissions have their own endpoints so each
    # dashboard section can load (or fail) on its own.
    path = learning_service.build_learning_path(db, user)
    topics = [t for t in path.topics if t.problem_count > 0][:DASHBOARD_TOPIC_LIMIT]
    overview = progress_service.overview(db, user.id)
    streak = progress_service.streak(db, user.id)
    return StudentDashboard(
        user=DashboardUser.model_validate(user),
        statistics=StudentStatistics(
            problems_solved=overview.solved_problems,
            total_problems=overview.total_problems,
            attempted_problems=overview.attempted_problems,
            total_attempts=overview.total_submissions,
            accepted_submissions=overview.accepted_submissions,
            acceptance_rate=overview.acceptance_rate,
            current_streak=streak.current_streak,
            longest_streak=streak.longest_streak,
            active_today=streak.active_today,
        ),
        difficulty=progress_service.difficulty_progress(db, user.id),
        learning_progress=[
            TopicProgress(slug=t.slug, topic=t.name, solved=t.solved_count, total=t.problem_count, percent=t.progress)
            for t in topics
        ],
        continue_learning=progress_service.recommendations(db, user.id),
        timezone=settings.APP_TIMEZONE,
    )


def build_staff_dashboard(db: Session, user: User) -> StaffDashboard:
    # Students is a real count of STUDENT accounts (same query as the admin
    # dashboard). Classrooms, assignments and contests arrive in later phases,
    # so their honest value is still zero.
    return StaffDashboard(
        user=DashboardUser.model_validate(user),
        statistics=StaffStatistics(students=user_service.count_users(db, role=UserRole.STUDENT)),
    )


def _database_status(db: Session) -> ServiceStatus:
    try:
        db.execute(text("SELECT 1"))
        return ServiceStatus(key="database", name="Database", status="online", detail="PostgreSQL responding")
    except Exception:  # pragma: no cover - exercised only when the DB is down
        logger.exception("Database health check failed")
        return ServiceStatus(key="database", name="Database", status="offline", detail="Health check failed")


def _judge_status() -> ServiceStatus:
    if not execution_service.is_configured():
        return ServiceStatus(key="judge", name="Judge Engine", status="not_connected", detail="Judge0 is not configured")
    if execution_service.check_available():
        return ServiceStatus(key="judge", name="Judge Engine", status="online", detail="Judge0 responding")
    return ServiceStatus(key="judge", name="Judge Engine", status="offline", detail="Judge0 not responding")


def build_admin_dashboard(db: Session) -> AdminDashboard:
    total_users = user_service.count_users(db)
    active_users = user_service.count_users(db, active_only=True)
    return AdminDashboard(
        total_users=total_users,
        total_students=user_service.count_users(db, role=UserRole.STUDENT),
        total_staff=user_service.count_users(db, role=UserRole.STAFF),
        total_admins=user_service.count_users(db, role=UserRole.ADMIN),
        active_users=active_users,
        inactive_users=total_users - active_users,
        system_status=[
            # Answering this request proves the API and auth layers are up.
            ServiceStatus(key="api", name="API Server", status="online", detail="FastAPI responding"),
            _database_status(db),
            ServiceStatus(key="auth", name="Authentication", status="online", detail="JWT verification active"),
            _judge_status(),
            ServiceStatus(key="ai", name="AI Service", status="not_connected", detail="Planned for a later phase"),
        ],
    )
