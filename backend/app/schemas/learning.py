"""Topic and learning-path schemas. Progress values come from submissions only."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

TopicProgressStatus = Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED"]


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str
    order_index: int
    icon: str | None = None
    parent_topic_id: int | None = None
    learning_outcomes: list[str]
    problem_count: int = 0  # published problems only


class DifficultyCounts(BaseModel):
    EASY: int = 0
    MEDIUM: int = 0
    HARD: int = 0


class LearningTopic(TopicOut):
    solved_count: int = 0
    progress: int = 0  # percent 0–100
    status: TopicProgressStatus = "NOT_STARTED"


class TopicDetail(LearningTopic):
    difficulty_counts: DifficultyCounts


class LearningPath(BaseModel):
    topics: list[LearningTopic]
    total_problems: int
    total_solved: int
    progress: int
