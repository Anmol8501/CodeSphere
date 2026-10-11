"""Import every model here so Alembic's autogenerate can discover them."""

from app.models.draft import CodeDraft
from app.models.problem import (
    Problem,
    ProblemDifficulty,
    ProblemExample,
    ProblemStatus,
    ProgrammingLanguage,
    StarterCode,
    TestCase,
)
from app.models.progress import UserProblemProgress
from app.models.submission import Submission, SubmissionStatus, SubmissionTestResult, TestResultStatus
from app.models.tag import Tag, problem_tags
from app.models.topic import Topic
from app.models.user import User, UserRole

__all__ = [
    "CodeDraft",
    "Problem",
    "ProblemDifficulty",
    "ProblemExample",
    "ProblemStatus",
    "ProgrammingLanguage",
    "StarterCode",
    "Submission",
    "SubmissionStatus",
    "SubmissionTestResult",
    "Tag",
    "TestCase",
    "TestResultStatus",
    "Topic",
    "User",
    "UserProblemProgress",
    "UserRole",
    "problem_tags",
]
