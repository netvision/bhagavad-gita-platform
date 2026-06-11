from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db import models  # noqa: F401
from app.modules.content.importer import ImportResult, import_seed_json
from app.modules.organizations.models import Organization
from app.modules.subscriptions.models import Plan, Subscription
from app.modules.users.models import User


LOCAL_SUPER_ADMIN_EMAIL = "admin@gita.local"
LOCAL_SUPER_ADMIN_PASSWORD = "change-me-local"
LOCAL_CONTENT_ADMIN_EMAIL = "content@gita.local"
LOCAL_CONTENT_ADMIN_PASSWORD = "change-me-local"
ALLOW_LOCAL_SEED_CREDENTIALS = "ALLOW_LOCAL_SEED_CREDENTIALS"
REPLACE_SEED_CONTENT = "REPLACE_SEED_CONTENT"


def seed_initial_data(db: Session) -> ImportResult:
    settings = get_settings()
    platform = _ensure_organization(db, name="Gita Learning Platform", organization_type="platform")
    school = _ensure_organization(db, name="Default School", organization_type="school")
    plan = _ensure_plan(db)
    _ensure_active_subscription(db, school, plan)
    _ensure_super_admin(db, platform, settings.app_env)
    _ensure_content_admin(db, platform, settings.app_env)
    result = import_seed_json(
        db,
        "backend/seed_data/bhagavad_gita_export.json",
        replace_content=_replace_seed_content_enabled(),
    )
    db.commit()
    return result


def _ensure_organization(db: Session, name: str, organization_type: str) -> Organization:
    organization = db.scalar(
        select(Organization).where(
            Organization.name == name,
            Organization.type == organization_type,
        )
    )
    if organization is None:
        organization = Organization(name=name, type=organization_type)
        db.add(organization)
        db.flush()
    return organization


def _ensure_plan(db: Session) -> Plan:
    plan = db.scalar(select(Plan).where(Plan.slug == "default"))
    if plan is None:
        plan = Plan(
            name="Default Plan",
            slug="default",
            description="Default platform access plan.",
        )
        db.add(plan)
        db.flush()
    else:
        plan.name = "Default Plan"
        plan.description = "Default platform access plan."
    return plan


def _ensure_active_subscription(db: Session, organization: Organization, plan: Plan) -> Subscription:
    subscription = db.scalar(
        select(Subscription).where(
            Subscription.organization_id == organization.id,
            Subscription.plan_id == plan.id,
        )
    )
    if subscription is None:
        subscription = Subscription(
            organization_id=organization.id,
            plan_id=plan.id,
            status="active",
            starts_at=datetime.now(timezone.utc),
            contract_notes="Seeded default subscription.",
        )
        db.add(subscription)
        db.flush()
    else:
        subscription.status = "active"
        subscription.starts_at = subscription.starts_at or datetime.now(timezone.utc)
    return subscription


def _ensure_super_admin(db: Session, organization: Organization, app_env: str) -> User:
    email, password = _admin_credentials(
        app_env=app_env,
        email_env="SUPER_ADMIN_EMAIL",
        password_env="SUPER_ADMIN_PASSWORD",
        local_email=LOCAL_SUPER_ADMIN_EMAIL,
        local_password=LOCAL_SUPER_ADMIN_PASSWORD,
        required_label="super admin",
    )
    return _ensure_admin_user(
        db,
        organization=organization,
        email=email,
        password=password,
        username="super-admin",
        full_name="Super Admin",
        role="super_admin",
    )


def _ensure_content_admin(db: Session, organization: Organization, app_env: str) -> User | None:
    email = os.getenv("CONTENT_ADMIN_EMAIL")
    password = os.getenv("CONTENT_ADMIN_PASSWORD")
    allow_local_credentials = _local_seed_credentials_allowed()
    if not email and not password and app_env.lower() == "production":
        return None
    if not email and not password and not allow_local_credentials:
        return None

    email, password = _admin_credentials(
        app_env=app_env,
        email_env="CONTENT_ADMIN_EMAIL",
        password_env="CONTENT_ADMIN_PASSWORD",
        local_email=LOCAL_CONTENT_ADMIN_EMAIL,
        local_password=LOCAL_CONTENT_ADMIN_PASSWORD,
        required_label="content admin",
    )
    return _ensure_admin_user(
        db,
        organization=organization,
        email=email,
        password=password,
        username="content-admin",
        full_name="Content Admin",
        role="content_admin",
    )


def _admin_credentials(
    *,
    app_env: str,
    email_env: str,
    password_env: str,
    local_email: str,
    local_password: str,
    required_label: str,
) -> tuple[str, str]:
    email = os.getenv(email_env)
    password = os.getenv(password_env)
    is_production = app_env.lower() == "production"
    allow_local_credentials = _local_seed_credentials_allowed()
    if is_production and (not email or not password):
        raise RuntimeError(f"{email_env} and {password_env} are required to seed the {required_label} in production")
    if is_production and password == local_password:
        raise RuntimeError(f"{password_env} must not use the local development default in production")
    if email or password:
        if not email or not password:
            raise RuntimeError(f"{email_env} and {password_env} must be provided together")
        return email, password
    if not allow_local_credentials:
        raise RuntimeError(
            f"{email_env} and {password_env} are required, or set "
            f"{ALLOW_LOCAL_SEED_CREDENTIALS}=true to use local development seed credentials"
        )
    return local_email, local_password


def _local_seed_credentials_allowed() -> bool:
    return os.getenv(ALLOW_LOCAL_SEED_CREDENTIALS, "").strip().lower() == "true"


def _replace_seed_content_enabled() -> bool:
    return os.getenv(REPLACE_SEED_CONTENT, "").strip().lower() == "true"


def _ensure_admin_user(
    db: Session,
    *,
    organization: Organization,
    email: str,
    password: str,
    username: str,
    full_name: str,
    role: str,
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            organization_id=organization.id,
            email=email,
            username=username,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        user.organization_id = organization.id
        user.username = username
        user.full_name = full_name
        user.role = role
        user.is_active = True
        if not user.hashed_password:
            user.hashed_password = hash_password(password)
    return user
