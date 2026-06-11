from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import require_content_admin, require_platform_admin
from app.db.session import get_db
from app.modules.subscriptions import service
from app.modules.subscriptions.models import Subscription
from app.modules.subscriptions.schemas import SubscriptionRead, SubscriptionUpdate
from app.modules.users.models import User


router = APIRouter(prefix="/api/admin/subscriptions")


@router.get("", response_model=list[SubscriptionRead])
def get_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_admin),
) -> list[SubscriptionRead]:
    return [_subscription_read(item) for item in service.list_subscriptions(db, current_user)]


@router.put("/{subscription_id}", response_model=SubscriptionRead)
def put_subscription(
    subscription_id: int,
    payload: SubscriptionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin),
) -> SubscriptionRead:
    return _subscription_read(service.update_subscription(db, subscription_id, payload))


def _subscription_read(subscription: Subscription) -> SubscriptionRead:
    return SubscriptionRead(
        id=subscription.id,
        organization_id=subscription.organization_id,
        organization_name=subscription.organization.name if subscription.organization else None,
        plan_id=subscription.plan_id,
        plan_name=subscription.plan.name if subscription.plan else None,
        status=subscription.status,
        starts_at=subscription.starts_at,
        expires_at=subscription.expires_at,
        grace_until=subscription.grace_until,
        contract_notes=subscription.contract_notes,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )
