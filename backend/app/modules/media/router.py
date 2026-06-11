from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.permissions import require_content_admin, require_learning_access
from app.db.session import get_db
from app.modules.media import service
from app.modules.media.models import MediaAsset
from app.modules.media.schemas import MediaAssetOut, MediaUrlOut
from app.modules.users.models import User


admin_router = APIRouter(prefix="/api/admin/media")
media_router = APIRouter(prefix="/api/media")


@admin_router.post("", response_model=MediaAssetOut, status_code=status.HTTP_201_CREATED)
def post_admin_media(
    file: UploadFile = File(...),
    alt_text: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> MediaAsset:
    return service.create_media_asset(db, file, current_user, alt_text=alt_text)


@admin_router.get("", response_model=list[MediaAssetOut])
def get_admin_media(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> list[MediaAsset]:
    return service.list_media_assets(db, current_user)


@media_router.get("/{asset_id}/url", response_model=MediaUrlOut)
def get_media_url(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_learning_access),
) -> MediaUrlOut:
    expires_seconds = 3600
    return MediaUrlOut(
        url=service.get_media_asset_url(db, asset_id, current_user, expires_seconds=expires_seconds),
        expires_seconds=expires_seconds,
    )
