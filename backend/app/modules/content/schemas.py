from datetime import datetime

from pydantic import BaseModel, Field


class PhaseRead(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    sort_order: int


class PhaseCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    sort_order: int = 0


class PhaseUpdate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    sort_order: int = 0


class ChapterListRead(BaseModel):
    id: int
    curriculum_phase_id: int | None = None
    title: str
    summary: str | None = None
    sort_order: int
    status: str
    version_id: int


class ExhibitRead(BaseModel):
    id: int
    concept_id: int | None = None
    title: str
    field_type: str
    field_format: str | None = None
    content: str | None = None
    media_asset_id: int | None = None
    sort_order: int


class ConceptRead(BaseModel):
    id: int
    title: str
    slug: str | None = None
    description: str | None = None
    learning_outcome: str | None = None
    teaching_material: str | None = None
    activities: str | None = None
    sort_order: int
    exhibits: list[ExhibitRead] = Field(default_factory=list)


class ChapterDetailRead(BaseModel):
    id: int
    curriculum_phase_id: int | None = None
    title: str
    summary: str | None = None
    sort_order: int
    status: str
    version_id: int
    version_title: str
    body: str | None = None
    concepts: list[ConceptRead] = Field(default_factory=list)


class AdminChapterRead(BaseModel):
    id: int
    curriculum_phase_id: int | None = None
    title: str
    slug: str
    sort_order: int
    current_status: str | None = None
    current_version_id: int | None = None


class ChapterCreate(BaseModel):
    curriculum_phase_id: int | None = None
    title: str
    slug: str
    sort_order: int = 0
    summary: str | None = None
    body: str | None = None


class ChapterUpdate(BaseModel):
    curriculum_phase_id: int | None = None
    title: str
    slug: str
    sort_order: int = 0


class ChapterVersionRead(BaseModel):
    id: int
    chapter_id: int
    version_number: int
    status: str
    title: str
    summary: str | None = None
    body: str | None = None
    published_at: datetime | None = None


class ChapterVersionUpdate(BaseModel):
    title: str
    summary: str | None = None
    body: str | None = None


class ConceptCreate(BaseModel):
    title: str
    slug: str | None = None
    description: str | None = None
    learning_outcome: str | None = None
    teaching_material: str | None = None
    activities: str | None = None
    sort_order: int = 0


class ConceptUpdate(BaseModel):
    title: str
    slug: str | None = None
    description: str | None = None
    learning_outcome: str | None = None
    teaching_material: str | None = None
    activities: str | None = None
    sort_order: int = 0


class ExhibitCreate(BaseModel):
    title: str
    field_type: str
    field_format: str | None = None
    content: str | None = None
    media_asset_id: int | None = None
    sort_order: int = 0


class ExhibitUpdate(BaseModel):
    title: str
    field_type: str
    field_format: str | None = None
    content: str | None = None
    media_asset_id: int | None = None
    sort_order: int = 0
