from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


Role = Literal["super_admin", "content_admin", "teacher", "student"]


class UserCreate(BaseModel):
    organization_id: int
    email: EmailStr | None = None
    username: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None
    role: Role
    grade_label: str | None = None
    section_label: str | None = None
    is_active: bool = True

    @field_validator("username", "full_name", "grade_label", "section_label", mode="before")
    @classmethod
    def trim_optional_text(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class UserUpdate(BaseModel):
    organization_id: int | None = None
    email: EmailStr | None = None
    username: str = Field(min_length=2, max_length=100)
    full_name: str | None = None
    role: Role
    grade_label: str | None = None
    section_label: str | None = None
    is_active: bool = True


class UserActiveUpdate(BaseModel):
    is_active: bool


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    organization_name: str | None = None
    email: str | None = None
    username: str
    full_name: str | None = None
    role: str
    grade_label: str | None = None
    section_label: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PasswordResetTokenRead(BaseModel):
    user_id: int
    temporary_password: str
