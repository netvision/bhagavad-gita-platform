from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sanitize import sanitize_file_key, sanitize_required_text, sanitize_text


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ExhibitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: Optional[int] = None
    field_key: str
    field_type: str
    field_value: Optional[str] = None
    file_key: Optional[str] = None
    file_url: Optional[str] = None
    sort_order: int = 0


class ConceptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: Optional[int] = None
    s_no: Optional[str] = None
    title: str
    display_order: int = 0
    concept_description: Optional[str] = None
    sessions: Optional[str] = None
    learning_outcomes: Optional[str] = None
    integration_other_sub: Optional[str] = None
    teaching_materials_methods: Optional[str] = None
    library: Optional[str] = None
    activity: Optional[str] = None
    life_lesson: Optional[str] = None
    remarks: Optional[str] = None
    exhibit_ref: Optional[str] = None
    exhibits: List[ExhibitOut] = Field(default_factory=list)


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: Optional[int] = None
    title: str
    aim: Optional[str] = None
    order_index: int = 0
    pdf_filename: Optional[str] = None
    pdf_url: Optional[str] = None
    is_published: bool = True
    concepts: List[ConceptOut] = Field(default_factory=list)


class ChapterIn(BaseModel):
    title: str
    aim: Optional[str] = None
    order_index: int = 0
    pdf_filename: Optional[str] = None
    is_published: bool = True

    @field_validator("title", mode="before")
    @classmethod
    def clean_required_text(cls, value):
        return sanitize_required_text(value)

    @field_validator("aim", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        return sanitize_text(value)

    @field_validator("pdf_filename", mode="before")
    @classmethod
    def clean_file_key(cls, value):
        return sanitize_file_key(value)


class ConceptIn(BaseModel):
    chapter_id: int
    s_no: Optional[str] = None
    title: str
    display_order: int = 0
    concept_description: Optional[str] = None
    sessions: Optional[str] = None
    learning_outcomes: Optional[str] = None
    integration_other_sub: Optional[str] = None
    teaching_materials_methods: Optional[str] = None
    library: Optional[str] = None
    activity: Optional[str] = None
    life_lesson: Optional[str] = None
    remarks: Optional[str] = None
    exhibit_ref: Optional[str] = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_required_text(cls, value):
        return sanitize_required_text(value)

    @field_validator(
        "s_no",
        "concept_description",
        "sessions",
        "learning_outcomes",
        "integration_other_sub",
        "teaching_materials_methods",
        "library",
        "activity",
        "life_lesson",
        "remarks",
        "exhibit_ref",
        mode="before",
    )
    @classmethod
    def clean_optional_text(cls, value):
        return sanitize_text(value)


class ExhibitIn(BaseModel):
    concept_id: int
    field_key: str
    field_type: str = "string"
    field_value: Optional[str] = None
    file_key: Optional[str] = None
    sort_order: int = 0

    @field_validator("field_key", mode="before")
    @classmethod
    def clean_required_text(cls, value):
        return sanitize_required_text(value)

    @field_validator("field_type", "field_value", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        return sanitize_text(value)

    @field_validator("file_key", mode="before")
    @classmethod
    def clean_file_key(cls, value):
        return sanitize_file_key(value)
