from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.permissions import require_content_admin
from app.db.session import get_db
from app.modules.users import service
from app.modules.users.models import User
from app.modules.users.schemas import (
    PasswordResetTokenRead,
    UserActiveUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)


router = APIRouter(prefix="/api/admin/users", dependencies=[Depends(require_content_admin)])


@router.get("", response_model=list[UserRead])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> list[UserRead]:
    return [_user_read(user) for user in service.list_users(db, current_user)]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def post_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> UserRead:
    return _user_read(service.create_user(db, payload, current_user))


@router.put("/{user_id}", response_model=UserRead)
def put_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> UserRead:
    return _user_read(service.update_user(db, user_id, payload, current_user))


@router.post("/{user_id}/reset-password-token", response_model=PasswordResetTokenRead)
def post_reset_password_token(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> PasswordResetTokenRead:
    user, temporary_password = service.reset_password_token(db, user_id, current_user)
    return PasswordResetTokenRead(user_id=user.id, temporary_password=temporary_password)


@router.put("/{user_id}/active", response_model=UserRead)
def put_user_active(
    user_id: int,
    payload: UserActiveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> UserRead:
    return _user_read(service.update_active(db, user_id, payload, current_user))


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        organization_id=user.organization_id,
        organization_name=user.organization.name if user.organization else None,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        grade_label=user.grade_label,
        section_label=user.section_label,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
