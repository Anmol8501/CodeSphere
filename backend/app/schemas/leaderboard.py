"""Leaderboard responses: public ranking fields only (no email, no ids of others)."""

from typing import Literal

from pydantic import BaseModel

from app.schemas.common import Page

LeaderboardScope = Literal["global"]  # classroom boards arrive with classrooms


class LeaderboardEntry(BaseModel):
    rank: int
    name: str
    solved: int
    acceptance_rate: float
    is_current_user: bool = False


class LeaderboardPage(Page[LeaderboardEntry]):
    scope: LeaderboardScope = "global"
    # The signed-in student's own row (None when not ranked yet).
    current_user: LeaderboardEntry | None = None
    ranking_rule: str
