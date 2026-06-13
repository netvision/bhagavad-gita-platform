import secrets
import string

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.modules.organizations.models import Organization
from app.modules.users.models import User
from app.modules.users.schemas import UserActiveUpdate, UserCreate, UserUpdate


def list_users(db: Session, current_user: User) -> list[User]:
    query = select(User).options(selectinload(User.organization)).order_by(User.role, User.full_name, User.username)
    if current_user.role != "super_admin":
        query = query.where(User.organization_id == current_user.organization_id)
    return db.scalars(query).all()


def create_user(db: Session, payload: UserCreate, current_user: User) -> User:
    _validate_scope(payload.organization_id, current_user)
    user = User(
        organization_id=payload.organization_id,
        email=str(payload.email).lower() if payload.email else None,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        grade_label=payload.grade_label,
        section_label=payload.section_label,
        is_active=payload.is_active,
    )
    db.add(user)
    return _commit_user(db, user)


def update_user(db: Session, user_id: int, payload: UserUpdate, current_user: User) -> User:
    user = _get_user(db, user_id, current_user)
    organization_id = payload.organization_id or user.organization_id
    _validate_scope(organization_id, current_user)
    user.organization_id = organization_id
    user.email = str(payload.email).lower() if payload.email else None
    user.username = payload.username
    user.full_name = payload.full_name
    user.role = payload.role
    user.grade_label = payload.grade_label
    user.section_label = payload.section_label
    user.is_active = payload.is_active
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    return _commit_user(db, user)


def update_active(db: Session, user_id: int, payload: UserActiveUpdate, current_user: User) -> User:
    user = _get_user(db, user_id, current_user)
    user.is_active = payload.is_active
    return _commit_user(db, user)


def reset_password_token(db: Session, user_id: int, current_user: User) -> tuple[User, str]:
    user = _get_user(db, user_id, current_user)
    temporary_password = _temporary_password()
    user.hashed_password = hash_password(temporary_password)
    return _commit_user(db, user), temporary_password


def _get_user(db: Session, user_id: int, current_user: User) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _validate_scope(user.organization_id, current_user)
    return user


def _validate_scope(organization_id: int, current_user: User) -> None:
    if current_user.role != "super_admin" and organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot manage users outside organization")


def _commit_user(db: Session, user: User) -> User:
    organization_exists = db.get(Organization, user.organization_id)
    if organization_exists is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization not found")
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists") from exc
    db.refresh(user)
    return user


def _temporary_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(14))
