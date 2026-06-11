from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.permissions import require_content_admin, require_learning_access
from app.db.session import get_db
from app.modules.content import service
from app.modules.content.models import ChapterVersion, Concept, Exhibit
from app.modules.content.schemas import (
    AdminChapterRead,
    ChapterCreate,
    ChapterDetailRead,
    ChapterListRead,
    ChapterUpdate,
    ChapterVersionRead,
    ChapterVersionUpdate,
    ConceptCreate,
    ConceptRead,
    ConceptUpdate,
    ExhibitCreate,
    ExhibitRead,
    ExhibitUpdate,
    PhaseCreate,
    PhaseRead,
    PhaseUpdate,
)


learning_router = APIRouter(prefix="/api/learning", dependencies=[Depends(require_learning_access)])
admin_router = APIRouter(prefix="/api/admin/content", dependencies=[Depends(require_content_admin)])


@learning_router.get("/phases", response_model=list[PhaseRead])
def get_learning_phases(db: Session = Depends(get_db)) -> list[PhaseRead]:
    return [
        PhaseRead(
            id=phase.id,
            name=phase.name,
            slug=phase.slug,
            description=phase.description,
            sort_order=phase.sort_order,
        )
        for phase in service.list_phases(db)
    ]


@learning_router.get("/chapters", response_model=list[ChapterListRead])
def get_learning_chapters(db: Session = Depends(get_db)) -> list[ChapterListRead]:
    return [
        ChapterListRead(
            id=chapter.id,
            curriculum_phase_id=chapter.curriculum_phase_id,
            title=version.title,
            summary=version.summary,
            learning_outcome=_first_learning_outcome(version),
            sort_order=chapter.sort_order,
            status=version.status,
            version_id=version.id,
        )
        for chapter, version in service.list_published_chapters(db)
    ]


@learning_router.get("/chapters/{chapter_id}", response_model=ChapterDetailRead)
def get_learning_chapter(chapter_id: int, db: Session = Depends(get_db)) -> ChapterDetailRead:
    chapter, version = service.get_published_chapter(db, chapter_id)
    return _chapter_detail(chapter.id, chapter.curriculum_phase_id, version.title, chapter.sort_order, version)


@admin_router.get("/chapters", response_model=list[AdminChapterRead])
def get_admin_chapters(db: Session = Depends(get_db)) -> list[AdminChapterRead]:
    return [
        AdminChapterRead(
            id=chapter.id,
            curriculum_phase_id=chapter.curriculum_phase_id,
            title=chapter.title,
            slug=chapter.slug,
            sort_order=chapter.sort_order,
            current_status=version.status if version else None,
            current_version_id=version.id if version else None,
        )
        for chapter, version in service.list_admin_chapters(db)
    ]


@admin_router.get("/phases", response_model=list[PhaseRead])
def get_admin_phases(db: Session = Depends(get_db)) -> list[PhaseRead]:
    return [_phase_read(phase) for phase in service.list_phases(db)]


@admin_router.post("/phases", response_model=PhaseRead, status_code=status.HTTP_201_CREATED)
def post_admin_phase(payload: PhaseCreate, db: Session = Depends(get_db)) -> PhaseRead:
    return _phase_read(service.create_phase(db, payload))


@admin_router.put("/phases/{phase_id}", response_model=PhaseRead)
def put_admin_phase(phase_id: int, payload: PhaseUpdate, db: Session = Depends(get_db)) -> PhaseRead:
    return _phase_read(service.update_phase(db, phase_id, payload))


