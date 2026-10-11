import enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.tag import Tag, problem_tags

if TYPE_CHECKING:
    from app.models.topic import Topic
    from app.models.user import User


class ProblemDifficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class ProblemStatus(str, enum.Enum):
    """Lifecycle: DRAFT → PUBLISHED → ARCHIVED. Students only ever see PUBLISHED."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ProgrammingLanguage(str, enum.Enum):
    CPP = "CPP"
    JAVA = "JAVA"
    PYTHON = "PYTHON"


class Problem(TimestampMixin, Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    # Markdown source. Rendered as text on the client; never stored as HTML.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[ProblemDifficulty] = mapped_column(
        Enum(ProblemDifficulty, name="problem_difficulty"), nullable=False, index=True
    )
    # RESTRICT: a topic that still has problems cannot be deleted by accident.
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    constraints: Mapped[str] = mapped_column(Text, nullable=False, default="")
    input_format: Mapped[str] = mapped_column(Text, nullable=False, default="")
    output_format: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Execution limits sent to the judge (per language, the time limit is scaled
    # by the language's time_factor in app/core/languages.py).
    time_limit_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=2000, server_default="2000")
    memory_limit_kb: Mapped[int] = mapped_column(Integer, nullable=False, default=262144, server_default="262144")
    status: Mapped[ProblemStatus] = mapped_column(
        Enum(ProblemStatus, name="problem_status"),
        nullable=False,
        default=ProblemStatus.DRAFT,
        index=True,
    )
    # SET NULL: removing an author never removes their problems (and vice versa).
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    topic: Mapped["Topic"] = relationship(back_populates="problems")
    creator: Mapped["User | None"] = relationship("User")
    tags: Mapped[list[Tag]] = relationship(secondary=problem_tags, order_by=Tag.name)
    examples: Mapped[list["ProblemExample"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProblemExample.order_index",
    )
    starter_codes: Mapped[list["StarterCode"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="StarterCode.language",
    )
    # Contains hidden test cases: never serialize this for students.
    test_cases: Mapped[list["TestCase"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TestCase.order_index",
    )

    @property
    def is_published(self) -> bool:
        return self.status == ProblemStatus.PUBLISHED

    def __repr__(self) -> str:
        return f"<Problem id={self.id} slug={self.slug} status={self.status.value}>"


class ProblemExample(Base):
    """A worked example shown in the problem statement (always public)."""

    __tablename__ = "problem_examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class StarterCode(TimestampMixin, Base):
    """Initial editor contents for one language. Stored only; never executed."""

    __tablename__ = "starter_codes"
    __table_args__ = (UniqueConstraint("problem_id", "language", name="uq_starter_codes_problem_language"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[ProgrammingLanguage] = mapped_column(
        Enum(ProgrammingLanguage, name="programming_language"), nullable=False
    )
    starter_code: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional hidden harness for function-style problems: a full program that
    # contains the line {{USER_CODE}}, where the student's code is inserted. It
    # reads stdin, calls the student's function and prints the result. Never
    # sent to students. NULL = the student's code is the whole program.
    driver_code: Mapped[str | None] = mapped_column(Text)


class TestCase(TimestampMixin, Base):
    """Judge input/output pair. Hidden cases are admin-only (future judge use)."""

    __tablename__ = "test_cases"
    __test__ = False  # not a pytest test class
    __table_args__ = (Index("ix_test_cases_problem_hidden", "problem_id", "is_hidden"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

