"""Shared logic for the development seed scripts (seed_admin / seed_staff).

Credentials come only from environment variables (backend/.env).
Passwords are hashed and never printed.

Pass --reset-password to update an existing account's password (and re-activate
it) so it matches the current value in backend/.env.
"""

import sys

from pydantic import BaseModel, EmailStr, ValidationError, field_validator

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import UserRole
from app.schemas.validators import validate_full_name, validate_password_strength
from app.services import user_service


class _SeedAccount(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("full_name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        return validate_full_name(value)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


def wants_password_reset() -> bool:
    return "--reset-password" in sys.argv[1:]


def seed_account(
    *,
    role: UserRole,
    full_name: str,
    email: str | None,
    password: str | None,
    env_prefix: str,
    reset_password: bool = False,
) -> int:
    """Create the account if it does not exist. Returns a process exit code."""
    if not email or not password:
        print(f"[seed] {env_prefix}_EMAIL and {env_prefix}_PASSWORD must be set in backend/.env")
        return 1

    try:
        account = _SeedAccount(full_name=full_name, email=email, password=password)
    except ValidationError as exc:
        for err in exc.errors():
            field = err["loc"][-1] if err["loc"] else "value"
            print(f"[seed] Invalid {env_prefix} {field}: {err['msg'].removeprefix('Value error, ')}")
        return 1

    with SessionLocal() as db:
        existing = user_service.get_user_by_email(db, account.email)
        if existing:
            if existing.role == role:
                if reset_password:
                    existing.password_hash = hash_password(account.password)
                    existing.is_active = True
                    db.commit()
                    print(f"[seed] Password for {role.value} account {existing.email} reset from .env.")
                else:
                    print(
                        f"[seed] {role.value} account {existing.email} already exists. Nothing to do. "
                        "(Run with --reset-password to sync its password with .env.)"
                    )
                return 0
            print(
                f"[seed] {existing.email} already exists with role {existing.role.value}. "
                "Refusing to change it; choose a different email."
            )
            return 1

        user = user_service.create_user(
            db,
            full_name=account.full_name,
            email=account.email,
            password=account.password,
            role=role,
        )
        print(f"[seed] Created {role.value} account: {user.email} (id={user.id})")
        return 0


def run(exit_code: int) -> None:
    sys.exit(exit_code)
