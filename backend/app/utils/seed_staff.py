"""Create the development staff account from STAFF_* environment variables.

Usage (from the backend/ folder):
    python -m app.utils.seed_staff
    python -m app.utils.seed_staff --reset-password   # sync password with .env
"""

from app.core.config import settings
from app.models.user import UserRole
from app.utils.seed import run, seed_account, wants_password_reset

if __name__ == "__main__":
    run(
        seed_account(
            role=UserRole.STAFF,
            full_name=settings.STAFF_NAME,
            email=settings.STAFF_EMAIL,
            password=settings.STAFF_PASSWORD,
            env_prefix="STAFF",
            reset_password=wants_password_reset(),
        )
    )
