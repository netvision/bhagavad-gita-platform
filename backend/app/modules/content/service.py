from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, selectinload

from app.core.sanitizer import sanitize_rich_html
from app.modules.content.models import Chapter, ChapterVersion, Concept, Exhibit
from app.modules.content.schemas import (
    ChapterCreate,
    ChapterVersionUpdate,
    ConceptCreate,
    ConceptUpdate,
    ExhibitCreate,
    ExhibitUpdate,
)
from app.modules.curriculum.models import CurriculumPhase


ALLOWED_EXHIBIT_FIELD_TYPES = {"html", "link", "image", "audio", "video"}


def list_phases(db: Session) -> list[CurriculumPhase]:
    return db.scalars(select(CurriculumPhase).order_by(CurriculumPhase.sort_order, CurriculumPhase.id)).all()


def _published_version_subquery():
    version_alias = aliased(ChapterVersion)
    return (
        select(version_alias.id)
        .where(version_alias.chapter_id == Chapter.id)
        .where(version_alias.status == "published")
        .order_by(version_alias.published_at.desc().nullslast(), version_alias.version_number.desc())
        .limit(1)
        .correlate(Chapter)
        .scalar_subquery()
    )


def list_published_chapters(db: Session) -> list[tuple[Chapter, ChapterVersion]]:
    version_id = _published_version_subquery()
    return db.execute(
        select(Chapter, ChapterVersion)
        .join(ChapterVersion, ChapterVersion.id == version_id)
        .order_by(Chapter.sort_order, Chapter.id)
    ).all()


def get_published_chapter(db: Session, chapter_id: int) -> tuple[Chapter, ChapterVersion]:
    version = db.scalar(
        select(ChapterVersion)
        .options(selectinload(ChapterVersion.concepts).selectinload(Concept.exhibits))
        .where(ChapterVersion.chapter_id == chapter_id)
        .where(ChapterVersion.status == "published")
        .order_by(ChapterVersion.published_at.desc().nullslast(), ChapterVersion.version_number.desc())
        .limit(1)
    )
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published chapter not found")
    return version.chapter, version


def list_admin_chapters(db: Session) -> list[tuple[Chapter, ChapterVersion | None]]:
    rows: list[tuple[Chapter, ChapterVersion | None]] = []
    chapters = db.scalars(select(Chapter).options(selectinload(Chapter.versions)).order_by(Chapter.sort_order, Chapter.id)).all()
    for chapter in chapters:
        current = sorted(
            chapter.versions,
            key=lambda version: (version.status != "published", -version.version_number),
        )[0] if chapter.versions else None
        rows.append((chapter, current))
    return rows


