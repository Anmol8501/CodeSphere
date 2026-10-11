from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.tag import Tag
from app.utils.slug import slugify

TAG_EXISTS_MESSAGE = "A tag with this name already exists."


def list_tags(db: Session) -> list[Tag]:
    return list(db.scalars(select(Tag).order_by(Tag.name)).all())


def get_tags_by_ids(db: Session, tag_ids: list[int]) -> list[Tag]:
    if not tag_ids:
        return []
    return list(db.scalars(select(Tag).where(Tag.id.in_(tag_ids))).all())


def find_tag(db: Session, name: str) -> Tag | None:
    slug = slugify(name, max_length=60)
    return db.scalar(select(Tag).where(or_(func.lower(Tag.name) == name.lower(), Tag.slug == slug)))


def create_tag(db: Session, name: str) -> Tag:
    slug = slugify(name, max_length=60)
    if not slug:
        raise AppError(400, "Tag name must contain letters or numbers.")
    if find_tag(db, name):
        raise AppError(409, TAG_EXISTS_MESSAGE)
    tag = Tag(name=name, slug=slug)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, TAG_EXISTS_MESSAGE) from None
    db.refresh(tag)
    return tag
