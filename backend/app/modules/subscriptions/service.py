from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.subscriptions.models import Subscription
from app.modules.subscriptions.schemas import SubscriptionUpdate
from app.modules.users.models import User


def list_subscriptions(db: Session, current_user: User) -> list[Subscription]:
    query = (
        select(Subscription)
        .options(selectinload(Subscription.organization), selectinload(Subscription.plan))
        .order_by(Subscription.updated_at.desc())
    )
    if current_user.role != "super_admin":
        query = query.where(Subscription.organization_id == current_user.organization_id)
    return db.scalars(query).all()


def update_subscription(db: Session, subscription_id: int, payload: SubscriptionUpdate) -> Subscription:
    subscription = db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    subscription.status = payload.status
    subscription.starts_at = payload.starts_at
    subscription.expires_at = payload.expires_at
    subscription.grace_until = payload.grace_until
    subscription.contract_notes = payload.contract_notes
    db.commit()
    db.refresh(subscription)
    return subscription
