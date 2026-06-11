from datetime import datetime, timezone

import pytest
from botocore.exceptions import EndpointConnectionError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.modules.media.models import MediaAsset
from app.modules.organizations.models import Organization
from app.modules.subscriptions.models import Plan, Subscription
from app.modules.users.models import User


def auth_headers(user):
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


def create_org(db_session, name="Media School"):
    organization = Organization(name=name, type="school")
    db_session.add(organization)
    db_session.flush()
    return organization


def create_user(db_session, organization, role, username):
    user = User(
        organization_id=organization.id,
        email=f"{username}@example.com",
        username=username,
        hashed_password=hash_password("password"),
        full_name=username.replace("-", " ").title(),
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def add_active_subscription(db_session, organization):
    plan = Plan(name="School Plan", slug="school-plan")
    db_session.add(plan)
    db_session.flush()
    subscription = Subscription(
        organization_id=organization.id,
        plan_id=plan.id,
        status="active",
        starts_at=datetime.now(timezone.utc),
    )
    db_session.add(subscription)
    db_session.flush()
    return subscription


def test_content_admin_can_upload_media(client, db_session, monkeypatch):
    from app.modules.media import service

    uploaded = {}

    def fake_upload_file(file_obj, key, content_type):
        uploaded["key"] = key
        uploaded["content_type"] = content_type
        uploaded["body"] = file_obj.read()

    monkeypatch.setattr(service.storage, "upload_file", fake_upload_file)
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin")

    response = client.post(
        "/api/admin/media",
        files={"file": ("Lesson Image.JPG", b"image-bytes", "image/jpeg")},
        data={"alt_text": "Krishna and Arjuna"},
        headers=auth_headers(admin),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["organization_id"] == organization.id
    assert payload["uploaded_by"] == admin.id
    assert payload["original_filename"] == "Lesson Image.JPG"
    assert payload["mime_type"] == "image/jpeg"
    assert payload["size_bytes"] == len(b"image-bytes")
    assert payload["visibility"] == "private"
    assert payload["alt_text"] == "Krishna and Arjuna"
    assert payload["storage_key"].endswith("-Lesson_Image.JPG")
    assert uploaded["key"] == payload["storage_key"]
    assert uploaded["content_type"] == "image/jpeg"
    assert uploaded["body"] == b"image-bytes"


def test_upload_rejects_unsupported_mime_type(client, db_session, monkeypatch):
    from app.modules.media import service

    called = False

    def fake_upload_file(file_obj, key, content_type):
        nonlocal called
        called = True

    monkeypatch.setattr(service.storage, "upload_file", fake_upload_file)
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin")

    response = client.post(
        "/api/admin/media",
        files={"file": ("notes.txt", b"plain text", "text/plain")},
        headers=auth_headers(admin),
    )

    assert response.status_code == 422
    assert called is False


def test_upload_rejects_oversized_file_without_calling_storage(client, db_session, monkeypatch):
    from app.modules.media import service

    called = False

    def fake_upload_file(file_obj, key, content_type):
        nonlocal called
        called = True

    monkeypatch.setattr(service.storage, "upload_file", fake_upload_file)
    monkeypatch.setattr(get_settings(), "max_upload_mb", 0)
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin")

    response = client.post(
        "/api/admin/media",
        files={"file": ("large.png", b"x", "image/png")},
        headers=auth_headers(admin),
    )

    assert response.status_code == 413
    assert called is False


def test_upload_returns_503_when_storage_is_unavailable(client, db_session, monkeypatch):
    from app.modules.media import service

    def fake_upload_file(file_obj, key, content_type):
        raise EndpointConnectionError(endpoint_url="http://127.0.0.1:9000")

    monkeypatch.setattr(service.storage, "upload_file", fake_upload_file)
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin")

    response = client.post(
        "/api/admin/media",
        files={"file": ("asset.png", b"image-bytes", "image/png")},
        headers=auth_headers(admin),
    )

    assert response.status_code == 503
    assert response.json()["detail"].startswith("Media storage is unavailable")


def test_upload_deletes_storage_object_when_db_commit_fails(db_session, monkeypatch):
    from app.modules.media import service

    uploaded = {}
    deleted = []

    def fake_upload_file(file_obj, key, content_type):
        uploaded["key"] = key
        uploaded["body"] = file_obj.read()

    def fake_commit():
        raise SQLAlchemyError("commit failed")

    monkeypatch.setattr(service.storage, "upload_file", fake_upload_file)
    monkeypatch.setattr(service.storage, "delete_file", lambda key: deleted.append(key))
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin")
    monkeypatch.setattr(db_session, "commit", fake_commit)

    with pytest.raises(SQLAlchemyError, match="commit failed"):
        service.create_media_asset(db_session, _Upload("asset.png", b"image-bytes", "image/png"), admin)

    assert uploaded["body"] == b"image-bytes"
    assert deleted == [uploaded["key"]]


def test_upload_closes_validated_file_after_success(db_session, monkeypatch):
    from app.modules.media import service

    uploaded = {}

    def fake_upload_file(file_obj, key, content_type):
        uploaded["file_obj"] = file_obj

    monkeypatch.setattr(service.storage, "upload_file", fake_upload_file)
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin")

    service.create_media_asset(db_session, _Upload("asset.png", b"image-bytes", "image/png"), admin)

    assert uploaded["file_obj"].closed is True


def test_content_admin_can_list_media(client, db_session):
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin")
    other_org = create_org(db_session, name="Other School")
    other_admin = create_user(db_session, other_org, "content_admin", "other-admin")
    asset = MediaAsset(
        organization_id=organization.id,
        uploaded_by=admin.id,
        storage_key="media/asset.png",
        original_filename="asset.png",
        mime_type="image/png",
        size_bytes=12,
    )
    other_asset = MediaAsset(
        organization_id=other_org.id,
        uploaded_by=other_admin.id,
        storage_key="media/other.png",
        original_filename="other.png",
        mime_type="image/png",
        size_bytes=15,
    )
    db_session.add_all([asset, other_asset])
    db_session.commit()

    response = client.get("/api/admin/media", headers=auth_headers(admin))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [asset.id]


def test_learning_user_can_get_media_signed_url(client, db_session, monkeypatch):
    from app.modules.media import service

    monkeypatch.setattr(service.storage, "get_presigned_url", lambda key, expires_seconds=3600: f"https://cdn.test/{key}")
    organization = create_org(db_session)
    student = create_user(db_session, organization, "student", "student-one")
    add_active_subscription(db_session, organization)
    asset = MediaAsset(
        organization_id=organization.id,
        uploaded_by=student.id,
        storage_key="media/lesson-audio.mp3",
        original_filename="lesson-audio.mp3",
        mime_type="audio/mpeg",
        size_bytes=20,
    )
    db_session.add(asset)
    db_session.commit()

    response = client.get(f"/api/media/{asset.id}/url", headers=auth_headers(student))

    assert response.status_code == 200
    assert response.json() == {"url": "https://cdn.test/media/lesson-audio.mp3", "expires_seconds": 3600}


class _Upload:
    def __init__(self, filename, body, content_type):
        from io import BytesIO

        self.filename = filename
        self.file = BytesIO(body)
        self.content_type = content_type
