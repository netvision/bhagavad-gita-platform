from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.curriculum.models import CurriculumPhase
    from app.modules.feedback.models import Feedback
    from app.modules.media.models import MediaAsset
    from app.modules.reflections.models import Reflection


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("curriculum_phase_id", "slug", name="uq_chapters_phase_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    curriculum_phase_id: Mapped[int | None] = mapped_column(ForeignKey("curriculum_phases.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    curriculum_phase: Mapped["CurriculumPhase | None"] = relationship(back_populates="chapters")
    versions: Mapped[list["ChapterVersion"]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
    )
    feedback_items: Mapped[list["Feedback"]] = relationship(back_populates="chapter")
    reflections: Mapped[list["Reflection"]] = relationship(back_populates="chapter")


class ChapterVersion(Base):
    __tablename__ = "chapter_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_chapter_versions_status",
        ),
        UniqueConstraint("chapter_id", "version_number", name="uq_chapter_versions_chapter_version"),
        Index(
            "uq_chapter_versions_one_published_per_chapter",
            "chapter_id",
            unique=True,
            sqlite_where=text("status = 'published'"),
            postgresql_where=text("status = 'published'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chapter: Mapped["Chapter"] = relationship(back_populates="versions")
    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="chapter_version",
        cascade="all, delete-orphan",
    )
    exhibits: Mapped[list["Exhibit"]] = relationship(
        back_populates="chapter_version",
        cascade="all, delete-orphan",
    )


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_version_id: Mapped[int] = mapped_column(
        ForeignKey("chapter_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    learning_outcome: Mapped[str | None] = mapped_column(Text)
    teaching_material: Mapped[str | None] = mapped_column(Text)
    activities: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chapter_version: Mapped["ChapterVersion"] = relationship(back_populates="concepts")
    exhibits: Mapped[list["Exhibit"]] = relationship(
        back_populates="concept",
        cascade="all, delete-orphan",
    )
    feedback_items: Mapped[list["Feedback"]] = relationship(back_populates="concept")
    reflections: Mapped[list["Reflection"]] = relationship(back_populates="concept")


class Exhibit(Base):
    __tablename__ = "exhibits"
    __table_args__ = (
        CheckConstraint(
            "field_type IN ('html', 'link', 'image', 'audio', 'video')",
            name="ck_exhibits_field_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_version_id: Mapped[int] = mapped_column(
        ForeignKey("chapter_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    media_asset_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    field_format: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chapter_version: Mapped["ChapterVersion"] = relationship(back_populates="exhibits")
    concept: Mapped["Concept | None"] = relationship(back_populates="exhibits")
    media_asset: Mapped["MediaAsset | None"] = relationship(back_populates="exhibits")
    feedback_items: Mapped[list["Feedback"]] = relationship(back_populates="exhibit")
    reflections: Mapped[list["Reflection"]] = relationship(back_populates="exhibit")
