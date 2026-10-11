"""Staff / admin analytics responses (aggregated from real submissions).

Classrooms do not exist yet, so the scope is every student account. When
classrooms arrive, the same responses can be filtered to a classroom roster.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.progress import (
    ActivityItem,
    DifficultyProgress,
    Heatmap,
    LanguageStat,
    ProblemRef,
    ProgressOverview,
    StreakInfo,
    TopicProgressItem,
)


class DailyCount(BaseModel):
    date: date
    submissions: int
    accepted: int


class StudentRef(BaseModel):
    id: int
    full_name: str


class TopStudent(StudentRef):
    rank: int
    solved: int
    acceptance_rate: float


AttentionReason = Literal["STUCK", "INACTIVE"]


class AttentionItem(StudentRef):
    reason: AttentionReason
    message: str
    solved: int
    attempts: int
    last_active_at: datetime | None


class ProblemInsight(BaseModel):
    problem: ProblemRef
    attempts: int
    solved_by: int
    acceptance_rate: float | None


class AnalyticsOverview(BaseModel):
    """Platform-wide numbers. "Judged" submissions exclude judge failures."""

    total_students: int
    active_students: int  # judged submission within the last `active_window_days`
    students_with_submissions: int
    problems_solved: int  # (student, published problem) pairs solved
    total_submissions: int
    submissions_today: int
    accepted_submissions: int
    accepted_today: int
    # Mean of per-student acceptance rates (students with >= 1 judged submission).
    average_acceptance_rate: float
    active_window_days: int
    timezone: str
    daily: list[DailyCount]  # last 14 days, oldest first
    top_students: list[TopStudent]
    needs_attention: list[AttentionItem]
    problems: list[ProblemInsight]  # most attempted published problems


class StudentAnalyticsRow(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    solved: int
    attempts: int
    accepted: int
    acceptance_rate: float | None  # None without judged submissions
    last_active_at: datetime | None
    current_streak: int


StudentSort = Literal["solved", "attempts", "acceptance", "last_active", "name"]


class StudentProfileOut(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    joined_at: datetime


class SolvedProblemOut(BaseModel):
    problem: ProblemRef
    solved_at: datetime
    attempts: int
    best_runtime_ms: int | None
    best_memory_kb: int | None


class StudentAnalyticsDetail(BaseModel):
    student: StudentProfileOut
    overview: ProgressOverview
    difficulty: DifficultyProgress
    topics: list[TopicProgressItem]
    languages: list[LanguageStat]
    streak: StreakInfo
    heatmap: Heatmap
    recent_activity: list[ActivityItem]
    solved_problems: list[SolvedProblemOut]
