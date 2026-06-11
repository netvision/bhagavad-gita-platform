from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.permissions import require_learning_access
from app.db.session import get_db
from app.modules.reflections import service
from app.modules.reflections.models import Reflection
from app.modules.reflections.schemas import ReflectionCreate, ReflectionRead
from app.modules.users.models import User


router = APIRouter(prefix="/api/reflections", dependencies=[Depends(require_learning_access)])


@router.post("", response_model=ReflectionRead, status_code=status.HTTP_201_CREATED)
def post_reflection(
    payload: ReflectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_learning_access),
) -> Reflection:
    return service.create_reflection(db, payload, current_user)


@router.get("", response_model=list[ReflectionRead])
def get_reflections(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_learning_access),
) -> list[Reflection]:
    return service.list_user_reflections(db, current_user)


@router.get("/{reflection_id}", response_model=ReflectionRead)
def get_reflection(
    reflection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_learning_access),
) -> Reflection:
    return service.get_visible_reflection(db, reflection_id, current_user)
