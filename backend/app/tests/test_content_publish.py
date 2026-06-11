from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.security import create_access_token, hash_password
from app.modules.content.models import Chapter, ChapterVersion
from app.modules.curriculum.models import CurriculumPhase
from app.modules.organizations.models import Organization
from app.modules.subscriptions.models import Plan, Subscription
from app.modules.users.models import User


def auth_headers(user):
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


def create_org(db_session):
    organization = Organization(name="Learning School", type="school")
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


def create_chapter_with_published_and_draft(db_session):
    phase = CurriculumPhase(name="Foundation", slug="foundation", sort_order=1)
    db_session.add(phase)
    db_session.flush()
    chapter = Chapter(
        curriculum_phase_id=phase.id,
        title="Chapter 1",
        slug="chapter-1",
        sort_order=1,
    )
    db_session.add(chapter)
    db_session.flush()
    published = ChapterVersion(
        chapter_id=chapter.id,
        version_number=1,
        status="published",
        title="Published Title",
        summary="<p>Published summary</p>",
        body="<p>Published body</p>",
        published_at=datetime.now(timezone.utc),
    )
    draft = ChapterVersion(
        chapter_id=chapter.id,
        version_number=2,
        status="draft",
        title="Draft Title",
        summary="<p>Draft summary</p>",
        body="<p>Draft body</p>",
    )
    db_session.add_all([published, draft])
    db_session.commit()
    return chapter, published, draft


def test_learning_api_returns_published_version_only_not_draft(client, db_session):
    organization = create_org(db_session)
    student = create_user(db_session, organization, "student", "student-one")
    add_active_subscription(db_session, organization)
    chapter, published, draft = create_chapter_with_published_and_draft(db_session)

    list_response = client.get("/api/learning/chapters", headers=auth_headers(student))
    detail_response = client.get(f"/api/learning/chapters/{chapter.id}", headers=auth_headers(student))

    assert list_response.status_code == 200
    assert list_response.json() == [
        {
            "id": chapter.id,
            "curriculum_phase_id": chapter.curriculum_phase_id,
            "title": published.title,
            "summary": published.summary,
            "sort_order": chapter.sort_order,
            "status": "published",
            "version_id": published.id,
        }
    ]
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["title"] == "Published Title"
    assert detail["version_id"] == published.id
    assert detail["version_title"] == "Published Title"
    assert detail["body"] == "<p>Published body</p>"
    assert detail["version_id"] != draft.id


def test_content_admin_can_publish_draft_and_learning_content_stays_stable_until_publish(client, db_session):
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin")
    student = create_user(db_session, organization, "student", "student-two")
    add_active_subscription(db_session, organization)
    chapter, published, draft = create_chapter_with_published_and_draft(db_session)

    update_response = client.put(
        f"/api/admin/content/chapter-versions/{draft.id}",
        json={"title": "Edited Draft", "summary": "<p>Edited draft</p>", "body": "<p>Edited body</p>"},
        headers=auth_headers(admin),
    )
    before_publish_response = client.get(f"/api/learning/chapters/{chapter.id}", headers=auth_headers(student))
    publish_response = client.post(
        f"/api/admin/content/chapter-versions/{draft.id}/publish",
        headers=auth_headers(admin),
    )
    after_publish_response = client.get(f"/api/learning/chapters/{chapter.id}", headers=auth_headers(student))

    assert update_response.status_code == 200
    assert before_publish_response.status_code == 200
    assert before_publish_response.json()["version_id"] == published.id
    assert before_publish_response.json()["title"] == "Published Title"
    assert before_publish_response.json()["version_title"] == "Published Title"
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"
    assert after_publish_response.status_code == 200
    assert after_publish_response.json()["version_id"] == draft.id
    assert after_publish_response.json()["title"] == "Edited Draft"
    assert after_publish_response.json()["version_title"] == "Edited Draft"
    db_session.refresh(published)
    assert published.status == "archived"


def test_content_admin_cannot_publish_already_published_or_archived_version(client, db_session):
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin-reject")
    _, published, _ = create_chapter_with_published_and_draft(db_session)
    archived = ChapterVersion(
        chapter_id=published.chapter_id,
        version_number=3,
        status="archived",
        title="Archived Title",
        summary="<p>Archived summary</p>",
        body="<p>Archived body</p>",
    )
    db_session.add(archived)
    db_session.commit()

    published_response = client.post(
        f"/api/admin/content/chapter-versions/{published.id}/publish",
        headers=auth_headers(admin),
    )
    archived_response = client.post(
        f"/api/admin/content/chapter-versions/{archived.id}/publish",
        headers=auth_headers(admin),
    )

    assert published_response.status_code == 400
    assert archived_response.status_code == 400
    assert "draft" in published_response.json()["detail"]
    assert "draft" in archived_response.json()["detail"]


def test_only_one_published_version_remains_after_publishing_draft(client, db_session):
    organization = create_org(db_session)
    admin = create_user(db_session, organization, "content_admin", "content-admin-single")
    _, published, draft = create_chapter_with_published_and_draft(db_session)

    response = client.post(
        f"/api/admin/content/chapter-versions/{draft.id}/publish",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert (
        db_session.scalar(
            select(func.count())
            .select_from(ChapterVersion)
            .where(ChapterVersion.chapter_id == draft.chapter_id)
            .where(ChapterVersion.status == "published")
        )
        == 1
    )
    db_session.refresh(published)
    db_session.refresh(draft)
    assert published.status == "archived"
    assert draft.status == "published"
