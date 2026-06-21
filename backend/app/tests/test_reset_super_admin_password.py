from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.modules.organizations.models import Organization
from app.modules.users.models import User
from scripts.reset_super_admin_password import reset_super_admin_password


def test_reset_super_admin_password_updates_matching_super_admin(db_session):
    organization = Organization(name="Platform", type="platform")
    db_session.add(organization)
    db_session.flush()
    user = User(
        organization_id=organization.id,
        email="admin@example.com",
        username="super-admin",
        hashed_password=hash_password("old-password"),
        full_name="Super Admin",
        role="super_admin",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    reset_super_admin_password(db_session, "admin@example.com", "new-password")

    updated = db_session.scalar(select(User).where(User.email == "admin@example.com"))
    assert verify_password("new-password", updated.hashed_password)
    assert updated.is_active is True
