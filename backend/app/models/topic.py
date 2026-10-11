from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.problem import Problem


class Topic(TimestampMixin, Base):
    """A step of the DSA learning path (e.g. Arrays).

    `parent_topic_id` is NULL for top-level topics. It lets subtopics such as
    Arrays → Prefix Sum be added later without a schema change.
    """

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # Name of a Lucide icon (e.g. "brackets"). The frontend maps it to a component.
    icon: Mapped[str | None] = mapped_column(String(40))
    # Short "What you will learn" bullet points.
    learning_outcomes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    parent_topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), index=True
    )

    problems: Mapped[list["Problem"]] = relationship(back_populates="topic")

    def __repr__(self) -> str:
        return f"<Topic id={self.id} slug={self.slug}>"
