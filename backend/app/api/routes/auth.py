from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenData
from app.schemas.common import ApiResponse, ErrorResponse, ResponsesDict, ok
from app.schemas.user import UserOut
from app.services import auth_service
from app.utils.rate_limiter import login_rate_limiter, register_rate_limiter

router = APIRouter(prefix="/auth", tags=["Auth"])

_errors: ResponsesDict = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
}


@router.post(
    "/register",
    response_model=ApiResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
    description="Public registration. The account is always created with role STUDENT.",
    responses={409: {"model": ErrorResponse}, **_errors},
    dependencies=[Depends(register_rate_limiter)],
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register_student(db, data)
    return ok("Account created successfully. You can now login.", UserOut.model_validate(user))


@router.post(
    "/login",
    response_model=ApiResponse[TokenData],
    summary="Login with email and password",
    description=(
        "Returns a JWT access token. `portal` is optional; when given, the server "
        "checks it against the user's real role stored in the database."
    ),
    responses=_errors,
    dependencies=[Depends(login_rate_limiter)],
)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, data)
    return ok("Login successful", auth_service.build_token_response(user))


@router.get(
    "/me",
    response_model=ApiResponse[UserOut],
    summary="Get the currently authenticated user",
    responses=_errors,
)
def me(user: User = Depends(get_current_user)):
    return ok("Current user", UserOut.model_validate(user))


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    summary="Logout",
    description=(
        "Access tokens are stateless JWTs, so logout is completed by the client "
        "discarding its token. This endpoint confirms the token was valid."
    ),
    responses=_errors,
)
def logout(_: User = Depends(get_current_user)):
    return ok("Logged out successfully")
