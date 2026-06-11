# Gita Learning Platform Milestone 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the current prototype into a production-grade one-school Gita Learning platform with PostgreSQL, role-based auth, versioned curriculum content, media storage, feedback/reflections, and a professional Vue application.

**Architecture:** Replace the prototype shape with a modular FastAPI backend and routed Vue frontend. PostgreSQL is the source of truth, Alembic owns schema changes, MinIO stores media, and the UI is split into learning and admin application areas.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic, python-jose/passlib or bcrypt, bleach, boto3 or minio client, Vue 3, Vite, Vue Router, Pinia, TipTap, Vitest, pytest.

---

## Scope and Execution Notes

This plan implements Milestone 1 from [the approved design spec](../specs/2026-06-09-gita-learning-platform-design.md).

This workspace is currently not a Git repository. If Git is initialized before execution, commit after each task. If not, record completed tasks in this plan and keep verification output in the assistant response.

The existing prototype can be replaced rather than preserved. Preserve only the seed JSON and useful import knowledge.

## Target File Structure

Create or reshape files toward this structure:

```text
backend/
  alembic.ini
  app/
    main.py
    core/
      config.py
      security.py
      permissions.py
      sanitizer.py
      storage.py
    db/
      base.py
      session.py
      seed.py
    modules/
      auth/
        router.py
        schemas.py
        service.py
      users/
        models.py
        router.py
        schemas.py
        service.py
      organizations/
        models.py
        router.py
        schemas.py
        service.py
      subscriptions/
        models.py
        router.py
        schemas.py
        service.py
      content/
        models.py
        router.py
        schemas.py
        service.py
      media/
        models.py
        router.py
        schemas.py
        service.py
      feedback/
        models.py
        router.py
        schemas.py
        service.py
      reflections/
        models.py
        router.py
        schemas.py
        service.py
    tests/
      conftest.py
      test_auth.py
      test_permissions.py
      test_content_publish.py
      test_sanitizer.py
      test_feedback_reflections.py
      test_seed_import.py
  migrations/
    env.py
    versions/
frontend/
  src/
    app/
      apiClient.js
      authStore.js
      permissions.js
      router.js
    layouts/
      AuthLayout.vue
      LearningLayout.vue
      AdminLayout.vue
    modules/
      auth/LoginView.vue
      learning/DashboardView.vue
      learning/JourneyView.vue
      learning/ReaderView.vue
      learning/FeedbackView.vue
      learning/ReflectionsView.vue
      admin/AdminDashboard.vue
      admin/ContentWorkspace.vue
      admin/UserManagement.vue
      admin/SubscriptionSettings.vue
      admin/MediaLibrary.vue
      content-editor/RichTextEditor.vue
      content-editor/ExhibitEditor.vue
      content-editor/PublishPanel.vue
    components/
      content/SafeRichContent.vue
      ui/
    styles/
      tokens.css
      theme.css
      typography.css
```

---

### Task 1: Backend Project Skeleton and Configuration

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/base.py`
- Modify: `backend/requirements.txt`

- [x] **Step 1: Replace backend dependencies**

Set `backend/requirements.txt` to:

```text
fastapi
uvicorn[standard]
gunicorn
sqlalchemy
alembic
psycopg[binary]
pydantic-settings
python-jose[cryptography]
bcrypt
python-multipart
email-validator
bleach
boto3
pytest
httpx
pytest-asyncio
```

- [x] **Step 2: Create environment configuration**

Create `backend/app/core/config.py`:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Gita Learning"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://gita:gita@127.0.0.1:5432/gita_learning"
    secret_key: str = "change-this-in-production"
    access_token_minutes: int = 60
    allowed_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8001"
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_bucket: str = "gita-learning"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    max_upload_mb: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [x] **Step 3: Create DB session**

Create `backend/app/db/session.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [x] **Step 4: Create declarative base**

Create `backend/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [x] **Step 5: Create FastAPI app entrypoint**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True, "app": settings.app_name}
```

