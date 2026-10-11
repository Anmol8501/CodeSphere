"""Password hashing (bcrypt) and JWT helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# bcrypt only uses the first 72 bytes of a password; schemas enforce this limit.
BCRYPT_MAX_BYTES = 72

# Used so a login for an unknown email takes about as long as a wrong password.
_DUMMY_HASH = bcrypt.hashpw(b"codearena-timing-dummy", bcrypt.gensalt(settings.BCRYPT_ROUNDS)).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(settings.BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), (password_hash or _DUMMY_HASH).encode("utf-8")
        )
    except ValueError:
        return False


def create_access_token(subject: str | int, role: str) -> tuple[str, int]:
    """Return (token, expires_in_seconds)."""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        # Informational only: the backend always re-reads the role from the database.
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + expires_delta,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a token.

    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Wrong token type")
    return payload
