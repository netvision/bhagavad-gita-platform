from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


SubscriptionStatus = Literal["active", "grace", "expired", "suspended"]


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    organization_name: str | None = None
    plan_id: int
    plan_name: str | None = None
    status: str
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    grace_until: datetime | None = None
    contract_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SubscriptionUpdate(BaseModel):
    status: SubscriptionStatus
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    grace_until: datetime | None = None
    contract_notes: str | None = None
