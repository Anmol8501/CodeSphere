from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UserProblemProgress(TimestampMixin, Base):
    """One student's progress on one problem, maintained from judged submissions.

    Written only by the backend, in the same transaction that records a
    submission's final verdict (progress_service.record_judged_submission),
    and rebuildable at any time from the submissions table
    (`python -m app.utils.rebuild_progress`). Never accepted from clients.

    Status is derived, not stored: SOLVED when solved_at is set, ATTEMPTED when
    attempt_count > 0, otherwise NOT STARTED (no row at all).
    """

    __tablename__ = "user_problem_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_user_problem_progress_user_problem"),
        # Problem statistics (solved by N students, acceptance) group by problem.
        Index("ix_user_problem_progress_problem", "problem_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    # Judged submissions (verdicts on the code; infrastructure failures excluded).
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    accepted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    first_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When the first ACCEPTED submission was made (NULL = not solved).
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Lowest valid runtime / memory among ACCEPTED submissions.
    best_runtime_ms: Mapped[int | None] = mapped_column(Integer)
    best_memory_kb: Mapped[int | None] = mapped_column(Integer)
