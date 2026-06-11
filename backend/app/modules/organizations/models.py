from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.curriculum.models import CurriculumPhase
    from app.modules.media.models import MediaAsset
    from app.modules.subscriptions.models import Subscription
    from app.modules.users.models import User


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint("type IN ('platform', 'school')", name="ck_organizations_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="organization")
    users: Mapped[list["User"]] = relationship(back_populates="organization")
    curriculum_phases: Mapped[list["CurriculumPhase"]] = relationship(back_populates="organization")
    media_assets: Mapped[list["MediaAsset"]] = relationship(back_populates="organization")
