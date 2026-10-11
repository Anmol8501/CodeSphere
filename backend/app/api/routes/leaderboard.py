"""Global leaderboard (any signed-in user). Public ranking fields only."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ErrorResponse, ok
from app.schemas.leaderboard import LeaderboardPage, LeaderboardScope
from app.services import leaderboard_service

router = APIRouter(
    prefix="/leaderboard",
    tags=["Leaderboard"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse}},
)


@router.get("", response_model=ApiResponse[LeaderboardPage], summary="Students ranked by problems solved")
def get_leaderboard(
    scope: LeaderboardScope = Query(default="global"),
    page: int = Query(default=1, ge=1, le=10_000),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok("Leaderboard", leaderboard_service.leaderboard(db, user, page=page, limit=limit))
