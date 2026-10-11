from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_student
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ErrorResponse, ok
from app.schemas.dashboard import StudentDashboard
from app.services import dashboard_service

router = APIRouter(
    prefix="/student",
    tags=["Student"],
    # Every route here requires a STUDENT, even ones added later.
    dependencies=[Depends(require_student)],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)


@router.get(
    "/dashboard",
    response_model=ApiResponse[StudentDashboard],
    summary="Student dashboard: profile, statistics, learning progress, activity",
)
def student_dashboard(user: User = Depends(require_student), db: Session = Depends(get_db)):
    return ok("Student dashboard", dashboard_service.build_student_dashboard(db, user))
