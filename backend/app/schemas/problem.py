"""Problem schemas returned to signed-in users (students and staff).

These models are the security boundary for problem data: they contain only
public information. Hidden test cases, lifecycle status and authoring metadata
are not part of any model in this file, so they cannot be serialized here.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.problem import ProblemDifficulty, ProgrammingLanguage

# SOLVED = has an ACCEPTED submission; ATTEMPTED = judged submissions but none
# accepted; UNSOLVED = never attempted (shown as "Not Attempted").
UserProblemStatus = Literal["SOLVED", "ATTEMPTED", "UNSOLVED"]
ProgressFilter = Literal["solved", "attempted", "unsolved"]


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TagOut(_Orm):
    id: int
    name: str
    slug: str


class TopicRef(_Orm):
    id: int
    name: str
    slug: str


class ProblemExampleOut(_Orm):
    input: str
    output: str
    explanation: str | None = None
    order_index: int


class StarterCodeOut(_Orm):
    language: ProgrammingLanguage
    starter_code: str


class SampleTestCaseOut(_Orm):
    """A test case the author marked visible (is_hidden = false)."""

    input_data: str
    expected_output: str
    order_index: int


class ProblemStats(BaseModel):
    """Problem statistics across all students (aggregates only, no personal data).

    solved_by       distinct students with an ACCEPTED submission
    attempts        judged submissions (infrastructure failures excluded)
    accepted        ACCEPTED submissions
    acceptance_rate accepted / attempts * 100, submission-based (None without attempts)
    """

    solved_by: int = 0
    attempts: int = 0
    accepted: int = 0
    acceptance_rate: float | None = None


class UserProblemProgressOut(BaseModel):
    """The signed-in student's own progress on one problem."""

    status: UserProblemStatus = "UNSOLVED"
    attempts: int = 0
    accepted_submissions: int = 0
    first_attempt_at: datetime | None = None
    last_attempt_at: datetime | None = None
    solved_at: datetime | None = None
    best_runtime_ms: int | None = None
    best_memory_kb: int | None = None


class ProblemListItem(_Orm):
    id: int
    title: str
    slug: str
    difficulty: ProblemDifficulty
    topic: TopicRef
    tags: list[TagOut]
    user_status: UserProblemStatus = "UNSOLVED"
    stats: ProblemStats = ProblemStats()


class ProblemDetail(ProblemListItem):
    description: str
    constraints: str
    input_format: str
    output_format: str
    examples: list[ProblemExampleOut]
    starter_codes: list[StarterCodeOut]
    sample_test_cases: list[SampleTestCaseOut]
    # Languages the coding workspace offers for this problem.
    languages: list[ProgrammingLanguage]
    # Judge limits (shown to students; never accepted from them).
    time_limit_ms: int
    memory_limit_kb: int
    # The signed-in student's own progress (None for staff / admin).
    progress: UserProblemProgressOut | None = None
