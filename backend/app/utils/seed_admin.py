"""Create the development admin account from ADMIN_* environment variables.

Usage (from the backend/ folder):
    python -m app.utils.seed_admin
    python -m app.utils.seed_admin --reset-password   # sync password with .env
"""

from app.core.config import settings
from app.models.user import UserRole
from app.utils.seed import run, seed_account, wants_password_reset

if __name__ == "__main__":
    run(
        seed_account(
            role=UserRole.ADMIN,
            full_name=settings.ADMIN_NAME,
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            env_prefix="ADMIN",
            reset_password=wants_password_reset(),
        )
    )
