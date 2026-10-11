"""DSA learning path: ordered topics with real problem counts and progress.

All topics are open for exploration (no prerequisite locking yet). Progress is
solved / published problems, where "solved" means an ACCEPTED submission.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.topic import Topic
from app.models.user import User
from app.schemas.learning import LearningPath, LearningTopic, TopicDetail, TopicProgressStatus
from app.services import progress_service, topic_service

TOPIC_NOT_FOUND = "Topic not found."


def _percent(solved: int, total: int) -> int:
    return round(solved * 100 / total) if total else 0


def _status(solved: int, total: int) -> TopicProgressStatus:
    if total and solved >= total:
        return "COMPLETED"
    return "IN_PROGRESS" if solved else "NOT_STARTED"


def _learning_topic(topic: Topic, total: int, solved: int) -> LearningTopic:
    return LearningTopic(
        **topic_service.to_topic_out(topic, total).model_dump(),
        solved_count=solved,
        progress=_percent(solved, total),
        status=_status(solved, total),
    )


def build_learning_path(db: Session, user: User) -> LearningPath:
    counts = topic_service.published_counts_by_topic(db)
    solved = progress_service.solved_counts_by_topic(db, user.id)
    topics = [
        _learning_topic(t, counts.get(t.id, 0), solved.get(t.id, 0))
        for t in topic_service.list_topics(db)
    ]
    total_problems = sum(t.problem_count for t in topics)
    total_solved = sum(t.solved_count for t in topics)
    return LearningPath(
        topics=topics,
        total_problems=total_problems,
        total_solved=total_solved,
        progress=_percent(total_solved, total_problems),
    )


def get_topic_detail(db: Session, slug: str, user: User) -> TopicDetail:
    topic = topic_service.get_topic_by_slug(db, slug)
    if topic is None:
        raise AppError(404, TOPIC_NOT_FOUND)
    difficulty = topic_service.difficulty_counts(db, topic.id)
    total = difficulty.EASY + difficulty.MEDIUM + difficulty.HARD
    solved = progress_service.solved_counts_by_topic(db, user.id).get(topic.id, 0)
    return TopicDetail(
        **_learning_topic(topic, total, solved).model_dump(),
        difficulty_counts=difficulty,
    )
