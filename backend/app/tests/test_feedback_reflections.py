from datetime import datetime, timezone

from app.core.security import create_access_token, hash_password
from app.modules.content.models import Chapter, ChapterVersion, Concept, Exhibit
from app.modules.feedback.models import Feedback
from app.modules.organizations.models import Organization
from app.modules.reflections.models import Reflection
from app.modules.subscriptions.models import Plan, Subscription
from app.modules.users.models import User


def auth_headers(user):
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


def create_org(db_session, name="Learning School"):
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
    plan = Plan(name=f"{organization.name} Plan", slug=f"{organization.id}-school-plan")
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


def create_learning_content(db_session, *, status="published", slug_suffix="one"):
    chapter = Chapter(title=f"Chapter {slug_suffix}", slug=f"chapter-{slug_suffix}", sort_order=1)
    db_session.add(chapter)
    db_session.flush()
    version = ChapterVersion(
        chapter_id=chapter.id,
        version_number=1,
        status=status,
        title=f"Chapter {slug_suffix}",
        published_at=datetime.now(timezone.utc) if status == "published" else None,
    )
    db_session.add(version)
    db_session.flush()
    concept = Concept(
        chapter_version_id=version.id,
        title=f"Concept {slug_suffix}",
        slug=f"concept-{slug_suffix}",
        sort_order=1,
    )
    db_session.add(concept)
    db_session.flush()
    exhibit = Exhibit(
        chapter_version_id=version.id,
        concept_id=concept.id,
        title=f"Exhibit {slug_suffix}",
        field_type="html",
        content="<p>Exhibit</p>",
        sort_order=1,
    )
    db_session.add(exhibit)
    db_session.commit()
    return chapter, version, concept, exhibit


