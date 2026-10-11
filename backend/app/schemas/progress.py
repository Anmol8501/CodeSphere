"""Progress, statistics and activity responses (all computed by the server).

There is no input model in this file: students can only READ their progress.
Solved state, attempts, acceptance rate, streaks and leaderboard values are
derived from judged submissions and never accepted from a client.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.models.problem import ProblemDifficulty, ProgrammingLanguage
from app.models.submission import SubmissionStatus
from app.schemas.problem import TopicRef


class ProgressOverview(BaseModel):
    total_problems: int  # published problems
    solved_problems: int  # published problems with an ACCEPTED submission
    attempted_problems: int  # published problems tried but not solved yet
    total_submissions: int  # judged submissions (= attempts)
    accepted_submissions: int
    acceptance_rate: float  # accepted / judged submissions * 100 (0 with no submissions)


class DifficultyCount(BaseModel):
    total: int
    solved: int
    percentage: float


class DifficultyProgress(BaseModel):
    easy: DifficultyCount
    medium: DifficultyCount
    hard: DifficultyCount


class TopicProgressItem(BaseModel):
    topic: TopicRef
    total_problems: int
    solved_problems: int
    attempted_problems: int
    percentage: float


class LanguageStat(BaseModel):
    language: ProgrammingLanguage
    submissions: int
    accepted: int
    acceptance_rate: float | None  # None when there are no submissions in this language
    solved_problems: int


class StreakInfo(BaseModel):
    current_streak: int
    longest_streak: int
    active_today: bool
    last_active_date: date | None
    # Coding days in the last 365 days, oldest first.
    activity_dates: list[date]
    timezone: str


class HeatmapDay(BaseModel):
    date: date
    submission_count: int


class Heatmap(BaseModel):
    start_date: date
    end_date: date
    timezone: str
    total_submissions: int
    active_days: int
    # Every day from start_date to end_date (inclusive), zeros included.
    days: list[HeatmapDay]


class ProblemRef(BaseModel):
    id: int
    slug: str
    title: str
    difficulty: ProblemDifficulty


ActivityType = Literal["SOLVED", "ACCEPTED", "ATTEMPTED"]


class ActivityItem(BaseModel):
    """One judged submission. SOLVED = first accepted, ACCEPTED = accepted again."""

    submission_id: int
    type: ActivityType
    verdict: SubmissionStatus
    language: ProgrammingLanguage
    problem: ProblemRef
    occurred_at: datetime


RecommendationReason = Literal["RESUME", "CONTINUE_TOPIC", "START_TOPIC"]


class RecommendedProblem(ProblemRef):
    topic: TopicRef


class Recommendation(BaseModel):
    problem: RecommendedProblem
    reason: RecommendationReason
    message: str
