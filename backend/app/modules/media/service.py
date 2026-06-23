from pathlib import Path
import re
from tempfile import SpooledTemporaryFile
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.config import get_settings
from app.modules.media.models import MediaAsset
from app.modules.users.models import User


ALLOWED_MIME_PREFIXES = ("image/", "audio/", "video/")
ALLOWED_MIME_TYPES = {"application/pdf"}
CHUNK_SIZE = 1024 * 1024
REQUEST_TOO_LARGE_STATUS = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
UNPROCESSABLE_STATUS = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


def create_media_asset(db: Session, file: UploadFile, current_user: User, alt_text: str | None = None) -> MediaAsset:
    content_type = file.content_type or "application/octet-stream"
    if not _is_allowed_mime_type(content_type):
        raise HTTPException(status_code=UNPROCESSABLE_STATUS, detail="Unsupported media MIME type")

    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    upload_file, size_bytes = _validated_file(file, max_bytes)

    try:
        original_filename = file.filename or "upload"
        storage_key = _storage_key(current_user.organization_id, original_filename)
        storage.upload_file(upload_file, storage_key, content_type)

        asset = MediaAsset(
            organization_id=current_user.organization_id,
            uploaded_by=current_user.id,
            storage_key=storage_key,
            original_filename=original_filename,
            mime_type=content_type,
            size_bytes=size_bytes,
            visibility="private",
            alt_text=alt_text,
        )
        db.add(asset)
        try:
            db.commit()
            db.refresh(asset)
        except Exception:
            db.rollback()
            storage.delete_file(storage_key)
            raise
        return asset
    finally:
        upload_file.close()


def list_media_assets(db: Session, current_user: User) -> list[MediaAsset]:
    query = select(MediaAsset).order_by(MediaAsset.created_at.desc(), MediaAsset.id.desc())
    if current_user.role != "super_admin":
        query = query.where(MediaAsset.organization_id == current_user.organization_id)
    return db.scalars(query).all()


def get_media_asset_url(
    db: Session,
    asset_id: int,
    current_user: User,
    expires_seconds: int = 3600,
) -> str:
    asset = db.get(MediaAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    if current_user.role != "super_admin" and asset.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    return storage.get_file_url(asset.storage_key)


def _is_allowed_mime_type(content_type: str) -> bool:
    return content_type in ALLOWED_MIME_TYPES or content_type.startswith(ALLOWED_MIME_PREFIXES)


def _validated_file(file: UploadFile, max_bytes: int):
    size_bytes = 0
    output = SpooledTemporaryFile(max_size=CHUNK_SIZE, mode="w+b")
    while True:
        chunk = file.file.read(CHUNK_SIZE)
        if not chunk:
            break
        size_bytes += len(chunk)
        if size_bytes > max_bytes:
            output.close()
            raise HTTPException(status_code=REQUEST_TOO_LARGE_STATUS, detail="Uploaded file is too large")
        output.write(chunk)
    output.seek(0)
    return output, size_bytes


def _storage_key(organization_id: int | None, filename: str) -> str:
    safe_filename = _safe_filename(filename)
    org_part = organization_id if organization_id is not None else "global"
    return f"media/{org_part}/{uuid4()}-{safe_filename}"


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "upload"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._") or "upload"
