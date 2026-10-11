"""Database operations for users. Routes call these instead of querying directly."""

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.models.user import User, UserRole

EMAIL_TAKEN_MESSAGE = "An account with this email already exists."


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def create_user(
    db: Session, *, full_name: str, email: str, password: str, role: UserRole
) -> User:
    """Create a user with a hashed password. Raises 409 if the email is taken."""
    if get_user_by_email(db, email):
        raise AppError(409, EMAIL_TAKEN_MESSAGE)

    user = User(
        full_name=full_name,
        email=normalize_email(email),
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two requests raced for the same email; the unique index caught it.
        db.rollback()
        raise AppError(409, EMAIL_TAKEN_MESSAGE) from None
    db.refresh(user)
    return user


def list_users(
    db: Session,
    *,
    role: UserRole | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[User], int]:
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active.is_(is_active))
    if search and search.strip():
        # Escape LIKE wildcards so a search for "a_b" matches literally.
        term = search.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{term}%"
        query = query.where(
            or_(
                func.lower(User.full_name).like(pattern, escape="\\"),
                User.email.like(pattern, escape="\\"),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    users = db.scalars(
        query.order_by(User.created_at.desc(), User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(users), total


def count_users(db: Session, *, role: UserRole | None = None, active_only: bool = False) -> int:
    query = select(func.count(User.id))
    if role:
        query = query.where(User.role == role)
    if active_only:
        query = query.where(User.is_active.is_(True))
    return db.scalar(query) or 0


def set_user_active(db: Session, *, target: User, is_active: bool, acting_user: User) -> User:
    """Activate/deactivate a user, protecting the platform from losing all admins."""
    if not is_active:
        if target.id == acting_user.id:
            raise AppError(400, "You cannot deactivate your own account.")
        if target.role == UserRole.ADMIN and target.is_active:
            if count_users(db, role=UserRole.ADMIN, active_only=True) <= 1:
                raise AppError(400, "You cannot deactivate the last active admin account.")

    target.is_active = is_active
    db.commit()
    db.refresh(target)
    return target
