from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedbackCreate(BaseModel):
    scope_type: Literal["app", "chapter", "concept", "exhibit"]
    scope_id: int | None = None
    category: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str

    @field_validator("comment")
    @classmethod
    def comment_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Comment is required")
        return value

    @field_validator("category")
    @classmethod
    def trim_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    chapter_id: int | None = None
    concept_id: int | None = None
    exhibit_id: int | None = None
    scope_type: str
    scope_id: int | None = None
    category: str | None = None
    rating: int | None = None
    comment: str
    status: str
    created_at: datetime
    updated_at: datetime
