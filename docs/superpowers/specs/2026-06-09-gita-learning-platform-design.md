# Gita Learning Platform Design

## Status

Approved direction: rebuild the current Bhagavad Gita prototype into a production-quality learning platform.

Milestone 1 is a one-school production MVP. The target architecture remains a full school-subscription SaaS platform.

## Product Goal

Build a professional subscription-based Bhagavad Gita learning application for schools serving students from standards 9 to 12. Content is a common four-year curriculum sequence of roughly 50-60 chapters, organized into four curriculum phases rather than grade-specific courses.

The platform must support:

- Central curriculum management.
- Student and teacher learning access.
- Feedback and reflections.
- A future evaluation section.
- Manual school subscription management.
- A later path to full SaaS operations without redesigning the schema.

## Milestone Strategy

### Milestone 1: Production One-School MVP

Milestone 1 includes:

- PostgreSQL database.
- Alembic migrations.
- Modular FastAPI backend.
- Vue 3 + Vite frontend with routing, layouts, and components.
- Login by email or username/admission number.
- Roles: `super_admin`, `content_admin`, `teacher`, `student`.
- Platform organization plus school organization model.
- Manual subscription state with expiry and grace period.
- Four curriculum phases.
- Chapters, concepts, and exhibits.
- Rich text editor for content fields.
- Safe HTML storage/rendering policy.
- Versioned publishing so live content stays stable during edits.
- Self-hosted S3-compatible object storage using MinIO.
- Student/teacher dashboard.
- Curriculum journey view.
- Reader.
- Feedback.
- Private and submitted reflections.
- Admin content workspace.
- Manual user creation.
- Ubuntu bare-metal deployment behind existing Nginx and existing PostgreSQL.

Milestone 1 excludes:

- Online payment.
- Evaluation engine.
- Teacher review dashboard for reflections.
- School-specific notes or supplementary material.
- Bulk user import.
- Analytics dashboards.

### Milestone 2: School Operations

Milestone 2 adds:

- Bulk student and teacher import.
- Teacher review of submitted reflections.
- School-level groups, classes, and sections.
- Better subscription reporting.
- Audit logs.
- Email invitation/password-reset hardening.
- Media lifecycle tools.

### Milestone 3: Evaluation and SaaS Expansion

Milestone 3 adds:

- Quizzes.
- Reflective assessments.
- Scenario-based responses.
- Teacher-reviewed assignments.
- Question bank.
- Student response tracking.
- Progress and evaluation reports.
- Multi-school onboarding workflows.
- Optional school-specific notes/tools.

### Milestone 4: Scale and Polish

Milestone 4 adds:

- Redis-backed background jobs and rate limiting.
- Caching.
- Deeper analytics.
- Advanced content version diff/rollback.
- Multilingual content support.
- Strong backup and restore workflows.
- Mobile/PWA polish.

## Product Areas

### Student and Teacher App

Students and teachers have mostly the same Milestone 1 learning experience.

Primary screens:

- Login.
- Home dashboard.
- Curriculum journey.
- Reader.
- Feedback form.
- Reflections.

The dashboard should include:

- Continue learning.
- Current curriculum phase.
- Recent chapters or concepts.
- Reflection prompt.
- Feedback shortcut.

The journey view should show the Phase 1-4 sequence and make the curriculum feel like a guided four-year path.

The reader should support:

- Chapter navigation.
- Concept sections.
- Exhibit rendering.
- Rich shloka/story/explanation layouts.
- High readability for Hindi/Sanskrit/English content.

### Admin App

Admin lives at `/admin` on the same domain.

Admin screens:

- Admin dashboard.
- Content workspace.
- User management.
- Subscription settings.
- Media library.

Super admins can access all admin functions.

Content admins manage central curriculum only. Schools do not get content admins in Milestone 1. School-specific notes are reserved for Milestone 3 or later, and central curriculum remains controlled by platform staff.

## Roles and Permissions

### `super_admin`

Platform owner role. Can:

