from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.modules.auth.schemas import LoginResponse, UserSummary
from app.modules.users.models import User


def authenticate_user(db: Session, identifier: str, password: str) -> LoginResponse:
    identifier = identifier.strip()
    if "@" in identifier:
        user = db.scalar(select(User).where(func.lower(User.email) == identifier.lower()).limit(1))
    else:
        username_matches = db.scalars(select(User).where(User.username == identifier).order_by(User.id).limit(2)).all()
        user = username_matches[0] if len(username_matches) == 1 else None

    if user is None or not user.is_active or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return LoginResponse(
        access_token=create_access_token(str(user.id)),
        token_type="bearer",
        user=UserSummary(
            id=user.id,
            name=user.full_name,
            email=user.email,
            username=user.username,
            role=user.role,
            organization_id=user.organization_id,
        ),
    )
