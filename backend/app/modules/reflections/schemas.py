from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class ReflectionCreate(BaseModel):
    chapter_id: int | None = None
    concept_id: int | None = None
    exhibit_id: int | None = None
    visibility: Literal["private", "submitted"] = "private"
    body: str

    @field_validator("body")
    @classmethod
    def body_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Body is required")
        return value


class ReflectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    chapter_id: int | None = None
    concept_id: int | None = None
    exhibit_id: int | None = None
    visibility: str
    review_status: str
    body: str
    submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
