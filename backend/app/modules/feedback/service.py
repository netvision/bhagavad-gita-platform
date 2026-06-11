from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.content.learning_refs import (
    published_chapter_values,
    published_concept_values,
    published_exhibit_values,
)
from app.modules.feedback.models import Feedback
from app.modules.feedback.schemas import FeedbackCreate
from app.modules.users.models import User


def create_feedback(db: Session, payload: FeedbackCreate, current_user: User) -> Feedback:
    values = _scope_values(db, payload.scope_type, payload.scope_id)
    feedback = Feedback(
        user_id=current_user.id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        category=payload.category,
        rating=payload.rating,
        comment=payload.comment,
        **values,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def list_admin_feedback(db: Session, current_user: User) -> list[Feedback]:
    statement = select(Feedback).order_by(Feedback.created_at.desc(), Feedback.id.desc())
    if current_user.role != "super_admin":
        statement = statement.join(User, Feedback.user_id == User.id).where(
            User.organization_id == current_user.organization_id
        )
    return db.scalars(statement).all()


def _scope_values(db: Session, scope_type: str, scope_id: int | None) -> dict[str, int | None]:
    if scope_type == "app":
        return {"chapter_id": None, "concept_id": None, "exhibit_id": None}

    if scope_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope_id is required")

    if scope_type == "chapter":
        return published_chapter_values(db, scope_id)

    if scope_type == "concept":
        return published_concept_values(db, scope_id)

    return published_exhibit_values(db, scope_id)
