"""The signed-in student's own progress. Read-only: there is no write endpoint.

Every value is computed by the server from judged submissions. The student
always comes from the JWT; no parameter can select another user.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_student
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ErrorResponse, ok
from app.schemas.progress import (
    ActivityItem,
    DifficultyProgress,
    Heatmap,
    LanguageStat,
    ProgressOverview,
    StreakInfo,
    TopicProgressItem,
)
from app.services import progress_service

router = APIRouter(
    prefix="/progress",
    tags=["Progress"],
    dependencies=[Depends(require_student)],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)


@router.get("/overview", response_model=ApiResponse[ProgressOverview], summary="Solved, attempted and submission totals")
def get_overview(user: User = Depends(require_student), db: Session = Depends(get_db)):
    return ok("Progress overview", progress_service.overview(db, user.id))


@router.get("/topics", response_model=ApiResponse[list[TopicProgressItem]], summary="Solved / total per topic")
def get_topics(user: User = Depends(require_student), db: Session = Depends(get_db)):
    return ok("Topic progress", progress_service.topic_progress(db, user.id))


@router.get("/difficulty", response_model=ApiResponse[DifficultyProgress], summary="Solved / total per difficulty")
def get_difficulty(user: User = Depends(require_student), db: Session = Depends(get_db)):
    return ok("Difficulty progress", progress_service.difficulty_progress(db, user.id))


@router.get("/languages", response_model=ApiResponse[list[LanguageStat]], summary="Submissions and acceptance per language")
def get_languages(user: User = Depends(require_student), db: Session = Depends(get_db)):
    return ok("Language statistics", progress_service.language_stats(db, user.id))


@router.get("/activity", response_model=ApiResponse[list[ActivityItem]], summary="Recent judged submissions, newest first")
def get_activity(
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return ok("Recent activity", progress_service.activity(db, user.id, limit=limit))


@router.get("/streak", response_model=ApiResponse[StreakInfo], summary="Current and longest coding streak")
def get_streak(user: User = Depends(require_student), db: Session = Depends(get_db)):
    return ok("Coding streak", progress_service.streak(db, user.id))


@router.get("/heatmap", response_model=ApiResponse[Heatmap], summary="Judged submissions per day (grouped in SQL)")
def get_heatmap(
    days: int = Query(default=365, ge=7, le=371, description="Days up to and including today"),
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return ok("Submission heatmap", progress_service.heatmap(db, user.id, days=days))
