"""Coding workspace schemas: drafts, run/submit requests and judged results."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.problem import ProblemDifficulty, ProgrammingLanguage
from app.models.submission import SubmissionStatus, TestResultStatus

# Large enough for any real solution, small enough to stop abuse (~200 KB).
MAX_SOURCE_CHARS = 200_000
MAX_STDIN_CHARS = 100_000


class _Input(BaseModel):
    # Unknown fields such as "user_id" are rejected: the user always comes from the JWT.
    model_config = ConfigDict(extra="forbid")


# ------------------------------------------------------------------ drafts
class DraftSave(_Input):
    language: ProgrammingLanguage
    source_code: str = Field(max_length=MAX_SOURCE_CHARS)
    # The draft version the client last loaded (0 = it saw no saved draft).
    base_version: int = Field(default=0, ge=0)
    # Overwrite even if another tab saved a newer version (explicit user choice).
    force: bool = False


class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    problem_id: int
    language: ProgrammingLanguage
    source_code: str
    version: int
    updated_at: datetime


class DraftSaveResult(BaseModel):
    saved: bool = True
    version: int
    updated_at: datetime


# ------------------------------------------------------------------ execution
# Hard cap on what the request parser accepts; the configurable byte limit
# (EXECUTION_MAX_SOURCE_BYTES) is enforced by the service with a clear 413.
PARSE_SOURCE_CHARS = 1_000_000


class CustomCaseIn(_Input):
    """A student's own test (never stored, never counted as an official test)."""

    input: str = Field(default="", max_length=MAX_STDIN_CHARS)
    expected_output: str | None = Field(default=None, max_length=MAX_STDIN_CHARS)


class RunRequest(_Input):
    problem_id: int = Field(ge=1, le=2_147_483_647)
    # Validated by the service (400 INVALID_LANGUAGE): never trust the selector.
    language: str | None = None
    source_code: str = Field(max_length=PARSE_SOURCE_CHARS)
    custom_cases: list[CustomCaseIn] = Field(default_factory=list, max_length=5)


class SubmitRequest(_Input):
    problem_id: int = Field(ge=1, le=2_147_483_647)
    language: str | None = None
    source_code: str = Field(max_length=PARSE_SOURCE_CHARS)


TestKind = Literal["public", "hidden", "custom"]


class TestResultOut(BaseModel):
    """One test's outcome. `status` uses the single per-test vocabulary
    (PASSED, FAILED, COMPILE_ERROR, RUNTIME_ERROR, TIME_LIMIT_EXCEEDED,
    MEMORY_LIMIT_EXCEEDED, OUTPUT_LIMIT_EXCEEDED, SYSTEM_ERROR, and EXECUTED for
    a custom RUN case without an expected output)."""

    __test__ = False

    # Official tests: 1-based position ("Test Case 3"). Custom cases: 1-based among custom cases.
    index: int
    kind: TestKind
    status: TestResultStatus
    runtime_ms: int | None = None
    memory_kb: int | None = None
    # Public and custom tests only. Always null for hidden tests: their input,
    # expected output and the program's output on them are never returned.
    input: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None
    stderr: str | None = None


class RunResult(BaseModel):
    """Result of RUN: public tests (+ the student's custom cases). Not stored."""

    verdict: SubmissionStatus
    passed_tests: int
    total_tests: int
    runtime_ms: int | None = None
    memory_kb: int | None = None
    compile_output: str | None = None
    message: str | None = None
    # Effective limits the judge applied (time scaled for the language).
    time_limit_ms: int | None = None
    memory_limit_kb: int | None = None
    results: list[TestResultOut]


class SubmissionProblemRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    difficulty: ProblemDifficulty


class SubmissionSummary(BaseModel):
    id: int
    problem: SubmissionProblemRef
    language: ProgrammingLanguage
    status: SubmissionStatus
    passed_tests: int
    total_tests: int
    runtime_ms: int | None = None
    memory_kb: int | None = None
    # The submission that first solved the problem for this student.
    is_first_accepted: bool = False
    submitted_at: datetime


class SubmissionPerformance(BaseModel):
    """Percentiles against other students' best accepted solutions (same problem
    and language). Null unless at least `min_sample` students can be compared."""

    runtime_percentile: float | None = None
    memory_percentile: float | None = None
    compared_with: int = 0
    min_sample: int


class SubmissionDetail(SubmissionSummary):
    error_message: str | None = None
    results: list[TestResultOut]
    # Tests not executed because judging stops at the first failure.
    not_run_tests: int = 0
    # Effective limits the judge applied (time scaled for the language).
    time_limit_ms: int | None = None
    memory_limit_kb: int | None = None
    performance: SubmissionPerformance | None = None
    finished_at: datetime | None = None
    # The student's own code (only ever returned to its author).
    source_code: str


class ExecutionHealth(BaseModel):
    available: bool