def test_student_can_submit_content_feedback(client, db_session):
    organization = create_org(db_session)
    student = create_user(db_session, organization, "student", "student-one")
    add_active_subscription(db_session, organization)
    chapter, _, concept, _ = create_learning_content(db_session, slug_suffix="two")

    response = client.post(
        "/api/feedback",
        json={
            "scope_type": "concept",
            "scope_id": concept.id,
            "category": "content",
            "rating": 4,
            "comment": "  The concept explanation is clear.  ",
        },
        headers=auth_headers(student),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["user_id"] == student.id
    assert payload["scope_type"] == "concept"
    assert payload["scope_id"] == concept.id
    assert payload["concept_id"] == concept.id
    assert payload["chapter_id"] == chapter.id
    assert payload["category"] == "content"
    assert payload["rating"] == 4
    assert payload["comment"] == "The concept explanation is clear."
    assert payload["status"] == "open"


def test_feedback_rejects_draft_concept_scope(client, db_session):
    organization = create_org(db_session)
    student = create_user(db_session, organization, "student", "student-draft-feedback")
    add_active_subscription(db_session, organization)
    _, _, concept, _ = create_learning_content(db_session, status="draft", slug_suffix="draft")

    response = client.post(
        "/api/feedback",
        json={
            "scope_type": "concept",
            "scope_id": concept.id,
            "category": "content",
            "rating": 3,
            "comment": "Draft content should not accept feedback.",
        },
        headers=auth_headers(student),
    )

    assert response.status_code == 404


def test_content_admin_sees_org_feedback_and_super_admin_sees_all(client, db_session):
    organization = create_org(db_session)
    other_organization = create_org(db_session, name="Other School")
    admin = create_user(db_session, organization, "content_admin", "content-admin")
    super_admin = create_user(db_session, organization, "super_admin", "super-admin")
    student = create_user(db_session, organization, "student", "student-one")
    other_student = create_user(db_session, other_organization, "student", "student-two")
    db_session.add_all(
        [
            Feedback(user_id=student.id, scope_type="app", comment="Own org feedback"),
            Feedback(user_id=other_student.id, scope_type="app", comment="Other org feedback"),
        ]
    )
    db_session.commit()

    admin_response = client.get("/api/admin/feedback", headers=auth_headers(admin))
    super_response = client.get("/api/admin/feedback", headers=auth_headers(super_admin))

    assert admin_response.status_code == 200
    assert [item["comment"] for item in admin_response.json()] == ["Own org feedback"]
    assert super_response.status_code == 200
    assert {item["comment"] for item in super_response.json()} == {"Own org feedback", "Other org feedback"}


def test_private_reflection_visible_only_to_owner(client, db_session):
    organization = create_org(db_session)
    owner = create_user(db_session, organization, "student", "student-one")
    other_user = create_user(db_session, organization, "teacher", "teacher-one")
    add_active_subscription(db_session, organization)

    create_response = client.post(
        "/api/reflections",
        json={"visibility": "private", "body": "  My private reflection.  "},
        headers=auth_headers(owner),
    )

    assert create_response.status_code == 201
    reflection_id = create_response.json()["id"]
    assert create_response.json()["user_id"] == owner.id
    assert create_response.json()["visibility"] == "private"
    assert create_response.json()["body"] == "My private reflection."
    assert create_response.json()["submitted_at"] is None

    owner_list_response = client.get("/api/reflections", headers=auth_headers(owner))
    owner_detail_response = client.get(f"/api/reflections/{reflection_id}", headers=auth_headers(owner))
    other_list_response = client.get("/api/reflections", headers=auth_headers(other_user))
    other_detail_response = client.get(f"/api/reflections/{reflection_id}", headers=auth_headers(other_user))

    assert owner_list_response.status_code == 200
    assert [item["id"] for item in owner_list_response.json()] == [reflection_id]
    assert owner_detail_response.status_code == 200
    assert owner_detail_response.json()["id"] == reflection_id
    assert other_list_response.status_code == 200
    assert other_list_response.json() == []
    assert other_detail_response.status_code == 404


def test_reflection_rejects_mismatched_chapter_and_concept_references(client, db_session):
    organization = create_org(db_session)
    student = create_user(db_session, organization, "student", "student-mismatch")
    add_active_subscription(db_session, organization)
    chapter, _, _, _ = create_learning_content(db_session, slug_suffix="alpha")
    _, _, other_concept, _ = create_learning_content(db_session, slug_suffix="beta")

    response = client.post(
        "/api/reflections",
        json={
            "chapter_id": chapter.id,
            "concept_id": other_concept.id,
            "visibility": "private",
            "body": "This reference combination is invalid.",
        },
        headers=auth_headers(student),
    )

    assert response.status_code == 400


def test_reflection_with_content_reference_uses_canonical_fields(client, db_session):
    organization = create_org(db_session)
    student = create_user(db_session, organization, "student", "student-canonical")
    add_active_subscription(db_session, organization)
    chapter, _, concept, exhibit = create_learning_content(db_session, slug_suffix="canonical")

    concept_response = client.post(
        "/api/reflections",
        json={"concept_id": concept.id, "visibility": "private", "body": "Concept-level reflection."},
        headers=auth_headers(student),
    )
    exhibit_response = client.post(
        "/api/reflections",
        json={"exhibit_id": exhibit.id, "visibility": "private", "body": "Exhibit-level reflection."},
        headers=auth_headers(student),
    )

    assert concept_response.status_code == 201
    assert concept_response.json()["chapter_id"] == chapter.id
    assert concept_response.json()["concept_id"] == concept.id
    assert concept_response.json()["exhibit_id"] is None
    assert exhibit_response.status_code == 201
    assert exhibit_response.json()["chapter_id"] == chapter.id
    assert exhibit_response.json()["concept_id"] == concept.id
    assert exhibit_response.json()["exhibit_id"] == exhibit.id


def test_super_admin_can_read_submitted_reflection_but_not_private(client, db_session):
    organization = create_org(db_session)
    owner = create_user(db_session, organization, "student", "student-one")
    super_admin = create_user(db_session, organization, "super_admin", "super-admin-reflections")
    private = Reflection(user_id=owner.id, visibility="private", body="Private reflection")
    submitted = Reflection(
        user_id=owner.id,
        visibility="submitted",
        body="Submitted reflection",
        submitted_at=datetime.now(timezone.utc),
    )
    db_session.add_all([private, submitted])
    db_session.commit()

    private_response = client.get(f"/api/reflections/{private.id}", headers=auth_headers(super_admin))
    submitted_response = client.get(f"/api/reflections/{submitted.id}", headers=auth_headers(super_admin))

    assert private_response.status_code == 404
    assert submitted_response.status_code == 200
    assert submitted_response.json()["id"] == submitted.id
