from app.core.security import hash_password
from app.modules.organizations.models import Organization
from app.modules.users.models import User


def create_org(db_session, name="Test School"):
    organization = Organization(name=name, type="school")
    db_session.add(organization)
    db_session.flush()
    return organization


def create_user(db_session, organization, **overrides):
    password = overrides.pop("password", None)
    hashed_password = overrides.pop("hashed_password", None)
    if hashed_password is None:
        hashed_password = hash_password(password)

    user = User(
        organization_id=organization.id,
        email=overrides.pop("email", None),
        username=overrides.pop("username"),
        hashed_password=hashed_password,
        full_name=overrides.pop("full_name"),
        role=overrides.pop("role"),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_student_can_login_with_username(client, db_session):
    organization = create_org(db_session)
    user = create_user(
        db_session,
        organization,
        username="student-one",
        email="student@example.com",
        password="student-pass",
        full_name="Student One",
        role="student",
    )

    response = client.post(
        "/api/auth/login",
        json={"identifier": "student-one", "password": "student-pass"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["user"] == {
        "id": user.id,
        "name": "Student One",
        "email": "student@example.com",
        "username": "student-one",
        "role": "student",
        "organization_id": organization.id,
    }


def test_teacher_can_login_with_email(client, db_session):
    organization = create_org(db_session)
    user = create_user(
        db_session,
        organization,
        username="teacher-one",
        email="teacher@example.com",
        password="teacher-pass",
        full_name="Teacher One",
        role="teacher",
    )

    response = client.post(
        "/api/auth/login",
        json={"identifier": "TEACHER@EXAMPLE.COM", "password": "teacher-pass"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == user.id


def test_invalid_password_rejected(client, db_session):
    organization = create_org(db_session)
    create_user(
        db_session,
        organization,
        username="student-two",
        email="student2@example.com",
        password="student-pass",
        full_name="Student Two",
        role="student",
    )

    response = client.post(
        "/api/auth/login",
        json={"identifier": "student-two", "password": "wrong-pass"},
    )

    assert response.status_code == 401


def test_duplicate_username_across_organizations_rejected(client, db_session):
    first_org = create_org(db_session, name="First School")
    second_org = create_org(db_session, name="Second School")
    create_user(
        db_session,
        first_org,
        username="shared-student",
        email="shared1@example.com",
        password="student-pass",
        full_name="Shared Student One",
        role="student",
    )
    create_user(
        db_session,
        second_org,
        username="shared-student",
        email="shared2@example.com",
        password="student-pass",
        full_name="Shared Student Two",
        role="student",
    )

    response = client.post(
        "/api/auth/login",
        json={"identifier": "shared-student", "password": "student-pass"},
    )

    assert response.status_code == 401


def test_malformed_stored_password_hash_rejected(client, db_session):
    organization = create_org(db_session)
    create_user(
        db_session,
        organization,
        username="bad-hash",
        email="bad-hash@example.com",
        hashed_password="not-a-bcrypt-hash",
        full_name="Bad Hash",
        role="student",
    )

    response = client.post(
        "/api/auth/login",
        json={"identifier": "bad-hash", "password": "student-pass"},
    )

    assert response.status_code == 401
