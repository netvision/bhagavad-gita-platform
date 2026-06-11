import json

import pytest
from sqlalchemy import func, select

from app.db.seed import seed_initial_data
from app.modules.content.importer import import_seed_json
from app.modules.content.models import Chapter, ChapterVersion, Concept, Exhibit
from app.modules.curriculum.models import CurriculumPhase


SEED_JSON = "backend/seed_data/bhagavad_gita_export.json"


def test_import_seed_json_creates_published_common_curriculum(db_session):
    result = import_seed_json(db_session, SEED_JSON)

    assert result.chapter_count > 0
    titles = db_session.scalars(select(Chapter.title).order_by(Chapter.sort_order)).all()
    assert "3. नित्य/अनित्य का भेद" in titles
    assert not any("à¤" in title for title in titles)
    assert db_session.scalar(select(func.count()).select_from(CurriculumPhase)) == 4
    assert (
        db_session.scalar(
            select(func.count()).select_from(ChapterVersion).where(ChapterVersion.status == "published")
        )
        > 0
    )


def test_import_seed_json_is_idempotent_for_phases_and_chapters(db_session):
    import_seed_json(db_session, SEED_JSON)
    phase_count = db_session.scalar(select(func.count()).select_from(CurriculumPhase))
    chapter_count = db_session.scalar(select(func.count()).select_from(Chapter))

    import_seed_json(db_session, SEED_JSON)

    assert db_session.scalar(select(func.count()).select_from(CurriculumPhase)) == phase_count
    assert db_session.scalar(select(func.count()).select_from(Chapter)) == chapter_count


def test_import_seed_json_preserves_child_ids_on_repeated_import(db_session):
    import_seed_json(db_session, SEED_JSON)
    concept_ids = db_session.scalars(select(Concept.id).order_by(Concept.id)).all()
    exhibit_ids = db_session.scalars(select(Exhibit.id).order_by(Exhibit.id)).all()

    import_seed_json(db_session, SEED_JSON)

    assert db_session.scalars(select(Concept.id).order_by(Concept.id)).all() == concept_ids
    assert db_session.scalars(select(Exhibit.id).order_by(Exhibit.id)).all() == exhibit_ids


def test_import_seed_json_clears_published_at_when_version_becomes_draft(db_session, tmp_path):
    source = tmp_path / "seed.json"
    payload = {
        "chapters": [
            {
                "source_id": 1,
                "title": "Chapter One",
                "aim": "<p>Published summary</p>",
                "order_index": 1,
                "is_published": True,
                "concepts": [],
            }
        ]
    }
    source.write_text(json.dumps(payload), encoding="utf-8")
    import_seed_json(db_session, source)
    version = db_session.scalar(select(ChapterVersion))
    assert version.published_at is not None

    payload["chapters"][0]["is_published"] = False
    source.write_text(json.dumps(payload), encoding="utf-8")
    import_seed_json(db_session, source)
    db_session.refresh(version)

    assert version.status == "draft"
    assert version.published_at is None


def test_seed_initial_data_requires_explicit_local_credential_opt_in(db_session, monkeypatch):
    monkeypatch.delenv("SUPER_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("SUPER_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("CONTENT_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("CONTENT_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("ALLOW_LOCAL_SEED_CREDENTIALS", raising=False)

    with pytest.raises(RuntimeError, match="ALLOW_LOCAL_SEED_CREDENTIALS"):
        seed_initial_data(db_session)
