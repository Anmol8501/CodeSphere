"""Admin problem management: problems, publishing, tags and test cases."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.problem import ProblemDifficulty, ProblemStatus
from app.models.user import User
from app.schemas.admin_problem import (
    AdminProblemDetail,
    AdminProblemListItem,
    ProblemCreate,
    ProblemUpdate,
    PublishUpdate,
    TagCreate,
    TestCaseIn,
    TestCaseOut,
)
from app.schemas.common import ApiResponse, ErrorResponse, Page, ResponsesDict, ok
from app.schemas.problem import TagOut
from app.services import admin_problem_service as service
from app.services import problem_service, tag_service

# Every route in this router requires an authenticated ADMIN (staff get 403).
router = APIRouter(
    prefix="/admin",
    tags=["Admin · Problems"],
    dependencies=[Depends(require_admin)],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)

NOT_FOUND: ResponsesDict = {404: {"model": ErrorResponse}}
# Bounded so an out-of-range id is a clean 422, not a database integer overflow.
IdPath = Annotated[int, Path(ge=1, le=2_147_483_647)]


@router.get("/problems", response_model=ApiResponse[Page[AdminProblemListItem]], summary="List all problems")
def list_problems(
    search: str | None = Query(default=None, max_length=100),
    difficulty: ProblemDifficulty | None = Query(default=None),
    topic: str | None = Query(default=None, max_length=80, description="Topic slug"),
    tags: str | None = Query(default=None, max_length=300, description="Comma-separated tag slugs"),
    status_filter: ProblemStatus | None = Query(default=None, alias="status"),
    published: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1, le=10_000),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    data = service.list_problems(
        db,
        search=search,
        difficulty=difficulty,
        topic_slug=topic,
        tag_slugs=problem_service.parse_tag_slugs(tags),
        status=status_filter,
        published=published,
        page=page,
        page_size=page_size,
    )
    return ok("Problems retrieved", data)


@router.get("/problems/{problem_id}", response_model=ApiResponse[AdminProblemDetail], responses=NOT_FOUND)
def get_problem(problem_id: IdPath, db: Session = Depends(get_db)):
    problem = service.get_problem_or_404(db, problem_id)
    return ok("Problem retrieved", service.to_detail(db, problem))


@router.post(
    "/problems",
    response_model=ApiResponse[AdminProblemDetail],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_problem(data: ProblemCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    problem = service.create_problem(db, data, admin)
    return ok("Problem created", service.to_detail(db, problem))


@router.put(
    "/problems/{problem_id}",
    response_model=ApiResponse[AdminProblemDetail],
    responses={**NOT_FOUND, 400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_problem(problem_id: IdPath, data: ProblemUpdate, db: Session = Depends(get_db)):
    problem = service.update_problem(db, service.get_problem_or_404(db, problem_id), data)
    return ok("Problem updated", service.to_detail(db, problem))


@router.patch(
    "/problems/{problem_id}/publish",
    response_model=ApiResponse[AdminProblemDetail],
    summary="Publish or unpublish (unpublish moves the problem to DRAFT)",
    responses=NOT_FOUND,
)
def publish_problem(problem_id: IdPath, data: PublishUpdate, db: Session = Depends(get_db)):
    problem = service.set_published(db, service.get_problem_or_404(db, problem_id), data.is_published)
    return ok("Problem published" if data.is_published else "Problem unpublished", service.to_detail(db, problem))


@router.delete(
    "/problems/{problem_id}",
    response_model=ApiResponse[AdminProblemDetail],
    summary="Archive a problem (soft delete; hidden from students)",
    responses=NOT_FOUND,
)
def archive_problem(problem_id: IdPath, db: Session = Depends(get_db)):
    problem = service.archive_problem(db, service.get_problem_or_404(db, problem_id))
    return ok("Problem archived", service.to_detail(db, problem))


# ------------------------------------------------------------------ test cases
@router.get("/problems/{problem_id}/test-cases", response_model=ApiResponse[list[TestCaseOut]], responses=NOT_FOUND)
def list_test_cases(problem_id: IdPath, db: Session = Depends(get_db)):
    problem = service.get_problem_or_404(db, problem_id)
    return ok("Test cases retrieved", [TestCaseOut.model_validate(tc) for tc in service.list_test_cases(db, problem)])


@router.post(
    "/problems/{problem_id}/test-cases",
    response_model=ApiResponse[TestCaseOut],
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def add_test_case(problem_id: IdPath, data: TestCaseIn, db: Session = Depends(get_db)):
    test_case = service.add_test_case(db, service.get_problem_or_404(db, problem_id), data)
    return ok("Test case created", TestCaseOut.model_validate(test_case))


@router.put("/test-cases/{test_case_id}", response_model=ApiResponse[TestCaseOut], responses=NOT_FOUND)
def update_test_case(test_case_id: IdPath, data: TestCaseIn, db: Session = Depends(get_db)):
    test_case = service.update_test_case(db, service.get_test_case_or_404(db, test_case_id), data)
    return ok("Test case updated", TestCaseOut.model_validate(test_case))


@router.delete("/test-cases/{test_case_id}", response_model=ApiResponse[None], responses=NOT_FOUND)
def delete_test_case(test_case_id: IdPath, db: Session = Depends(get_db)):
    service.delete_test_case(db, service.get_test_case_or_404(db, test_case_id))
    return ok("Test case deleted")


# ------------------------------------------------------------------ tags
@router.post(
    "/tags",
    response_model=ApiResponse[TagOut],
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_tag(data: TagCreate, db: Session = Depends(get_db)):
    return ok("Tag created", TagOut.model_validate(tag_service.create_tag(db, data.name)))
