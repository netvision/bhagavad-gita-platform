"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        *timestamps(),
        sa.CheckConstraint("type IN ('platform', 'school')", name="ck_organizations_type"),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("slug", name="uq_plans_slug"),
    )

    op.create_table(
        "curriculum_phases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *timestamps(),
        sa.UniqueConstraint("organization_id", "slug", name="uq_curriculum_phases_organization_slug"),
    )
    op.create_index("ix_curriculum_phases_organization_id", "curriculum_phases", ["organization_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contract_notes", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status IN ('active', 'grace', 'expired', 'suspended')",
            name="ck_subscriptions_status",
        ),
    )
    op.create_index("ix_subscriptions_organization_id", "subscriptions", ["organization_id"])
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("grade_label", sa.String(length=50), nullable=True),
        sa.Column("section_label", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "role IN ('super_admin', 'content_admin', 'teacher', 'student')",
            name="ck_users_role",
        ),
        sa.UniqueConstraint("organization_id", "username", name="uq_users_organization_username"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("visibility", sa.String(length=50), server_default="private", nullable=False),
        sa.Column("alt_text", sa.Text(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_media_assets_organization_id", "media_assets", ["organization_id"])
    op.create_index("ix_media_assets_uploaded_by", "media_assets", ["uploaded_by"])

    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("curriculum_phase_id", sa.Integer(), sa.ForeignKey("curriculum_phases.id"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *timestamps(),
        sa.UniqueConstraint("curriculum_phase_id", "slug", name="uq_chapters_phase_slug"),
    )
    op.create_index("ix_chapters_curriculum_phase_id", "chapters", ["curriculum_phase_id"])

    op.create_table(
        "chapter_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_chapter_versions_status",
        ),
        sa.UniqueConstraint("chapter_id", "version_number", name="uq_chapter_versions_chapter_version"),
    )
    op.create_index("ix_chapter_versions_chapter_id", "chapter_versions", ["chapter_id"])
    op.create_index(
        "uq_chapter_versions_one_published_per_chapter",
        "chapter_versions",
        ["chapter_id"],
        unique=True,
        postgresql_where=sa.text("status = 'published'"),
        sqlite_where=sa.text("status = 'published'"),
    )

    op.create_table(
        "concepts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chapter_version_id",
            sa.Integer(),
            sa.ForeignKey("chapter_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("learning_outcome", sa.Text(), nullable=True),
        sa.Column("teaching_material", sa.Text(), nullable=True),
        sa.Column("activities", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *timestamps(),
    )
    op.create_index("ix_concepts_chapter_version_id", "concepts", ["chapter_version_id"])

    op.create_table(
        "exhibits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chapter_version_id",
            sa.Integer(),
            sa.ForeignKey("chapter_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("media_asset_id", sa.Integer(), sa.ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("field_type", sa.String(length=50), nullable=False),
        sa.Column("field_format", sa.String(length=100), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "field_type IN ('html', 'link', 'image', 'audio', 'video')",
            name="ck_exhibits_field_type",
        ),
    )
    op.create_index("ix_exhibits_chapter_version_id", "exhibits", ["chapter_version_id"])
    op.create_index("ix_exhibits_concept_id", "exhibits", ["concept_id"])
    op.create_index("ix_exhibits_media_asset_id", "exhibits", ["media_asset_id"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("exhibit_id", sa.Integer(), sa.ForeignKey("exhibits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scope_type", sa.String(length=50), nullable=False),
        sa.Column("scope_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="open", nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "scope_type IN ('app', 'chapter', 'concept', 'exhibit')",
            name="ck_feedback_scope_type",
        ),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])
    op.create_index("ix_feedback_chapter_id", "feedback", ["chapter_id"])
    op.create_index("ix_feedback_concept_id", "feedback", ["concept_id"])
    op.create_index("ix_feedback_exhibit_id", "feedback", ["exhibit_id"])

    op.create_table(
        "reflections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("exhibit_id", sa.Integer(), sa.ForeignKey("exhibits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("visibility", sa.String(length=50), nullable=False),
        sa.Column("review_status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "visibility IN ('private', 'submitted')",
            name="ck_reflections_visibility",
        ),
    )
    op.create_index("ix_reflections_user_id", "reflections", ["user_id"])
    op.create_index("ix_reflections_chapter_id", "reflections", ["chapter_id"])
    op.create_index("ix_reflections_concept_id", "reflections", ["concept_id"])
    op.create_index("ix_reflections_exhibit_id", "reflections", ["exhibit_id"])


def downgrade() -> None:
    op.drop_index("ix_reflections_exhibit_id", table_name="reflections")
    op.drop_index("ix_reflections_concept_id", table_name="reflections")
    op.drop_index("ix_reflections_chapter_id", table_name="reflections")
    op.drop_index("ix_reflections_user_id", table_name="reflections")
    op.drop_table("reflections")

    op.drop_index("ix_feedback_exhibit_id", table_name="feedback")
    op.drop_index("ix_feedback_concept_id", table_name="feedback")
    op.drop_index("ix_feedback_chapter_id", table_name="feedback")
    op.drop_index("ix_feedback_user_id", table_name="feedback")
    op.drop_table("feedback")

    op.drop_index("ix_exhibits_media_asset_id", table_name="exhibits")
    op.drop_index("ix_exhibits_concept_id", table_name="exhibits")
    op.drop_index("ix_exhibits_chapter_version_id", table_name="exhibits")
    op.drop_table("exhibits")

    op.drop_index("ix_concepts_chapter_version_id", table_name="concepts")
    op.drop_table("concepts")

    op.drop_index("uq_chapter_versions_one_published_per_chapter", table_name="chapter_versions")
    op.drop_index("ix_chapter_versions_chapter_id", table_name="chapter_versions")
    op.drop_table("chapter_versions")

    op.drop_index("ix_chapters_curriculum_phase_id", table_name="chapters")
    op.drop_table("chapters")

    op.drop_index("ix_media_assets_uploaded_by", table_name="media_assets")
    op.drop_index("ix_media_assets_organization_id", table_name="media_assets")
    op.drop_table("media_assets")

    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_organization_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("ix_curriculum_phases_organization_id", table_name="curriculum_phases")
    op.drop_table("curriculum_phases")

    op.drop_table("plans")
    op.drop_table("organizations")