- Manage organizations.
- Manage subscriptions.
- Manage users.
- Manage content.
- Manage media.
- See all feedback and operational data.

### `content_admin`

Central curriculum role. Can:

- Create/edit/publish curriculum content.
- Upload and manage curriculum media.
- See content-related feedback.

Cannot:

- Manage platform subscriptions unless explicitly granted later.
- See private student reflections.

### `teacher`

Milestone 1 teacher role. Can:

- Access published learning content if the school subscription is active or in grace.
- Submit feedback.
- Create private or submitted reflections.

Future teacher role may see:

- Teacher-only content/tools.
- Submitted reflections from students in their school.
- Evaluation review workflows.

### `student`

Student role. Can:

- Access published learning content if the school subscription is active or in grace.
- Submit content feedback and general feedback.
- Create private reflections.
- Submit reflections when intended for review.

## Organization and Subscription Model

The schema includes organizations from Milestone 1.

Organization types:

- `platform`: houses super admins and content admins.
- `school`: houses students and teachers.

Subscriptions are manual per-school contracts.

Subscription states:

- `active`
- `grace`
- `expired`
- `suspended`

Subscription fields:

- `organization_id`
- `plan_id`
- `status`
- `starts_at`
- `expires_at`
- `grace_until`
- manual contract notes

Access behavior:

- Students and teachers can access content while the school subscription is active.
- During grace, access continues with warning UI.
- After grace, student/teacher access is blocked.
- Platform admins can still log in regardless of school subscription status.

## Authentication

Milestone 1 uses email/username plus password.

Login identifiers:

- Teachers and admins require email.
- Students may have email, but it is optional.
- Students can log in with username/admission number.
- Usernames/admission numbers are scoped to organization to avoid cross-school conflicts.

Password reset:

- Include password reset if SMTP is configured.
- If SMTP is not available, implement reset-token generation and admin-copyable reset links as fallback.

Security requirements:

- Strong password hashing.
- No default production credentials.
- JWT access tokens for Milestone 1.
- Backend role checks on every protected route.
- Login rate limiting can be added later with Redis.

## Data Model

### Organizations

`organizations`

- `id`
- `name`
- `type`
- `status`
- timestamps

### Plans

`plans`

- `id`
- `name`
- `description`
- contract/package metadata
- timestamps

### Subscriptions

`subscriptions`

- `id`
- `organization_id`
- `plan_id`
- `status`
- `starts_at`
- `expires_at`
- `grace_until`
- `contract_notes`
- timestamps

### Users

`users`

- `id`
- `organization_id`
- `name`
- `email`
- `username`
- `password_hash`
- `role`
- `grade_label`
- `section_label`
- `is_active`
- timestamps

### Curriculum Phases

`curriculum_phases`

- `id`
- `title`
- `description`
- `order_index`
- timestamps

Use Phase 1-4, not hard-coded grade-specific curriculum.

### Chapters

`chapters`

- `id`
- `phase_id`
- `title`
- `description`
- `order_index`
- `status`
- timestamps

### Chapter Versions

`chapter_versions`

- `id`
- `chapter_id`
- `version_number`
- `status`: `draft`, `published`, `archived`
- `title`
- `description`
- `created_by`
- `published_by`
- `published_at`
- timestamps

Published content remains visible while admins edit a new draft version.

### Concepts

`concepts`

- `id`
- `chapter_version_id`
- `title`
- `description`
- `learning_outcome`
- `teaching_material`
- `activities`
- `order_index`
- timestamps

Concept descriptions and rich fields use sanitized safe HTML.

### Exhibits

`exhibits`

- `id`
- `concept_id`
- `title`
- `field_type`
- `field_format`
- `field_value`
- `media_asset_id`
- `order_index`
- timestamps

Allowed `field_type` values:

- `html`
- `link`
- `image`
- `audio`
- `video`

Allowed `field_format` values should include:

- `story`
- `shloka`
- `shloka_meaning`
- `example`
- `explanation`
- `discussion_prompt`
- `activity`
- `reference`

### Media Assets

`media_assets`

