"""Authentication & role-based authorization dependencies.

Usage in a route:
    @router.get("/thing")
    def thing(user: User = Depends(require_admin)): ...

The role is always read from the database record of the authenticated user,
never from the request body or the frontend.
"""

from collections.abc import Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services import user_service

bearer_scheme = HTTPBearer(auto_error=False, description="Paste the access_token from /api/auth/login")

_AUTH_HEADERS = {"WWW-Authenticate": "Bearer"}


def _unauthorized(message: str) -> AppError:
    return AppError(401, message, headers=_AUTH_HEADERS)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Not authenticated. Please login.")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Your session has expired. Please login again.") from None
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise _unauthorized("Invalid authentication token. Please login again.") from None

    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise _unauthorized("Invalid authentication token. Please login again.")
    if not user.is_active:
        raise _unauthorized("Your account has been deactivated. Please contact the administrator.")
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    """Build a dependency that only lets users with one of `roles` through."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppError(403, "You are not authorized to access this resource.")
        return user

    return dependency


require_student = require_roles(UserRole.STUDENT)
require_staff = require_roles(UserRole.STAFF)
require_admin = require_roles(UserRole.ADMIN)
require_staff_or_admin = require_roles(UserRole.STAFF, UserRole.ADMIN)