- [x] **Step 6: Verify import**

Run:

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 -m compileall app
```

Expected: exit code 0.

---

### Task 2: SQLAlchemy Models and Alembic Migration

**Files:**
- Create: `backend/app/modules/*/models.py`
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/versions/0001_initial.py`

- [x] **Step 1: Create organization/subscription/user/content/media/feedback/reflection models**

Create model files matching the approved spec. Use UUID-style integer primary keys or integer identity columns consistently. For this app use integer identity columns for simpler admin operations.

Model requirements:

```python
# Use this pattern in each model file.
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow():
    return datetime.utcnow()
```

Include these tables:

- `organizations`
- `plans`
- `subscriptions`
- `users`
- `curriculum_phases`
- `chapters`
- `chapter_versions`
- `concepts`
- `exhibits`
- `media_assets`
- `feedback`
- `reflections`

Critical constraints:

- `users.email` nullable, unique only when present.
- `users` has unique `(organization_id, username)`.
- `subscriptions.organization_id` references school organization.
- `concepts.chapter_version_id` references `chapter_versions.id`.
- `exhibits.media_asset_id` nullable.

- [x] **Step 2: Import all models in base metadata**

Create `backend/app/db/models.py`:

```python
from app.modules.organizations.models import Organization
from app.modules.subscriptions.models import Plan, Subscription
from app.modules.users.models import User
from app.modules.content.models import CurriculumPhase, Chapter, ChapterVersion, Concept, Exhibit
from app.modules.media.models import MediaAsset
from app.modules.feedback.models import Feedback
from app.modules.reflections.models import Reflection

__all__ = [
    "Organization",
    "Plan",
    "Subscription",
    "User",
    "CurriculumPhase",
    "Chapter",
    "ChapterVersion",
    "Concept",
    "Exhibit",
    "MediaAsset",
    "Feedback",
    "Reflection",
]
```

- [x] **Step 3: Create Alembic config**

Run:

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 -m alembic init migrations
```

Then edit `migrations/env.py` so `target_metadata = Base.metadata` and imports `app.db.models`.

- [x] **Step 4: Create initial migration**

Run against a local Postgres database:

```powershell
cd D:\dvm\bhagavad-gita\backend
$env:DATABASE_URL="postgresql+psycopg://gita:gita@127.0.0.1:5432/gita_learning"
py -3.13 -m alembic revision --autogenerate -m "initial schema"
```

Expected: migration file includes all Milestone 1 tables and constraints.

- [ ] **Step 5: Apply migration**

Blocked locally: `alembic upgrade head` could not authenticate as `gita@127.0.0.1:5432`. Migration files compile and passed static/mapping review; run this step when valid PostgreSQL credentials are available.

Run:

```powershell
py -3.13 -m alembic upgrade head
```

Expected: all tables created in PostgreSQL.

---

### Task 3: Auth, Passwords, Roles, and Current User

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/permissions.py`
- Create: `backend/app/modules/auth/router.py`
- Create: `backend/app/modules/auth/schemas.py`
- Create: `backend/app/modules/auth/service.py`
- Modify: `backend/app/main.py`
- Test: `backend/app/tests/test_auth.py`

- [x] **Step 1: Write auth tests**

Create tests for:

```python
def test_student_can_login_with_username(client, seeded_student):
    response = client.post("/api/auth/login", json={"identifier": seeded_student.username, "password": "Passw0rd!"})
    assert response.status_code == 200
    assert response.json()["access_token"]

def test_teacher_can_login_with_email(client, seeded_teacher):
    response = client.post("/api/auth/login", json={"identifier": seeded_teacher.email, "password": "Passw0rd!"})
    assert response.status_code == 200

def test_invalid_password_is_rejected(client, seeded_student):
    response = client.post("/api/auth/login", json={"identifier": seeded_student.username, "password": "wrong"})
    assert response.status_code == 401
```

- [x] **Step 2: Implement password hashing and JWT**

Create `backend/app/core/security.py`:

```python
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
from app.core.config import get_settings

settings = get_settings()
ALGORITHM = "HS256"

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": subject, "exp": expires}, settings.secret_key, algorithm=ALGORITHM)
```

- [x] **Step 3: Implement login route**

Login accepts JSON:

```json
{"identifier": "student001", "password": "Passw0rd!"}
```

Lookup rule:

- if identifier contains `@`, match lowercased email.
- otherwise match username within organization-independent first pass for Milestone 1.
- later multi-school login screen can include school code if username collision becomes visible.

- [x] **Step 4: Implement permissions**

Create dependencies:

- `get_current_user`
- `require_roles(*roles)`
- `require_platform_admin`
- `require_content_admin`
- `require_learning_access`

`require_learning_access` verifies student/teacher school subscription is active or in grace.

- [x] **Step 5: Register auth router**

In `backend/app/main.py`:

```python
from app.modules.auth.router import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
```

- [x] **Step 6: Run tests**

Run:

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 -m pytest app/tests/test_auth.py -v
```

Expected: all auth tests pass.

---

### Task 4: Seed Initial Platform, School, Admins, and Import Current Content

**Files:**
- Create: `backend/app/db/seed.py`
- Create: `backend/app/modules/content/importer.py`
- Test: `backend/app/tests/test_seed_import.py`

- [x] **Step 1: Write importer test**

Test behavior:

```python
def test_seed_import_creates_phases_and_published_content(db_session):
    result = import_seed_json(db_session, "backend/seed_data/bhagavad_gita_export.json")
    assert result.chapter_count > 0
    assert db_session.query(CurriculumPhase).count() == 4
    assert db_session.query(ChapterVersion).filter_by(status="published").count() > 0
```

- [x] **Step 2: Implement seed service**

`seed.py` creates:

- platform organization
- default school organization
- default plan
- active subscription for default school
- super admin user
- optional content admin user

Use environment variables:

- `SUPER_ADMIN_EMAIL`
- `SUPER_ADMIN_PASSWORD`

Do not hard-code production defaults in deployed environments.

- [x] **Step 3: Implement content importer**

Importer maps existing JSON:

- create 4 phases.
- distribute existing chapters by order across phases until manual mapping exists.
- create chapter.
- create first published chapter version.
- create concepts.
- create exhibits.
- sanitize rich HTML with backend sanitizer.

- [x] **Step 4: Add CLI entrypoint**

Create `backend/scripts/seed.py`:

```python
from app.db.session import SessionLocal
from app.db.seed import seed_initial_data

db = SessionLocal()
try:
    seed_initial_data(db)
finally:
    db.close()
```

- [x] **Step 5: Verify seed**

Run:

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 scripts\seed.py
py -3.13 -m pytest app/tests/test_seed_import.py -v
```

Expected: seed creates platform/school/content once and is idempotent.

---

### Task 5: Content Versioning and Publish APIs

**Files:**
- Create: `backend/app/modules/content/router.py`
- Create: `backend/app/modules/content/schemas.py`
- Create: `backend/app/modules/content/service.py`
- Test: `backend/app/tests/test_content_publish.py`

- [x] **Step 1: Write content publish tests**

Required tests:

```python
def test_learning_api_returns_published_version_only(client, published_chapter, draft_version, student_token):
    response = client.get("/api/learning/chapters", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 200
    assert response.json()[0]["title"] == published_chapter.current_published_title

def test_content_admin_can_publish_draft(client, content_admin_token, draft_version):
    response = client.post(f"/api/admin/content/chapter-versions/{draft_version.id}/publish", headers={"Authorization": f"Bearer {content_admin_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "published"
```

- [x] **Step 2: Implement learning read APIs**

Routes:

- `GET /api/learning/phases`
- `GET /api/learning/chapters`
- `GET /api/learning/chapters/{chapter_id}`

Return only published versions.

- [x] **Step 3: Implement admin content APIs**

Routes:

- `GET /api/admin/content/chapters`
- `POST /api/admin/content/chapters`
- `POST /api/admin/content/chapters/{chapter_id}/draft`
- `PUT /api/admin/content/chapter-versions/{version_id}`
- `POST /api/admin/content/chapter-versions/{version_id}/publish`
- concept CRUD under draft version
- exhibit CRUD under concept

- [x] **Step 4: Run tests**

Run:

```powershell
py -3.13 -m pytest app/tests/test_content_publish.py -v
```

Expected: published content remains stable until explicit publish.

---

### Task 6: Rich Text Sanitizer

**Files:**
- Create: `backend/app/core/sanitizer.py`
- Test: `backend/app/tests/test_sanitizer.py`
- Create: `frontend/src/components/content/SafeRichContent.vue`

- [x] **Step 1: Write sanitizer tests**

Tests:

```python
def test_sanitizer_removes_scripts():
    dirty = '<p>Hello</p><script>alert(1)</script>'
    assert '<script' not in sanitize_rich_html(dirty)

def test_sanitizer_preserves_allowed_content():
    dirty = '<h2>Title</h2><blockquote>Verse</blockquote><ul><li>Point</li></ul>'
    clean = sanitize_rich_html(dirty)
    assert '<h2>' in clean
    assert '<blockquote>' in clean
    assert '<li>' in clean
```

- [x] **Step 2: Implement bleach sanitizer**

Allowed tags:

```python
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s",
    "h2", "h3", "h4",
    "ul", "ol", "li",
    "blockquote",
    "table", "thead", "tbody", "tr", "th", "td",
    "a",
]
```

Allowed attributes:

```python
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "target", "rel"]}
```

Always add `rel="noreferrer noopener"` to external links in rendering or sanitizer.

- [x] **Step 3: Use sanitizer in content create/update/import**

Sanitize all rich fields:

- chapter version description
- concept description
- concept learning outcome
- concept teaching material
- concept activities
- exhibit field value when `field_type = html`

- [x] **Step 4: Create frontend safe renderer**

`SafeRichContent.vue` is the only component allowed to use `v-html`:

```vue
<script setup>
defineProps({ html: { type: String, default: '' } });
</script>

<template>
  <div class="safe-rich-content" v-html="html" />
</template>
```

- [x] **Step 5: Run tests**

Run:

```powershell
py -3.13 -m pytest app/tests/test_sanitizer.py -v
npm run build
```

Expected: sanitizer tests and frontend build pass.

---

### Task 7: Media Storage with MinIO

**Files:**
- Create: `backend/app/core/storage.py`
- Create: `backend/app/modules/media/router.py`
- Create: `backend/app/modules/media/schemas.py`
- Create: `backend/app/modules/media/service.py`

- [x] **Step 1: Implement storage abstraction**

Create functions:

- `upload_file(file_obj, key, content_type)`
- `delete_file(key)`
- `get_presigned_url(key, expires_seconds=3600)`

Use `boto3.client("s3", endpoint_url=settings.minio_endpoint, ...)`.

- [x] **Step 2: Implement media upload API**

Route:

- `POST /api/admin/media`

Only `super_admin` and `content_admin`.

Validates:

- MIME starts with `image/`, `audio/`, `video/`, or is PDF.
- file size <= `settings.max_upload_mb`.

Returns `MediaAssetOut`.

- [x] **Step 3: Implement media listing API**

Routes:

- `GET /api/admin/media`
- `GET /api/media/{asset_id}/url`

Use signed URLs or proxied URLs.

- [ ] **Step 4: Verify manually**

Run backend and upload one small image through API client or admin UI after frontend media screen exists.

Expected: object appears in MinIO bucket and row appears in `media_assets`.

---

### Task 8: Feedback and Reflections APIs

**Files:**
- Create: `backend/app/modules/feedback/router.py`
- Create: `backend/app/modules/feedback/schemas.py`
- Create: `backend/app/modules/feedback/service.py`
- Create: `backend/app/modules/reflections/router.py`
- Create: `backend/app/modules/reflections/schemas.py`
- Create: `backend/app/modules/reflections/service.py`
- Test: `backend/app/tests/test_feedback_reflections.py`

- [x] **Step 1: Write feedback/reflection tests**

Tests:

```python
def test_student_can_submit_content_feedback(client, student_token, published_concept):
    response = client.post("/api/feedback", headers={"Authorization": f"Bearer {student_token}"}, json={
        "scope_type": "concept",
        "scope_id": published_concept.id,
        "category": "confusing",
        "rating": 3,
        "comment": "Please explain this more."
    })
    assert response.status_code == 201

def test_private_reflection_visible_only_to_owner(client, student_token, other_student_token):
    created = client.post("/api/reflections", headers={"Authorization": f"Bearer {student_token}"}, json={
        "body": "My private note",
        "visibility": "private"
    }).json()
    response = client.get(f"/api/reflections/{created['id']}", headers={"Authorization": f"Bearer {other_student_token}"})
    assert response.status_code == 404
```

- [x] **Step 2: Implement feedback routes**

Routes:

- `POST /api/feedback`
- `GET /api/admin/feedback`

Visibility:

- student/teacher creates.
- content admin sees content feedback.
- super admin sees all.

- [x] **Step 3: Implement reflection routes**

Routes:

- `POST /api/reflections`
- `GET /api/reflections`
- `GET /api/reflections/{id}`

Visibility:

- owner sees own private/submitted reflections.
- super admin can see submitted reflections only in Milestone 1 admin APIs if needed.

- [x] **Step 4: Run tests**

Run:

```powershell
py -3.13 -m pytest app/tests/test_feedback_reflections.py -v
```

Expected: all visibility rules pass.

---

### Task 9: Frontend App Shell, Router, Auth Store

**Files:**
- Create: `frontend/src/app/router.js`
- Create: `frontend/src/app/apiClient.js`
- Create: `frontend/src/app/authStore.js`
- Create: `frontend/src/app/permissions.js`
- Create: `frontend/src/layouts/*.vue`
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/App.vue`

- [x] **Step 1: Install frontend dependencies**

Run:

```powershell
cd D:\dvm\bhagavad-gita\frontend
npm install vue-router pinia @tiptap/vue-3 @tiptap/starter-kit
```

- [x] **Step 2: Create API client**

`apiClient.js`:

```javascript
export async function api(path, options = {}) {
  const token = localStorage.getItem('gita.token');
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  const contentType = res.headers.get('content-type') || '';
  return contentType.includes('application/json') ? res.json() : res.blob();
}
```

- [x] **Step 3: Create Pinia auth store**

Store:

- token
- user
- login(identifier, password)
- logout()
- hasRole(role)

- [x] **Step 4: Create router guards**

Rules:

- `/login` public.
- learning routes require student/teacher/content_admin/super_admin.
- `/admin` routes require content_admin/super_admin.

- [x] **Step 5: Create layouts**

Layouts:

- `AuthLayout.vue`: centered login.
- `LearningLayout.vue`: student/teacher top nav.
- `AdminLayout.vue`: admin sidebar.

- [x] **Step 6: Verify build**

Run:

```powershell
npm run build
```

Expected: build passes.

---

### Task 10: Learning Dashboard, Journey, and Reader UI

**Files:**
- Create: `frontend/src/modules/learning/DashboardView.vue`
- Create: `frontend/src/modules/learning/JourneyView.vue`
- Create: `frontend/src/modules/learning/ReaderView.vue`
- Create: `frontend/src/modules/learning/FeedbackView.vue`
- Create: `frontend/src/modules/learning/ReflectionsView.vue`
- Create: `frontend/src/components/content/SafeRichContent.vue`
- Create: `frontend/src/styles/tokens.css`
- Create: `frontend/src/styles/theme.css`
- Create: `frontend/src/styles/typography.css`

- [x] **Step 1: Define design tokens**

Create tokens:

```css
:root {
  --color-ink: #101828;
  --color-indigo: #17213c;
  --color-saffron: #b66a18;
  --color-gold: #d8a641;
  --color-paper: #fffaf0;
  --color-surface: #ffffff;
  --color-line: #e3d7bf;
  --color-muted: #667085;
  --radius-sm: 6px;
  --radius-md: 8px;
  --shadow-soft: 0 16px 44px rgba(31, 24, 12, 0.10);
}
```

- [x] **Step 2: Implement dashboard**

Dashboard sections:

- continue learning
- current phase progress
- recent chapters
- reflection prompt
- feedback shortcut

Use real API data from `/api/learning/phases` and `/api/learning/chapters`.

- [x] **Step 3: Implement journey**

Show Phase 1-4 path with chapter counts and the selected/current phase based on the first unread chapter available to the user.

- [x] **Step 4: Implement reader**

Reader layout:

- left chapter navigation on desktop.
- top chapter selector on mobile.
- chapter header.
- concepts in ordered sections.
- exhibits rendered by type/format.

Use `SafeRichContent` for sanitized HTML.

- [x] **Step 5: Implement feedback/reflection screens**

Forms:

- general feedback.
- content feedback from reader.
- private/submitted reflection.

- [ ] **Step 6: Render-check**

Implementation build and backend regression checks passed. Local visual screenshot capture was blocked by the headless browser environment: Chrome and Edge both exited without writing screenshots, even with workspace-local profiles, while `http://127.0.0.1:5173/login` returned HTTP 200.

Run:

```powershell
npm run build
```

Then run backend and inspect:

- `/learn`
- `/journey`
- `/reader`
- `/feedback`
- `/reflections`

Expected: no generic prototype layout, no broken mobile first viewport, no raw HTML shown.

---

### Task 11: Admin Content Workspace and Rich Editor

**Files:**
- Create: `frontend/src/modules/admin/ContentWorkspace.vue`
- Create: `frontend/src/modules/content-editor/RichTextEditor.vue`
- Create: `frontend/src/modules/content-editor/ExhibitEditor.vue`
- Create: `frontend/src/modules/content-editor/PublishPanel.vue`

- [x] **Step 1: Implement TipTap editor wrapper**

`RichTextEditor.vue` supports:

- paragraph
- headings
- bold/italic
- bullet/ordered lists
- blockquote
- table if included by extension
- link command

Output HTML to parent.

- [x] **Step 2: Implement content workspace layout**

Desktop layout:

- left: phase/chapter tree.
- center: chapter/concept/exhibit editor.
- right: publish/status panel.

Mobile fallback:

- stacked panels.

- [x] **Step 3: Implement chapter version editing**

Admin can:

- create chapter.
- create draft from published chapter.
- edit draft title/description.
- publish draft.

- [x] **Step 4: Implement concept editing**

Admin can:

- create concept.
- edit rich fields.
- reorder by order index.
- delete concept from draft.

- [x] **Step 5: Implement exhibit editing**

Admin can:

- create exhibit.
- set title.
- set field type.
- set field format.
- edit HTML/link value.
- attach media asset.
- reorder/delete.

- [ ] **Step 6: Verify content workflow**

Implementation build passed and backend content tests passed. Manual login/publish smoke verification remains open until a running local database with seeded admin credentials is available.

Manual check:

1. Login as content admin.
2. Create draft.
3. Change title.
4. Confirm learner reader still shows old published title.
5. Publish draft.
6. Confirm learner reader shows new title.

---

### Task 12: Admin Users, Subscription, and Media Library

**Files:**
- Create: `frontend/src/modules/admin/UserManagement.vue`
- Create: `frontend/src/modules/admin/SubscriptionSettings.vue`
- Create: `frontend/src/modules/admin/MediaLibrary.vue`
- Backend routers for users, organizations, subscriptions, media

- [x] **Step 1: Implement user management APIs**

Routes:

- `GET /api/admin/users`
- `POST /api/admin/users`
- `PUT /api/admin/users/{id}`
- `POST /api/admin/users/{id}/reset-password-token`
- `PUT /api/admin/users/{id}/active`

- [x] **Step 2: Implement user management UI**

Fields:

- name
- email
- username/admission number
- role
- organization
- grade label
- section label
- active

- [x] **Step 3: Implement subscription APIs**

Routes:

- `GET /api/admin/subscriptions`
- `PUT /api/admin/subscriptions/{id}`

Fields:

- status
- starts_at
- expires_at
- grace_until
- contract_notes

- [x] **Step 4: Implement subscription settings UI**

Super admin can update manual subscription status and dates.

- [x] **Step 5: Implement media library UI**

Content admin/super admin can:

- upload media.
- list media.
- copy/select asset for exhibit.

- [ ] **Step 6: Verify admin flows**

Implementation build passed and targeted backend auth/media/feedback checks passed. Manual admin smoke verification remains open until seeded local runtime credentials/storage are available.

Manual check:

- create student with username.
- create teacher with email.
- update subscription to expired and after grace.
- confirm student/teacher access blocked.
- upload media and attach to exhibit.

---

### Task 13: Deployment Files and Documentation

**Files:**
- Create: `deploy/gita-learning.service`
- Create: `deploy/nginx-gita-learning.conf`
- Create: `deploy/env.example`
- Modify: `README.md`

- [x] **Step 1: Create systemd unit**

`deploy/gita-learning.service`:

```ini
[Unit]
Description=Gita Learning FastAPI app
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/gita-learning/backend
EnvironmentFile=/etc/gita-learning.env
ExecStart=/var/www/gita-learning/backend/.venv/bin/gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8001 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- [x] **Step 2: Create Nginx sample**

`deploy/nginx-gita-learning.conf`:

```nginx
server {
    server_name gita.example.com;

    client_max_body_size 100m;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

- [x] **Step 3: Create env example**

Include:

- `DATABASE_URL`
- `SECRET_KEY`
- `MINIO_ENDPOINT`
- `MINIO_BUCKET`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `SUPER_ADMIN_EMAIL`
- `SUPER_ADMIN_PASSWORD`
- `ALLOWED_ORIGINS`

- [x] **Step 4: Update README**

README sections:

- local PostgreSQL setup.
- alembic migration.
- seed import.
- frontend build.
- backend dev server.
- Ubuntu deployment.

---

### Task 14: End-to-End Verification

**Files:**
- Test command only unless adding e2e tests.

- [x] **Step 1: Backend tests**

Run:

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 -m pytest app/tests -v
```

Expected: all tests pass.

- [x] **Step 2: Frontend build**

Run:

```powershell
cd D:\dvm\bhagavad-gita\frontend
npm run build
```

Expected: Vite build passes.

- [ ] **Step 3: Migration verification**

Blocked locally by PostgreSQL authentication: `FATAL: password authentication failed for user "gita"` when running Alembic against `127.0.0.1:5432`.

Run against a test database:

```powershell
cd D:\dvm\bhagavad-gita\backend
py -3.13 -m alembic downgrade base
py -3.13 -m alembic upgrade head
```

Expected: downgrade/upgrade completes without schema errors.

- [ ] **Step 4: Manual smoke path**

Blocked until a seeded local runtime database, valid login credentials, and MinIO/storage service are available.

Run the app and verify:

1. Super admin login.
2. Content admin login.
3. Student login by username.
4. Teacher login by email.
5. Learning dashboard loads.
6. Journey loads.
7. Reader loads published content.
8. Draft edit does not affect published reader.
9. Publish updates reader.
10. Feedback submission works.
11. Private reflection is visible only to owner.
12. Submitted reflection saves.
13. Media upload works.
14. Expired subscription after grace blocks student/teacher access.

Expected: all smoke steps pass.
