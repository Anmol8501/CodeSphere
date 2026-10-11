"""Topic queries. Topics are the ordered steps of the learning path."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.problem import Problem, ProblemStatus
from app.models.topic import Topic
from app.schemas.learning import DifficultyCounts, TopicOut


def list_topics(db: Session, *, top_level_only: bool = True) -> list[Topic]:
    """Active topics in learning-path order (order_index ASC)."""
    query = select(Topic).where(Topic.is_active.is_(True))
    if top_level_only:
        query = query.where(Topic.parent_topic_id.is_(None))
    return list(db.scalars(query.order_by(Topic.order_index, Topic.id)).all())


def get_topic_by_slug(db: Session, slug: str) -> Topic | None:
    return db.scalar(select(Topic).where(Topic.slug == slug, Topic.is_active.is_(True)))


def get_topic(db: Session, topic_id: int) -> Topic | None:
    return db.get(Topic, topic_id)


def published_counts_by_topic(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(Problem.topic_id, func.count(Problem.id))
        .where(Problem.status == ProblemStatus.PUBLISHED)
        .group_by(Problem.topic_id)
    ).all()
    return dict(rows)


def difficulty_counts(db: Session, topic_id: int) -> DifficultyCounts:
    rows = db.execute(
        select(Problem.difficulty, func.count(Problem.id))
        .where(Problem.topic_id == topic_id, Problem.status == ProblemStatus.PUBLISHED)
        .group_by(Problem.difficulty)
    ).all()
    return DifficultyCounts(**{difficulty.value: count for difficulty, count in rows})


def to_topic_out(topic: Topic, problem_count: int) -> TopicOut:
    return TopicOut.model_validate(topic).model_copy(update={"problem_count": problem_count})


def create_topic(
    db: Session,
    *,
    name: str,
    slug: str,
    order_index: int,
    description: str = "",
    icon: str | None = None,
    learning_outcomes: list[str] | None = None,
    parent_topic_id: int | None = None,
) -> Topic:
    topic = Topic(
        name=name,
        slug=slug,
        order_index=order_index,
        description=description,
        icon=icon,
        learning_outcomes=learning_outcomes or [],
        parent_topic_id=parent_topic_id,
        is_active=True,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic
