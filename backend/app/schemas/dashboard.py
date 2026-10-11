"""Dashboard response models.

Real values only. Features that do not exist yet (contests, classrooms)
contribute zeros or empty lists; they are never filled with sample data.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole
from app.schemas.progress import DifficultyProgress, Recommendation


class DashboardUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: UserRole


# ---------------------------------------------------------------- student
class StudentStatistics(BaseModel):
    """See progress_service for the exact definitions."""

    problems_solved: int = 0  # distinct published problems with an ACCEPTED submission
    total_problems: int = 0  # published problems
    attempted_problems: int = 0  # tried but not solved yet
    total_attempts: int = 0  # judged submissions
    accepted_submissions: int = 0
    acceptance_rate: float = 0  # accepted / judged submissions, percentage 0-100
    current_streak: int = 0
    longest_streak: int = 0
    active_today: bool = False
    contest_rating: int | None = None


class TopicProgress(BaseModel):
    slug: str
    topic: str
    solved: int = 0
    total: int = 0
    percent: int = 0


class StudentDashboard(BaseModel):
    user: DashboardUser
    statistics: StudentStatistics
    difficulty: DifficultyProgress
    learning_progress: list[TopicProgress]
    # Rule-based "continue solving" suggestions from real progress.
    continue_learning: list[Recommendation]
    # Calendar days (streaks) are counted in this timezone.
    timezone: str


# ---------------------------------------------------------------- staff
class StaffStatistics(BaseModel):
    students: int = 0
    classrooms: int = 0
    assignments: int = 0
    contests: int = 0


class StaffDashboard(BaseModel):
    user: DashboardUser
    statistics: StaffStatistics


# ---------------------------------------------------------------- admin
ServiceState = Literal["online", "offline", "not_connected"]


class ServiceStatus(BaseModel):
    key: str
    name: str
    status: ServiceState
    detail: str


class AdminDashboard(BaseModel):
    total_users: int
    total_students: int
    total_staff: int
    total_admins: int
    active_users: int
    inactive_users: int
    system_status: list[ServiceStatus]
