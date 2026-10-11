"""Admin-only problem management schemas (input validation + full output)."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.problem import ProblemDifficulty, ProblemStatus, ProgrammingLanguage
from app.schemas.problem import ProblemExampleOut, StarterCodeOut, TagOut, TopicRef
from app.services.judging.harness import USER_CODE_MARKER

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TEST_DATA_MAX = 100_000


class _Input(BaseModel):
    # Unknown fields (e.g. "status", "created_by") are rejected, not ignored.
    model_config = ConfigDict(extra="forbid")


def _clean_text(value: str) -> str:
    return value.replace("\r\n", "\n").strip()


# ------------------------------------------------------------------ inputs
class ExampleIn(_Input):
    input: str = Field(min_length=1, max_length=5000)
    output: str = Field(min_length=1, max_length=5000)
    explanation: str | None = Field(default=None, max_length=2000)

    @field_validator("input", "output")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = _clean_text(value)
        if not value:
            raise ValueError("Example input and output cannot be empty.")
        return value

    @field_validator("explanation")
    @classmethod
    def _clean_explanation(cls, value: str | None) -> str | None:
        value = _clean_text(value) if value else ""
        return value or None


class StarterCodeIn(_Input):
    language: ProgrammingLanguage
    starter_code: str = Field(min_length=1, max_length=20_000)
    # Hidden harness for function-style problems: a full program containing
    # {{USER_CODE}} exactly once (see app/services/judging/harness.py).
    driver_code: str | None = Field(default=None, max_length=50_000)

    @field_validator("starter_code")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.replace("\r\n", "\n").rstrip()
        if not value.strip():
            raise ValueError("Starter code cannot be empty.")
        return value + "\n"

    @field_validator("driver_code")
    @classmethod
    def _check_driver(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.replace("\r\n", "\n")
        if value.count(USER_CODE_MARKER) != 1:
            raise ValueError(f"The execution harness must contain {USER_CODE_MARKER} exactly once.")
        return value


class TestCaseIn(_Input):
    __test__ = False  # not a pytest test class

    # Whitespace is significant for judges, so test data is stored as given
    # (only Windows line endings are normalized).
    input_data: str = Field(default="", max_length=TEST_DATA_MAX)
    expected_output: str = Field(min_length=1, max_length=TEST_DATA_MAX)
    is_hidden: bool = True
    order_index: int | None = Field(default=None, ge=0, le=10_000)

    @field_validator("input_data", "expected_output")
    @classmethod
    def _normalize_newlines(cls, value: str) -> str:
        return value.replace("\r\n", "\n")


class ProblemIn(_Input):
    title: str = Field(min_length=3, max_length=150)
    slug: str | None = Field(default=None, max_length=160)
    description: str = Field(min_length=10, max_length=20_000)
    difficulty: ProblemDifficulty
    topic_id: int = Field(ge=1)
    tag_ids: list[int] = Field(default_factory=list, max_length=10)
    constraints: str = Field(default="", max_length=5000)
    input_format: str = Field(default="", max_length=5000)
    output_format: str = Field(default="", max_length=5000)
    # Judge limits (the time limit is scaled per language by its time factor).
    time_limit_ms: int = Field(default=2000, ge=100, le=10_000)
    memory_limit_kb: int = Field(default=262_144, ge=16_384, le=512_000)
    examples: list[ExampleIn] = Field(default_factory=list, max_length=10)
    starter_codes: list[StarterCodeIn] = Field(default_factory=list, max_length=3)

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 3:
            raise ValueError("Title must be at least 3 characters.")
        return value

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None  # generated from the title
        value = value.strip().lower()
        if not SLUG_PATTERN.match(value):
            raise ValueError("Slug may only contain lowercase letters, numbers and single hyphens.")
        return value

    @field_validator("description", "constraints", "input_format", "output_format")
    @classmethod
    def _clean(cls, value: str) -> str:
        return _clean_text(value)

    @field_validator("description")
    @classmethod
    def _description_length(cls, value: str) -> str:
        if len(value) < 10:
            raise ValueError("Description must be at least 10 characters.")
        return value

    @field_validator("tag_ids")
    @classmethod
    def _unique_tags(cls, value: list[int]) -> list[int]:
        return list(dict.fromkeys(value))

    @field_validator("starter_codes")
    @classmethod
    def _unique_languages(cls, value: list[StarterCodeIn]) -> list[StarterCodeIn]:
        languages = [item.language for item in value]
        if len(languages) != len(set(languages)):
            raise ValueError("Each language can only have one starter code.")
        return value


class ProblemCreate(ProblemIn):
    test_cases: list[TestCaseIn] = Field(default_factory=list, max_length=50)
    is_published: bool = False


class ProblemUpdate(ProblemIn):
    """Full replacement of the problem content. Test cases have their own endpoints."""

    is_published: bool | None = None


class PublishUpdate(_Input):
    is_published: bool


class TagCreate(_Input):
    name: str = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Tag name is required.")
        return value


# ------------------------------------------------------------------ outputs
class TestCaseOut(BaseModel):
    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    input_data: str
    expected_output: str
    is_hidden: bool
    order_index: int
    created_at: datetime
    updated_at: datetime


class AdminStarterCodeOut(StarterCodeOut):
    driver_code: str | None = None


class AdminProblemListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    difficulty: ProblemDifficulty
    status: ProblemStatus
    is_published: bool
    topic: TopicRef
    tags: list[TagOut]
    test_case_count: int = 0
    hidden_test_case_count: int = 0
    created_by_name: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminProblemDetail(AdminProblemListItem):
    description: str
    constraints: str
    input_format: str
    output_format: str
    examples: list[ProblemExampleOut]
    time_limit_ms: int
    memory_limit_kb: int
    starter_codes: list[AdminStarterCodeOut]
    test_cases: list[TestCaseOut]