- `id`
- `storage_key`
- `original_filename`
- `mime_type`
- `size_bytes`
- `uploaded_by`
- `visibility`
- timestamps

Media files are stored in MinIO. PostgreSQL stores only metadata.

### Feedback

`feedback`

- `id`
- `user_id`
- `scope_type`: `app`, `chapter`, `concept`, `exhibit`
- `scope_id`
- `category`
- `rating`
- `comment`
- `status`
- timestamps

Visibility:

- Super admins see all feedback.
- Content admins see content-related feedback.
- Teachers do not get a broad feedback dashboard in Milestone 1.

### Reflections

`reflections`

- `id`
- `user_id`
- `chapter_id`
- `concept_id`
- `body`
- `visibility`: `private`, `submitted`
- `review_status`
- timestamps

Visibility:

- Students see their own reflections.
- Private reflections stay private.
- Submitted reflections are designed for future teacher/admin review.

### Future Evaluation Tables

Reserve module/table naming for:

- `evaluations`
- `evaluation_questions`
- `evaluation_responses`

Do not implement the evaluation engine in Milestone 1.

## Rich Text and Content Safety

Use a rich text editor from Milestone 1.

Recommended editor: TipTap for Vue.

Allowed rich content:

- headings
- paragraphs
- bold
- italic
- lists
- tables
- blockquotes
- links
- images/media references through the media system

Disallowed:

- arbitrary scripts
- arbitrary iframes
- inline event handlers
- broad custom HTML
- unsafe inline styles

Rich HTML must be sanitized before storage and before rendering. Rendering must happen through dedicated safe content-rendering components, not scattered arbitrary `v-html`.

## Media Storage

Use MinIO as the self-hosted S3-compatible object storage service.

Requirements:

- Upload API validates file type and size.
- Backend writes media metadata to PostgreSQL.
- Backend stores object in MinIO.
- Content references media through `media_asset_id`.
- Media URLs should be proxied or signed depending on visibility.
- Backup strategy must include object storage data.

## Backend Architecture

Use FastAPI, but restructure into modules.

Target layout:

```text
backend/
  app/
    main.py
    core/
      config.py
      security.py
      permissions.py
      storage.py
    db/
      session.py
      base.py
      migrations/
    modules/
      auth/
      users/
      organizations/
      subscriptions/
      content/
      media/
      feedback/
      reflections/
      admin/
    schemas/
    tests/
  alembic.ini
```

Backend requirements:

- PostgreSQL only for production.
- Alembic migrations from the start.
- No `Base.metadata.create_all()` in production startup.
- Environment-based configuration.
- Modular routers and service layers.
- Permission dependencies per route.
- Subscription access dependency for student/teacher content routes.
- Sanitizer service for rich HTML.
- Storage service abstraction for MinIO/S3-compatible APIs.

Backend test coverage:

- login by email
- login by username/admission number
- role permission enforcement
- subscription active/grace/expired behavior
- content version publishing
- rich HTML sanitizer
- media metadata creation
- feedback visibility
- reflection visibility

## Frontend Architecture

Use Vue 3 + Vite.

Target layout:

```text
frontend/
  src/
    app/
      router.js
      apiClient.js
      authStore.js
      permissions.js
    layouts/
      LearningLayout.vue
      AdminLayout.vue
      AuthLayout.vue
    modules/
      learning/
        Dashboard.vue
        Journey.vue
        Reader.vue
        FeedbackForm.vue
        ReflectionForm.vue
      admin/
        AdminDashboard.vue
        ContentWorkspace.vue
        UserManagement.vue
        SubscriptionSettings.vue
        MediaLibrary.vue
      content-editor/
        RichTextEditor.vue
        ExhibitEditor.vue
        PublishPanel.vue
    components/
      ui/
      content/
    styles/
      tokens.css
      theme.css
      typography.css
```

Routes:

- `/login`
- `/learn`
- `/journey`
- `/reader/:chapterId?`
- `/feedback`
- `/reflections`
- `/admin`
- `/admin/content`
- `/admin/users`
- `/admin/subscription`
- `/admin/media`

