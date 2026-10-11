"""Registration and login logic."""

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import create_access_token, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenData
from app.schemas.user import UserOut
from app.services import user_service

INVALID_CREDENTIALS = "Invalid email or password."

PORTAL_MISMATCH_MESSAGES = {
    "STUDENT": "This is not a student account. Please use the correct login option.",
    "STAFF": "This is not a staff account. Please use the correct login option.",
    "ADMIN": "You are not authorized to access the admin portal.",
}


def register_student(db: Session, data: RegisterRequest) -> User:
    # Role is decided here on the server; public registration is always STUDENT.
    return user_service.create_user(
        db,
        full_name=data.full_name,
        email=data.email,
        password=data.password,
        role=UserRole.STUDENT,
    )


def authenticate(db: Session, data: LoginRequest) -> User:
    user = user_service.get_user_by_email(db, data.email)

    # verify_password runs even when the user does not exist, to keep timing uniform.
    password_ok = verify_password(data.password, user.password_hash if user else None)
    if not user or not password_ok:
        raise AppError(401, INVALID_CREDENTIALS)

    if not user.is_active:
        raise AppError(403, "Your account has been deactivated. Please contact the administrator.")

    # The role comes from the database record, never from the request.
    if data.portal and user.role.value != data.portal:
        raise AppError(403, PORTAL_MISMATCH_MESSAGES[data.portal])

    return user


def build_token_response(user: User) -> TokenData:
    token, expires_in = create_access_token(user.id, user.role.value)
    return TokenData(
        access_token=token, expires_in=expires_in, user=UserOut.model_validate(user)
    )
