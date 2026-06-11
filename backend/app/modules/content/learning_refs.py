from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.content.models import Chapter, ChapterVersion, Concept, Exhibit


def published_chapter_values(db: Session, chapter_id: int) -> dict[str, int | None]:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    published_version_id = db.scalar(
        select(ChapterVersion.id)
        .where(ChapterVersion.chapter_id == chapter.id)
        .where(ChapterVersion.status == "published")
        .limit(1)
    )
    if published_version_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published chapter not found")
    return {"chapter_id": chapter.id, "concept_id": None, "exhibit_id": None}


def published_concept_values(db: Session, concept_id: int) -> dict[str, int | None]:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")
    if concept.chapter_version.status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published concept not found")
    return {
        "chapter_id": concept.chapter_version.chapter_id,
        "concept_id": concept.id,
        "exhibit_id": None,
    }


def published_exhibit_values(db: Session, exhibit_id: int) -> dict[str, int | None]:
    exhibit = db.get(Exhibit, exhibit_id)
    if exhibit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exhibit not found")
    if exhibit.chapter_version.status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published exhibit not found")
    return {
        "chapter_id": exhibit.chapter_version.chapter_id,
        "concept_id": exhibit.concept_id,
        "exhibit_id": exhibit.id,
    }
