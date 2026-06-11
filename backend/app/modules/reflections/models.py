from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.content.models import Chapter, Concept, Exhibit
    from app.modules.users.models import User


class Reflection(Base):
    __tablename__ = "reflections"
    __table_args__ = (
        CheckConstraint(
            "visibility IN ('private', 'submitted')",
            name="ck_reflections_visibility",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey("chapters.id", ondelete="SET NULL"), index=True)
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id", ondelete="SET NULL"), index=True)
    exhibit_id: Mapped[int | None] = mapped_column(ForeignKey("exhibits.id", ondelete="SET NULL"), index=True)
    visibility: Mapped[str] = mapped_column(String(50), nullable=False)
    review_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", server_default="pending")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="reflections")
    chapter: Mapped["Chapter | None"] = relationship(back_populates="reflections")
    concept: Mapped["Concept | None"] = relationship(back_populates="reflections")
    exhibit: Mapped["Exhibit | None"] = relationship(back_populates="reflections")
