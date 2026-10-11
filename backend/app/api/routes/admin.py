from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.common import ApiResponse, ErrorResponse, ok
from app.schemas.dashboard import AdminDashboard
from app.schemas.user import (
    AdminStats,
    StaffCreateRequest,
    UserListData,
    UserOut,
    UserStatusUpdate,
)
from app.services import dashboard_service, problem_service, user_service

# Every route in this router requires an authenticated ADMIN.
router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)


@router.get("/stats", response_model=ApiResponse[AdminStats], summary="Platform statistics")
def get_stats(db: Session = Depends(get_db)):
    stats = AdminStats(
        total_students=user_service.count_users(db, role=UserRole.STUDENT),
        total_staff=user_service.count_users(db, role=UserRole.STAFF),
        total_admins=user_service.count_users(db, role=UserRole.ADMIN),
        total_problems=problem_service.count_published(db),
        active_users=user_service.count_users(db, active_only=True),
    )
    return ok("Admin statistics", stats)


@router.get(
    "/dashboard",
    response_model=ApiResponse[AdminDashboard],
    summary="Admin dashboard: real user counts and system status",
)
def get_dashboard(db: Session = Depends(get_db)):
    return ok("Admin dashboard", dashboard_service.build_admin_dashboard(db))


@router.get("/users", response_model=ApiResponse[UserListData], summary="List users")
def list_users(
    role: UserRole | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None, description="Filter by status (true = active)"),
    search: str | None = Query(default=None, max_length=100, description="Search name or email"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    users, total = user_service.list_users(
        db, role=role, is_active=is_active, search=search, page=page, page_size=page_size
    )
    data = UserListData(
        items=[UserOut.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )
    return ok("Users retrieved", data)


@router.patch(
    "/users/{user_id}/status",
    response_model=ApiResponse[UserOut],
    summary="Activate or deactivate a user",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    target = user_service.get_user_by_id(db, user_id)
    if target is None:
        raise AppError(404, "User not found.")
    updated = user_service.set_user_active(
        db, target=target, is_active=data.is_active, acting_user=admin
    )
    action = "activated" if updated.is_active else "deactivated"
    return ok(f"User {action} successfully", UserOut.model_validate(updated))


@router.post(
    "/staff",
    response_model=ApiResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create a staff account",
    responses={409: {"model": ErrorResponse}},
)
def create_staff(data: StaffCreateRequest, db: Session = Depends(get_db)):
    user = user_service.create_user(
        db,
        full_name=data.full_name,
        email=data.email,
        password=data.password,
        role=UserRole.STAFF,
    )
    return ok("Staff account created successfully", UserOut.model_validate(user))
