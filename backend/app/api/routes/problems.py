"""Problem library for signed-in users. Only published problems are returned."""

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.problem import ProblemDifficulty
from app.models.user import User
from app.schemas.common import ApiResponse, ErrorResponse, Page, ok
from app.schemas.problem import ProblemDetail, ProblemListItem, ProgressFilter
from app.services import problem_service

router = APIRouter(
    prefix="/problems",
    tags=["Problems"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse}},
)


@router.get("", response_model=ApiResponse[Page[ProblemListItem]], summary="Search published problems")
def list_problems(
    search: str | None = Query(default=None, max_length=100, description="Title, slug or tag"),
    difficulty: ProblemDifficulty | None = Query(default=None),
    topic: str | None = Query(default=None, max_length=80, description="Topic slug, e.g. arrays"),
    tags: str | None = Query(default=None, max_length=300, description="Comma-separated tag slugs"),
    status: ProgressFilter | None = Query(default=None, description="Your progress: solved, attempted, unsolved"),
    page: int = Query(default=1, ge=1, le=10_000),
    page_size: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = problem_service.list_published(
        db,
        user=user,
        search=search,
        difficulty=difficulty,
        topic_slug=topic,
        tag_slugs=problem_service.parse_tag_slugs(tags),
        progress=status,
        page=page,
        page_size=page_size,
    )
    return ok("Problems retrieved", data)


@router.get(
    "/{slug}",
    response_model=ApiResponse[ProblemDetail],
    summary="Published problem details (no hidden test cases)",
    responses={404: {"model": ErrorResponse}},
)
def get_problem(
    slug: str = Path(max_length=160),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok("Problem retrieved", problem_service.get_published_detail(db, slug=slug, user=user))
