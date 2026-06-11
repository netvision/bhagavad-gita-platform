from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.content.learning_refs import (
    published_chapter_values,
    published_concept_values,
    published_exhibit_values,
)
from app.modules.reflections.models import Reflection
from app.modules.reflections.schemas import ReflectionCreate
from app.modules.users.models import User


def create_reflection(db: Session, payload: ReflectionCreate, current_user: User) -> Reflection:
    values = _reflection_content_values(db, payload)
    reflection = Reflection(
        user_id=current_user.id,
        chapter_id=values["chapter_id"],
        concept_id=values["concept_id"],
        exhibit_id=values["exhibit_id"],
        visibility=payload.visibility,
        body=payload.body,
        submitted_at=datetime.now(timezone.utc) if payload.visibility == "submitted" else None,
    )
    db.add(reflection)
    db.commit()
    db.refresh(reflection)
    return reflection


def list_user_reflections(db: Session, current_user: User) -> list[Reflection]:
    return db.scalars(
        select(Reflection)
        .where(Reflection.user_id == current_user.id)
        .order_by(Reflection.created_at.desc(), Reflection.id.desc())
    ).all()


def get_visible_reflection(db: Session, reflection_id: int, current_user: User) -> Reflection:
    reflection = db.get(Reflection, reflection_id)
    if reflection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reflection not found")
    if reflection.user_id == current_user.id:
        return reflection
    if current_user.role == "super_admin" and reflection.visibility == "submitted":
        return reflection
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reflection not found")


def _reflection_content_values(db: Session, payload: ReflectionCreate) -> dict[str, int | None]:
    if payload.exhibit_id is not None:
        values = published_exhibit_values(db, payload.exhibit_id)
        _reject_if_mismatch(payload.chapter_id, values["chapter_id"], "chapter_id")
        _reject_if_mismatch(payload.concept_id, values["concept_id"], "concept_id")
        return values

    if payload.concept_id is not None:
        values = published_concept_values(db, payload.concept_id)
        _reject_if_mismatch(payload.chapter_id, values["chapter_id"], "chapter_id")
        return values

    if payload.chapter_id is not None:
        return published_chapter_values(db, payload.chapter_id)

    return {"chapter_id": None, "concept_id": None, "exhibit_id": None}


def _reject_if_mismatch(provided: int | None, expected: int | None, field_name: str) -> None:
    if provided is not None and provided != expected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} does not match referenced content",
        )