@admin_router.delete("/phases/{phase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_phase(phase_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_phase(db, phase_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.post("/chapters", response_model=ChapterVersionRead, status_code=status.HTTP_201_CREATED)
def post_admin_chapter(payload: ChapterCreate, db: Session = Depends(get_db)) -> ChapterVersion:
    return service.create_chapter(db, payload)


@admin_router.put("/chapters/{chapter_id}", response_model=AdminChapterRead)
def put_admin_chapter(chapter_id: int, payload: ChapterUpdate, db: Session = Depends(get_db)) -> AdminChapterRead:
    chapter = service.update_chapter(db, chapter_id, payload)
    current = sorted(
        chapter.versions,
        key=lambda version: (version.status != "published", -version.version_number),
    )[0] if chapter.versions else None
    return AdminChapterRead(
        id=chapter.id,
        curriculum_phase_id=chapter.curriculum_phase_id,
        title=chapter.title,
        slug=chapter.slug,
        sort_order=chapter.sort_order,
        current_status=current.status if current else None,
        current_version_id=current.id if current else None,
    )


@admin_router.post("/chapters/{chapter_id}/draft", response_model=ChapterVersionRead, status_code=status.HTTP_201_CREATED)
def post_admin_chapter_draft(chapter_id: int, db: Session = Depends(get_db)) -> ChapterVersion:
    return service.create_draft_from_current(db, chapter_id)


@admin_router.put("/chapter-versions/{version_id}", response_model=ChapterVersionRead)
def put_admin_chapter_version(
    version_id: int,
    payload: ChapterVersionUpdate,
    db: Session = Depends(get_db),
) -> ChapterVersion:
    return service.update_draft_version(db, version_id, payload)


@admin_router.get("/chapter-versions/{version_id}", response_model=ChapterVersionRead)
def get_admin_chapter_version(version_id: int, db: Session = Depends(get_db)) -> ChapterVersion:
    return service.get_chapter_version(db, version_id)


@admin_router.post("/chapter-versions/{version_id}/publish", response_model=ChapterVersionRead)
def post_admin_chapter_version_publish(version_id: int, db: Session = Depends(get_db)) -> ChapterVersion:
    return service.publish_version(db, version_id)


@admin_router.post("/chapter-versions/{version_id}/concepts", response_model=ConceptRead, status_code=status.HTTP_201_CREATED)
def post_admin_concept(version_id: int, payload: ConceptCreate, db: Session = Depends(get_db)) -> ConceptRead:
    return _concept_read(service.create_concept(db, version_id, payload))


@admin_router.get("/chapter-versions/{version_id}/concepts", response_model=list[ConceptRead])
def get_admin_concepts(version_id: int, db: Session = Depends(get_db)) -> list[ConceptRead]:
    return [_concept_read(concept) for concept in service.list_version_concepts(db, version_id)]


@admin_router.get("/concepts/{concept_id}", response_model=ConceptRead)
def get_admin_concept(concept_id: int, db: Session = Depends(get_db)) -> ConceptRead:
    return _concept_read(service.get_concept(db, concept_id))


@admin_router.put("/concepts/{concept_id}", response_model=ConceptRead)
def put_admin_concept(concept_id: int, payload: ConceptUpdate, db: Session = Depends(get_db)) -> ConceptRead:
    return _concept_read(service.update_concept(db, concept_id, payload))


@admin_router.delete("/concepts/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_concept(concept_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_concept(db, concept_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.post("/concepts/{concept_id}/exhibits", response_model=ExhibitRead, status_code=status.HTTP_201_CREATED)
def post_admin_exhibit(concept_id: int, payload: ExhibitCreate, db: Session = Depends(get_db)) -> ExhibitRead:
    return _exhibit_read(service.create_exhibit(db, concept_id, payload))


@admin_router.get("/concepts/{concept_id}/exhibits", response_model=list[ExhibitRead])
def get_admin_exhibits(concept_id: int, db: Session = Depends(get_db)) -> list[ExhibitRead]:
    return [_exhibit_read(exhibit) for exhibit in service.list_concept_exhibits(db, concept_id)]


@admin_router.get("/exhibits/{exhibit_id}", response_model=ExhibitRead)
def get_admin_exhibit(exhibit_id: int, db: Session = Depends(get_db)) -> ExhibitRead:
    return _exhibit_read(service.get_exhibit(db, exhibit_id))


@admin_router.put("/exhibits/{exhibit_id}", response_model=ExhibitRead)
def put_admin_exhibit(exhibit_id: int, payload: ExhibitUpdate, db: Session = Depends(get_db)) -> ExhibitRead:
    return _exhibit_read(service.update_exhibit(db, exhibit_id, payload))


@admin_router.delete("/exhibits/{exhibit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_exhibit(exhibit_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_exhibit(db, exhibit_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _chapter_detail(
    chapter_id: int,
    curriculum_phase_id: int | None,
    chapter_title: str,
    sort_order: int,
    version: ChapterVersion,
) -> ChapterDetailRead:
    return ChapterDetailRead(
        id=chapter_id,
        curriculum_phase_id=curriculum_phase_id,
        title=chapter_title,
        summary=version.summary,
        sort_order=sort_order,
        status=version.status,
        version_id=version.id,
        version_title=version.title,
        body=version.body,
        concepts=[_concept_read(concept) for concept in sorted(version.concepts, key=lambda item: (item.sort_order, item.id))],
    )


def _phase_read(phase) -> PhaseRead:
    return PhaseRead(
        id=phase.id,
        name=phase.name,
        slug=phase.slug,
        description=phase.description,
        sort_order=phase.sort_order,
    )


def _first_learning_outcome(version: ChapterVersion) -> str | None:
    for concept in sorted(version.concepts, key=lambda item: (item.sort_order, item.id)):
        if concept.learning_outcome:
            return concept.learning_outcome
    return None


def _concept_read(concept: Concept) -> ConceptRead:
    return ConceptRead(
        id=concept.id,
        title=concept.title,
        slug=concept.slug,
        description=concept.description,
        learning_outcome=concept.learning_outcome,
        teaching_material=concept.teaching_material,
        activities=concept.activities,
        sort_order=concept.sort_order,
        exhibits=[_exhibit_read(exhibit) for exhibit in sorted(concept.exhibits, key=lambda item: (item.sort_order, item.id))],
    )


def _exhibit_read(exhibit: Exhibit) -> ExhibitRead:
    return ExhibitRead(
        id=exhibit.id,
        concept_id=exhibit.concept_id,
        title=exhibit.title,
        field_type=exhibit.field_type,
        field_format=exhibit.field_format,
        content=exhibit.content,
        media_asset_id=exhibit.media_asset_id,
        sort_order=exhibit.sort_order,
    )
