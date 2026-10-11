from sqlalchemy import Enum, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.problem import ProgrammingLanguage


class CodeDraft(TimestampMixin, Base):
    """A student's in-progress code: one row per (user, problem, language).

    `version` increases on every save. Clients send the version they last saw,
    so a save from a stale tab is detected (409) instead of silently
    overwriting newer code.
    """

    __tablename__ = "code_drafts"
    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", "language", name="uq_code_drafts_user_problem_language"),
        Index("ix_code_drafts_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Drafts belong to the user: deleting a user or problem removes its drafts.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[ProgrammingLanguage] = mapped_column(
        Enum(ProgrammingLanguage, name="programming_language"), nullable=False
    )
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
