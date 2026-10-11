"""Staff / admin analytics. Every route requires STAFF or ADMIN (checked server-side).

Classrooms do not exist yet, so staff can see aggregated progress for every
student. Submission source code is not exposed here.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_staff_or_admin
from app.db.session import get_db
from app.schemas.analytics import AnalyticsOverview, StudentAnalyticsDetail, StudentAnalyticsRow, StudentSort
from app.schemas.common import ApiResponse, ErrorResponse, Page, ok
from app.services import analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(require_staff_or_admin)],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)


@router.get("/overview", response_model=ApiResponse[AnalyticsOverview], summary="Platform-wide student activity")
def get_overview(db: Session = Depends(get_db)):
    return ok("Analytics overview", analytics_service.overview(db))


@router.get("/students", response_model=ApiResponse[Page[StudentAnalyticsRow]], summary="Students with their progress")
def list_students(
    search: str | None = Query(default=None, max_length=100, description="Name or email"),
    sort: StudentSort = Query(default="solved"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1, le=10_000),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    data = analytics_service.students(db, search=search, sort=sort, descending=order == "desc", page=page, limit=limit)
    return ok("Students retrieved", data)


@router.get(
    "/students/{student_id}",
    response_model=ApiResponse[StudentAnalyticsDetail],
    summary="One student's progress",
    responses={404: {"model": ErrorResponse}},
)
def get_student(student_id: Annotated[int, Path(ge=1, le=2_147_483_647)], db: Session = Depends(get_db)):
    return ok("Student progress", analytics_service.student_detail(db, student_id))
