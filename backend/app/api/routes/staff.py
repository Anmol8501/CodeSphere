from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_staff
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ErrorResponse, ok
from app.schemas.dashboard import StaffDashboard
from app.services import dashboard_service

router = APIRouter(
    prefix="/staff",
    tags=["Staff"],
    # Every route here requires STAFF, even ones added later.
    dependencies=[Depends(require_staff)],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)


@router.get(
    "/dashboard",
    response_model=ApiResponse[StaffDashboard],
    summary="Staff dashboard: profile and teaching statistics",
)
def staff_dashboard(user: User = Depends(require_staff), db: Session = Depends(get_db)):
    return ok("Staff dashboard", dashboard_service.build_staff_dashboard(db, user))
