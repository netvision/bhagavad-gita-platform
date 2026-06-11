from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.permissions import require_content_admin, require_learning_access
from app.db.session import get_db
from app.modules.feedback import service
from app.modules.feedback.models import Feedback
from app.modules.feedback.schemas import FeedbackCreate, FeedbackRead
from app.modules.users.models import User


router = APIRouter(prefix="/api/feedback")
admin_router = APIRouter(prefix="/api/admin/feedback")


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def post_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_learning_access),
) -> Feedback:
    return service.create_feedback(db, payload, current_user)


@admin_router.get("", response_model=list[FeedbackRead])
def get_admin_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> list[Feedback]:
    return service.list_admin_feedback(db, current_user)