def create_chapter(db: Session, payload: ChapterCreate) -> ChapterVersion:
    chapter = Chapter(
        curriculum_phase_id=payload.curriculum_phase_id,
        title=payload.title,
        slug=payload.slug,
        sort_order=payload.sort_order,
    )
    db.add(chapter)
    db.flush()
    version = ChapterVersion(
        chapter_id=chapter.id,
        version_number=1,
        status="draft",
        title=payload.title,
        summary=sanitize_rich_html(payload.summary),
        body=sanitize_rich_html(payload.body),
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def create_draft_from_current(db: Session, chapter_id: int) -> ChapterVersion:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    source = db.scalar(
        select(ChapterVersion)
        .options(selectinload(ChapterVersion.concepts).selectinload(Concept.exhibits))
        .where(ChapterVersion.chapter_id == chapter_id)
        .where(ChapterVersion.status == "published")
        .order_by(ChapterVersion.published_at.desc().nullslast(), ChapterVersion.version_number.desc())
        .limit(1)
    )
    if source is None:
        source = db.scalar(
            select(ChapterVersion)
            .options(selectinload(ChapterVersion.concepts).selectinload(Concept.exhibits))
            .where(ChapterVersion.chapter_id == chapter_id)
            .order_by(ChapterVersion.version_number.desc())
            .limit(1)
        )
    if source is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chapter has no version to copy")

    next_number = (db.scalar(select(func.max(ChapterVersion.version_number)).where(ChapterVersion.chapter_id == chapter_id)) or 0) + 1
    draft = ChapterVersion(
        chapter_id=chapter.id,
        version_number=next_number,
        status="draft",
        title=source.title,
        summary=source.summary,
        body=source.body,
    )
    db.add(draft)
    db.flush()

    concept_map: dict[int, Concept] = {}
    for concept in sorted(source.concepts, key=lambda item: (item.sort_order, item.id)):
        copied = Concept(
            chapter_version_id=draft.id,
            title=concept.title,
            slug=concept.slug,
            description=concept.description,
            learning_outcome=concept.learning_outcome,
            teaching_material=concept.teaching_material,
            activities=concept.activities,
            sort_order=concept.sort_order,
        )
        db.add(copied)
        db.flush()
        concept_map[concept.id] = copied
        for exhibit in sorted(concept.exhibits, key=lambda item: (item.sort_order, item.id)):
            db.add(
                Exhibit(
                    chapter_version_id=draft.id,
                    concept_id=copied.id,
                    media_asset_id=exhibit.media_asset_id,
                    title=exhibit.title,
                    field_type=exhibit.field_type,
                    field_format=exhibit.field_format,
                    content=exhibit.content,
                    sort_order=exhibit.sort_order,
                )
            )

    for exhibit in sorted([item for item in source.exhibits if item.concept_id is None], key=lambda item: (item.sort_order, item.id)):
        db.add(
            Exhibit(
                chapter_version_id=draft.id,
                concept_id=None,
                media_asset_id=exhibit.media_asset_id,
                title=exhibit.title,
                field_type=exhibit.field_type,
                field_format=exhibit.field_format,
                content=exhibit.content,
                sort_order=exhibit.sort_order,
            )
        )

    db.commit()
    db.refresh(draft)
    return draft


def update_draft_version(db: Session, version_id: int, payload: ChapterVersionUpdate) -> ChapterVersion:
    version = _require_draft_version(db, version_id)
    version.title = payload.title
    version.summary = sanitize_rich_html(payload.summary)
    version.body = sanitize_rich_html(payload.body)
    db.commit()
    db.refresh(version)
    return version


def get_chapter_version(db: Session, version_id: int) -> ChapterVersion:
    version = db.get(ChapterVersion, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter version not found")
    return version


def list_version_concepts(db: Session, version_id: int) -> list[Concept]:
    version = db.scalar(
        select(ChapterVersion)
        .options(selectinload(ChapterVersion.concepts).selectinload(Concept.exhibits))
        .where(ChapterVersion.id == version_id)
    )
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter version not found")
    return sorted(version.concepts, key=lambda item: (item.sort_order, item.id))


def get_concept(db: Session, concept_id: int) -> Concept:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")
    return concept


def publish_version(db: Session, version_id: int) -> ChapterVersion:
    version = db.get(ChapterVersion, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter version not found")
    if version.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft versions can be published")

    now = datetime.now(timezone.utc)
    for current in db.scalars(
        select(ChapterVersion)
        .where(ChapterVersion.chapter_id == version.chapter_id)
        .where(ChapterVersion.status == "published")
        .where(ChapterVersion.id != version.id)
    ):
        current.status = "archived"
    version.status = "published"
    version.published_at = now
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chapter already has a published version",
        ) from exc
    db.refresh(version)
    return version


def create_concept(db: Session, version_id: int, payload: ConceptCreate) -> Concept:
    version = _require_draft_version(db, version_id)
    concept = Concept(chapter_version_id=version.id, **_concept_values(payload))
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept


def update_concept(db: Session, concept_id: int, payload: ConceptUpdate) -> Concept:
    concept = _require_draft_concept(db, concept_id)
    for key, value in _concept_values(payload).items():
        setattr(concept, key, value)
    db.commit()
    db.refresh(concept)
    return concept


def delete_concept(db: Session, concept_id: int) -> None:
    concept = _require_draft_concept(db, concept_id)
    db.delete(concept)
    db.commit()


def create_exhibit(db: Session, concept_id: int, payload: ExhibitCreate) -> Exhibit:
    concept = _require_draft_concept(db, concept_id)
    exhibit = Exhibit(chapter_version_id=concept.chapter_version_id, concept_id=concept.id, **_exhibit_values(payload))
    db.add(exhibit)
    db.commit()
    db.refresh(exhibit)
    return exhibit


def list_concept_exhibits(db: Session, concept_id: int) -> list[Exhibit]:
    concept = db.scalar(select(Concept).options(selectinload(Concept.exhibits)).where(Concept.id == concept_id))
    if concept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")
    return sorted(concept.exhibits, key=lambda item: (item.sort_order, item.id))


def get_exhibit(db: Session, exhibit_id: int) -> Exhibit:
    exhibit = db.get(Exhibit, exhibit_id)
    if exhibit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exhibit not found")
    return exhibit


def update_exhibit(db: Session, exhibit_id: int, payload: ExhibitUpdate) -> Exhibit:
    exhibit = db.get(Exhibit, exhibit_id)
    if exhibit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exhibit not found")
    if exhibit.chapter_version.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft exhibits can be changed")
    for key, value in _exhibit_values(payload).items():
        setattr(exhibit, key, value)
    db.commit()
    db.refresh(exhibit)
    return exhibit


def delete_exhibit(db: Session, exhibit_id: int) -> None:
    exhibit = db.get(Exhibit, exhibit_id)
    if exhibit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exhibit not found")
    if exhibit.chapter_version.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft exhibits can be changed")
    db.delete(exhibit)
    db.commit()


def _require_draft_version(db: Session, version_id: int) -> ChapterVersion:
    version = db.get(ChapterVersion, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter version not found")
    if version.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft versions can be changed")
    return version


def _require_draft_concept(db: Session, concept_id: int) -> Concept:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")
    if concept.chapter_version.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft concepts can be changed")
    return concept


def _concept_values(payload: ConceptCreate | ConceptUpdate) -> dict[str, object]:
    return {
        "title": payload.title,
        "slug": payload.slug,
        "description": sanitize_rich_html(payload.description),
        "learning_outcome": sanitize_rich_html(payload.learning_outcome),
        "teaching_material": sanitize_rich_html(payload.teaching_material),
        "activities": sanitize_rich_html(payload.activities),
        "sort_order": payload.sort_order,
    }


def _exhibit_values(payload: ExhibitCreate | ExhibitUpdate) -> dict[str, object]:
    if payload.field_type not in ALLOWED_EXHIBIT_FIELD_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid exhibit field_type")
    content = sanitize_rich_html(payload.content) if payload.field_type == "html" else payload.content
    return {
        "title": payload.title,
        "field_type": payload.field_type,
        "field_format": payload.field_format,
        "content": content,
        "media_asset_id": payload.media_asset_id,
        "sort_order": payload.sort_order,
    }
