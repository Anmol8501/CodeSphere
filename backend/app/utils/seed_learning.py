"""Seed the learning path: topics, tags and the starter problem set.

Usage (from the backend/ folder, after `alembic upgrade head`):
    python -m app.utils.seed_learning

Idempotent: every row is looked up by slug first (get-or-create), so running
it again creates nothing new and never overwrites edits made by an admin.
Seed problems go through the same validation and service as the admin API.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.problem import Problem
from app.models.tag import Tag
from app.models.topic import Topic
from app.models.user import User, UserRole
from app.schemas.admin_problem import ProblemCreate
from app.seed_data.problems import PROBLEMS
from app.seed_data.tags import TAGS
from app.seed_data.topics import TOPICS
from app.services import admin_problem_service, topic_service, user_service
from app.utils.slug import slugify


def _author(db: Session) -> User | None:
    if settings.ADMIN_EMAIL:
        admin = user_service.get_user_by_email(db, settings.ADMIN_EMAIL)
        if admin and admin.role == UserRole.ADMIN:
            return admin
    return db.scalar(select(User).where(User.role == UserRole.ADMIN).order_by(User.id))


def seed_topics(db: Session) -> tuple[dict[str, Topic], int]:
    created = 0
    for order, data in enumerate(TOPICS, start=1):
        if db.scalar(select(Topic).where(Topic.slug == data["slug"])) is None:
            topic_service.create_topic(db, order_index=order, **data)
            created += 1
    topics = {t.slug: t for t in db.scalars(select(Topic)).all()}
    return topics, created


def seed_tags(db: Session) -> tuple[dict[str, Tag], int]:
    created = 0
    for name in TAGS:
        slug = slugify(name, max_length=60)
        if db.scalar(select(Tag).where(Tag.slug == slug)) is None:
            db.add(Tag(name=name, slug=slug))
            created += 1
    db.commit()
    tags = {t.name: t for t in db.scalars(select(Tag)).all()}
    return tags, created


def seed_problems(db: Session, topics: dict[str, Topic], tags: dict[str, Tag]) -> int:
    author = _author(db)
    created = 0
    for data in PROBLEMS:
        if db.scalar(select(Problem.id).where(Problem.slug == data["slug"])) is not None:
            continue  # never overwrite an existing (possibly admin-edited) problem
        payload = ProblemCreate(
            title=data["title"],
            slug=data["slug"],
            description=data["description"],
            difficulty=data["difficulty"],
            topic_id=topics[data["topic"]].id,
            tag_ids=[tags[name].id for name in data["tags"]],
            constraints=data["constraints"],
            input_format=data["input_format"],
            output_format=data["output_format"],
            examples=data["examples"],
            starter_codes=[
                {"language": lang, "starter_code": code, "driver_code": (data.get("driver") or {}).get(lang)}
                for lang, code in data["starter"].items()
            ],
            test_cases=data["test_cases"],
            is_published=True,
        )
        admin_problem_service.create_problem(db, payload, author)
        created += 1
    return created


def seed_learning(db: Session) -> dict[str, int]:
    topics, topics_created = seed_topics(db)
    tags, tags_created = seed_tags(db)
    problems_created = seed_problems(db, topics, tags)
    return {"topics": topics_created, "tags": tags_created, "problems": problems_created}


def main() -> int:
    with SessionLocal() as db:
        result = seed_learning(db)
    print(
        f"[seed] Learning path: {result['topics']} topics, {result['tags']} tags, "
        f"{result['problems']} problems created (existing rows left unchanged)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
