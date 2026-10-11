"""Coding workspace: the student's own drafts, RUN, SUBMIT and submission history.

Every route requires a STUDENT. The user is always taken from the JWT; no
request field can select another user's data.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_student
from app.db.session import get_db
from app.models.problem import ProgrammingLanguage
from app.models.submission import SubmissionStatus
from app.models.user import User
from app.schemas.common import ApiResponse, ErrorResponse, Page, ResponsesDict, ok
from app.schemas.workspace import (
    DraftOut,
    DraftSave,
    DraftSaveResult,
    RunRequest,
    RunResult,
    SubmissionDetail,
    SubmissionSummary,
    SubmitRequest,
)
from app.services import draft_service, execution_service, submission_service
from app.services.submission_service import Period

ProblemId = Annotated[int, Path(ge=1, le=2_147_483_647)]

ERRORS: ResponsesDict = {401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}

drafts_router = APIRouter(prefix="/problems", tags=["Workspace"], dependencies=[Depends(require_student)], responses=ERRORS)
executions_router = APIRouter(
    prefix="/executions", tags=["Execution"], dependencies=[Depends(require_student)], responses=ERRORS
)
submissions_router = APIRouter(
    prefix="/submissions", tags=["Submissions"], dependencies=[Depends(require_student)], responses=ERRORS
)


@drafts_router.get(
    "/{problem_id}/draft",
    response_model=ApiResponse[DraftOut | None],
    summary="Your saved draft for this problem and language (data is null if none)",
)
def get_draft(
    problem_id: ProblemId,
    language: ProgrammingLanguage = Query(),
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    draft = draft_service.get_draft(db, user, problem_id, language)
    return ok("Draft retrieved" if draft else "No saved draft", DraftOut.model_validate(draft) if draft else None)


@drafts_router.put(
    "/{problem_id}/draft",
    response_model=ApiResponse[DraftSaveResult],
    summary="Save (upsert) your draft. 409 if another tab saved a newer version.",
    responses={409: {"model": ErrorResponse}},
)
def save_draft(
    problem_id: ProblemId,
    data: DraftSave,
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    draft = draft_service.save_draft(db, user, problem_id, data)
    return ok("Draft saved", DraftSaveResult(version=draft.version, updated_at=draft.updated_at))


@executions_router.post(
    "/run",
    response_model=ApiResponse[RunResult],
    summary="Run code on the public tests (+ your custom cases) through Judge0. Not stored.",
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 413: {"model": ErrorResponse},
               429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def run_code(data: RunRequest, user: User = Depends(require_student), db: Session = Depends(get_db)):
    result = execution_service.run(db, user, data)
    return ok("Run finished", result)


@submissions_router.post(
    "",
    response_model=ApiResponse[SubmissionDetail],
    summary="Submit for judging on public + hidden tests. The verdict is decided by the server.",
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 413: {"model": ErrorResponse},
               429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def submit_code(data: SubmitRequest, user: User = Depends(require_student), db: Session = Depends(get_db)):
    submission = execution_service.submit(db, user, data)
    submission = submission_service.get_for_user(db, user, submission.id)
    return ok("Submission judged", submission_service.to_detail(db, submission))


MAX_PAGE_SIZE = 100


@submissions_router.get("", response_model=ApiResponse[Page[SubmissionSummary]], summary="Your submission history")
def list_submissions(
    problem: str | None = Query(default=None, max_length=160, description="Problem slug"),
    problem_id: int | None = Query(default=None, ge=1, le=2_147_483_647),
    problem_id_alias: int | None = Query(default=None, alias="problemId", ge=1, le=2_147_483_647, include_in_schema=False),
    language: ProgrammingLanguage | None = Query(default=None),
    status: SubmissionStatus | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100, description="Problem title or slug"),
    period: Period = Query(default="all", description="today, 7d, 30d or all (calendar days in APP_TIMEZONE)"),
    page: int = Query(default=1, ge=1, le=10_000),
    limit: int | None = Query(default=None, ge=1, le=MAX_PAGE_SIZE, description="Page size (max 100)"),
    page_size: int | None = Query(default=None, ge=1, le=MAX_PAGE_SIZE, include_in_schema=False),
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    execution_service.expire_stuck_submissions(db)
    data = submission_service.list_for_user(
        db,
        user,
        problem_slug=problem,
        problem_id=problem_id or problem_id_alias,
        language=language,
        status=status,
        search=search,
        period=period,
        page=page,
        limit=limit or page_size or 20,
    )
    return ok("Submissions retrieved", data)


@submissions_router.get("/{submission_id}", response_model=ApiResponse[SubmissionDetail], summary="One of your submissions")
def get_submission(
    submission_id: Annotated[int, Path(ge=1, le=2_147_483_647)],
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    submission = submission_service.get_for_user(db, user, submission_id)
    return ok("Submission retrieved", submission_service.to_detail(db, submission))