Learning app requirements:

- Professional dashboard first.
- Phase journey one click away.
- Reader one click away.
- Strong readable content typography.
- Feedback and reflection flows are visible but not intrusive.

Admin app requirements:

- Separate `/admin` route area.
- Sidebar navigation.
- Dense, efficient screens.
- Content tree plus editor plus publish/status panel.
- User management with manual creation.
- Subscription settings for manual activation/expiry/grace.
- Media library.

## Visual Direction

Design foundation: modern school SaaS.

Subject layer: Indian spirituality, traditional yet modern.

Palette:

- deep indigo/navy for authority
- saffron/gold for spiritual accent
- warm paper/off-white for reading surfaces
- muted terracotta/copper as secondary accent
- clean white/near-white for admin efficiency

Avoid:

- generic beige card-heavy UI
- excessive brown/orange palette
- dark-heavy mystical UI everywhere
- decorative religious clutter
- marketing homepage composition for the app

Graphics:

- subtle mandala/yantra-inspired geometry
- thin-line motifs
- richer chapter/reader art moments
- restrained admin visuals

Typography:

- modern sans-serif UI
- strong Devanagari fallback for Hindi/Sanskrit
- special shloka block treatment

Admin UI should prioritize productivity over atmosphere. Student/teacher UI can carry more warmth and subject identity.

## Deployment and Operations

Production target: bare-metal Ubuntu VPS/server behind existing Nginx reverse proxy.

Runtime:

- FastAPI served by Gunicorn with Uvicorn workers.
- Managed by `systemd`.
- Vue built to static assets.
- Single domain:
  - `/` or `/learn` for learning app
  - `/admin` for admin app
  - `/api/...` for backend API

Database:

- Use existing PostgreSQL server.
- Dedicated database and DB user for this app.
- Alembic migrations run during deployment.

Object storage:

- MinIO or equivalent self-hosted S3-compatible storage.
- Managed as its own service.

Environment:

- Database URL.
- JWT secrets.
- MinIO endpoint/access keys.
- SMTP settings.
- App domain.
- Upload limits.
- Allowed origins.

Nginx:

- Existing Nginx reverse proxy forwards to local app port.
- TLS terminates at Nginx.
- Static cache headers for frontend assets.
- Upload size limits configured for media routes.

Backups:

- Daily PostgreSQL dump.
- Object storage backup/sync.
- Retention policy.
- Restore procedure documented and tested.

Monitoring:

- systemd service health.
- Nginx logs.
- app logs.
- structured FastAPI logs.
- health endpoint.

## Branding Defaults

Use `Gita Learning` as the working product name until final branding is chosen.

## Existing Data Migration

The existing seed JSON should be migrated into the new PostgreSQL schema as initial content.

Importer behavior:

- Create curriculum phases.
- Map existing chapters into initial phase/order manually or by configured mapping.
- Create chapters and first published chapter versions.
- Create concepts.
- Create exhibits.
- Sanitize existing rich HTML into the allowed safe HTML policy.

## Non-Goals for Milestone 1

- No online billing.
- No payment gateway.
- No evaluation engine.
- No multi-language translation management.
- No school-specific content customization.
- No teacher-only dashboards beyond reserved navigation/schema.
- No analytics dashboards.
- No mobile app.

## Acceptance Criteria for Milestone 1

- Super admin can log in and manage users, school subscription state, media, and content.
- Content admin can create/edit draft content and publish versions.
- Published content remains stable while a new draft is edited.
- Student can log in with username/admission number and access content when school subscription is active or in grace.
- Teacher can log in and access the same learning UI as students.
- Expired school subscription after grace blocks student/teacher access.
- Student/teacher can submit content feedback and general app feedback.
- Student/teacher can create private reflections and submitted reflections.
- Rich HTML is sanitized and rendered safely.
- Media uploads store files in object storage and metadata in PostgreSQL.
- App deploys on Ubuntu behind existing Nginx using existing PostgreSQL.
- Alembic migrations create and update schema.
