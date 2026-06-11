from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int | None = None
    uploaded_by: int | None = None
    storage_key: str
    original_filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    visibility: str
    alt_text: str | None = None
    created_at: datetime


class MediaUrlOut(BaseModel):
    url: str
    expires_seconds: int
