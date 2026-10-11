import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.problem import Problem, ProgrammingLanguage


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    COMPILE_ERROR = "COMPILE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
    # Infrastructure problems: never held against the student's solution.
    SYSTEM_ERROR = "SYSTEM_ERROR"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"


# Statuses that are still being judged (must always resolve; see cleanup).
IN_PROGRESS_STATUSES = (SubmissionStatus.PENDING, SubmissionStatus.RUNNING)
# Infrastructure failures: not a verdict on the code, not counted as attempts.
INFRASTRUCTURE_STATUSES = (SubmissionStatus.SYSTEM_ERROR, SubmissionStatus.EXECUTION_TIMEOUT)
# Verdicts on the student's code. Only these count as attempts, decide solved
# state, acceptance rates, streaks and activity (see docs/ANALYTICS.md).
JUDGED_STATUSES = tuple(s for s in SubmissionStatus if s not in IN_PROGRESS_STATUSES + INFRASTRUCTURE_STATUSES)


class TestResultStatus(str, enum.Enum):
    """Outcome of ONE test case. The single vocabulary for per-test results."""

    __test__ = False  # not a pytest class

    PASSED = "PASSED"
    FAILED = "FAILED"  # wrong answer
    COMPILE_ERROR = "COMPILE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    # RUN only: a student's custom case without an expected output (nothing to
    # compare). Custom cases are never stored, so this never reaches the table.
    EXECUTED = "EXECUTED"


# Judge verdict of a single test (SubmissionStatus value, or "EXECUTED") -> test status.
TEST_STATUS_FOR_VERDICT: dict[str, TestResultStatus] = {
    SubmissionStatus.ACCEPTED.value: TestResultStatus.PASSED,
    SubmissionStatus.WRONG_ANSWER.value: TestResultStatus.FAILED,
    SubmissionStatus.COMPILE_ERROR.value: TestResultStatus.COMPILE_ERROR,
    SubmissionStatus.RUNTIME_ERROR.value: TestResultStatus.RUNTIME_ERROR,
    SubmissionStatus.TIME_LIMIT_EXCEEDED.value: TestResultStatus.TIME_LIMIT_EXCEEDED,
    SubmissionStatus.MEMORY_LIMIT_EXCEEDED.value: TestResultStatus.MEMORY_LIMIT_EXCEEDED,
    SubmissionStatus.OUTPUT_LIMIT_EXCEEDED.value: TestResultStatus.OUTPUT_LIMIT_EXCEEDED,
    SubmissionStatus.SYSTEM_ERROR.value: TestResultStatus.SYSTEM_ERROR,
    SubmissionStatus.EXECUTION_TIMEOUT.value: TestResultStatus.SYSTEM_ERROR,
    TestResultStatus.EXECUTED.value: TestResultStatus.EXECUTED,
}


class Submission(Base):
    """A student's official submission, judged against public + hidden tests.

    Verdicts are decided by the backend only (never taken from the client).
    Per-test outcomes live in `submission_test_results`; the student's
    per-problem progress (attempts, solved, best runtime/memory) is kept in
    `user_problem_progress` and updated in the same transaction that records
    the final verdict.
    """

    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_user_problem", "user_id", "problem_id"),
        Index("ix_submissions_submitted_at", "submitted_at"),
        # History, heatmap and streak queries: one student's submissions by time.
        Index("ix_submissions_user_submitted", "user_id", "submitted_at"),
        # At most ONE first-accepted submission per student and problem,
        # guaranteed by the database rather than by application code.
        Index(
            "uq_submissions_first_accepted",
            "user_id",
            "problem_id",
            unique=True,
            postgresql_where=text("is_first_accepted"),
            sqlite_where=text("is_first_accepted"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[ProgrammingLanguage] = mapped_column(
        Enum(ProgrammingLanguage, name="programming_language"), nullable=False
    )
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status"),
        nullable=False,
        default=SubmissionStatus.PENDING,
        index=True,
    )
    passed_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Slowest test (ms) and peak memory (KB) across executed tests.
    runtime_ms: Mapped[int | None] = mapped_column(Integer)
    memory_kb: Mapped[int | None] = mapped_column(Integer)
    # Effective limits applied by the judge (per-language time factor
    # included), kept so old results still show the limit they were judged at.
    time_limit_ms: Mapped[int | None] = mapped_column(Integer)
    memory_limit_kb: Mapped[int | None] = mapped_column(Integer)
    # Safe, student-facing detail (compiler output, public-test stderr, or a message).
    error_message: Mapped[str | None] = mapped_column(Text)
    # True for the student's first ACCEPTED submission on this problem (see index above).
    is_first_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    problem: Mapped[Problem] = relationship()
    test_results: Mapped[list["SubmissionTestResult"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="SubmissionTestResult.position",
    )


class SubmissionTestResult(Base):
    """Outcome of one official test case in a judged submission.

    Only tests that were executed are stored (judging stops at the first
    failure; a compile error executes none). For PUBLIC tests the input,
    expected output, the program's output and stderr are kept (truncated) as
    they were at judging time. For HIDDEN tests those columns are always NULL:
    hidden data is reachable only internally through `test_case_id`.
    """

    __tablename__ = "submission_test_results"
    __table_args__ = (
        UniqueConstraint("submission_id", "position", name="uq_submission_test_results_position"),
        Index("ix_submission_test_results_test_case", "test_case_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    # The test case it was judged against (NULL if the test case was later deleted).
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_cases.id", ondelete="SET NULL"))
    # 1-based order among the official tests at judging time ("Test Case 3").
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    # Visibility when it was judged. Hidden results never carry test data.
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[TestResultStatus] = mapped_column(
        Enum(TestResultStatus, name="test_result_status"), nullable=False
    )
    runtime_ms: Mapped[int | None] = mapped_column(Integer)
    memory_kb: Mapped[int | None] = mapped_column(Integer)
    input_data: Mapped[str | None] = mapped_column(Text)
    expected_output: Mapped[str | None] = mapped_column(Text)
    actual_output: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    submission: Mapped[Submission] = relationship(back_populates="test_results")
