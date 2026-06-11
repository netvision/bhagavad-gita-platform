from __future__ import annotations

import json
import math
import re
import encodings.cp1252 as cp1252
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.sanitizer import sanitize_rich_html
from app.modules.content.models import Chapter, ChapterVersion, Concept, Exhibit
from app.modules.curriculum.models import CurriculumPhase


PHASES = [
    ("Phase 1", "phase-1", "Foundation sequence for the shared Gita curriculum."),
    ("Phase 2", "phase-2", "Development sequence for the shared Gita curriculum."),
    ("Phase 3", "phase-3", "Deepening sequence for the shared Gita curriculum."),
    ("Phase 4", "phase-4", "Integration sequence for the shared Gita curriculum."),
]

MEDIA_TYPES_BY_EXTENSION = {
    ".apng": "image",
    ".avif": "image",
    ".gif": "image",
    ".jpeg": "image",
    ".jpg": "image",
    ".png": "image",
    ".svg": "image",
    ".webp": "image",
    ".aac": "audio",
    ".flac": "audio",
    ".m4a": "audio",
    ".mp3": "audio",
    ".ogg": "audio",
    ".wav": "audio",
    ".avi": "video",
    ".m4v": "video",
    ".mov": "video",
    ".mp4": "video",
    ".mpeg": "video",
    ".mpg": "video",
    ".webm": "video",
}

CP1252_REVERSE_TABLE = {
    character: byte_value
    for byte_value, character in enumerate(cp1252.decoding_table)
    if character != "\ufffe"
}
MOJIBAKE_MARKERS = ("\u00c2", "\u00c3", "\u00e0", "\u00e2")


@dataclass(frozen=True)
class ImportResult:
    chapter_count: int
    phase_count: int
    chapter_version_count: int
    concept_count: int
    exhibit_count: int


def import_seed_json(db: Session, source_path: str | Path, *, replace_content: bool = False) -> ImportResult:
    path = Path(source_path)
    if not path.is_absolute() and not path.exists():
        backend_path = Path(__file__).resolve().parents[4] / path
        if backend_path.exists():
            path = backend_path

    with path.open("r", encoding="utf-8-sig") as source:
        payload = json.load(source)
    payload = _repair_mojibake(payload)

    chapters = sorted(
        payload.get("chapters", []),
        key=lambda chapter: (chapter.get("order_index") is None, chapter.get("order_index") or 0),
    )
    phases = _ensure_phases(db)

    version_count = 0
    concept_count = 0
    exhibit_count = 0

    for index, chapter_data in enumerate(chapters):
        phase = phases[_phase_index(index, len(chapters))]
        chapter = _ensure_chapter(db, phase, chapter_data, index)
        version = _ensure_first_version(db, chapter, chapter_data)

        version_count += 1
        existing_concept_count, existing_exhibit_count = _version_child_counts(db, version)
        if existing_concept_count or existing_exhibit_count:
            if not replace_content:
                concept_count += existing_concept_count
                exhibit_count += existing_exhibit_count
                continue
            _clear_version_content(db, version)

        concepts = sorted(
            chapter_data.get("concepts", []),
            key=lambda concept: (
                concept.get("display_order") is None,
                concept.get("display_order") or _safe_int(concept.get("s_no"), default=0),
            ),
        )
        for concept_index, concept_data in enumerate(concepts):
            concept = _build_concept(version, concept_data, concept_index)
            db.add(concept)
            db.flush()
            concept_count += 1

            exhibits = sorted(
                concept_data.get("exhibits", []),
                key=lambda exhibit: (exhibit.get("sort_order") is None, exhibit.get("sort_order") or 0),
            )
            for exhibit_index, exhibit_data in enumerate(exhibits):
                db.add(_build_exhibit(version, exhibit_data, exhibit_index, concept_id=concept.id))
                exhibit_count += 1

        if chapter_data.get("pdf_url") or chapter_data.get("pdf_filename"):
            db.add(_build_chapter_pdf_exhibit(version, chapter_data))
            exhibit_count += 1

    db.commit()
    return ImportResult(
        chapter_count=len(chapters),
        phase_count=len(phases),
        chapter_version_count=version_count,
        concept_count=concept_count,
        exhibit_count=exhibit_count,
    )


def _ensure_phases(db: Session) -> list[CurriculumPhase]:
    phases: list[CurriculumPhase] = []
    for sort_order, (name, slug, description) in enumerate(PHASES, start=1):
        phase = db.scalar(
            select(CurriculumPhase).where(
                CurriculumPhase.organization_id.is_(None),
                CurriculumPhase.slug == slug,
            )
        )
        if phase is None:
            phase = CurriculumPhase(
                organization_id=None,
                name=name,
                slug=slug,
                description=description,
                sort_order=sort_order,
            )
            db.add(phase)
            db.flush()
        else:
            phase.name = name
            phase.description = description
            phase.sort_order = sort_order
        phases.append(phase)
    return phases


def _phase_index(chapter_index: int, chapter_count: int) -> int:
    if chapter_count <= 0:
        return 0

    chunk_size = max(1, math.ceil(chapter_count / len(PHASES)))
    return min(chapter_index // chunk_size, len(PHASES) - 1)


def _ensure_chapter(
    db: Session,
    phase: CurriculumPhase,
    chapter_data: dict[str, Any],
    chapter_index: int,
) -> Chapter:
    source_id = chapter_data.get("source_id")
    sort_order = _safe_int(chapter_data.get("order_index"), default=chapter_index + 1)
    slug = _chapter_slug(source_id, sort_order, chapter_data.get("title"))
    chapter = db.scalar(
        select(Chapter).where(
            Chapter.curriculum_phase_id == phase.id,
            Chapter.slug == slug,
        )
    )

    if chapter is None:
        chapter = Chapter(
            curriculum_phase_id=phase.id,
            title=_coerce_text(chapter_data.get("title"), fallback=f"Chapter {sort_order}"),
            slug=slug,
            sort_order=sort_order,
        )
        db.add(chapter)
        db.flush()
    else:
        chapter.title = _coerce_text(chapter_data.get("title"), fallback=f"Chapter {sort_order}")
        chapter.sort_order = sort_order

    return chapter


def _ensure_first_version(
    db: Session,
    chapter: Chapter,
    chapter_data: dict[str, Any],
) -> ChapterVersion:
    version = db.scalar(
        select(ChapterVersion).where(
            ChapterVersion.chapter_id == chapter.id,
            ChapterVersion.version_number == 1,
        )
    )
    status = "published" if chapter_data.get("is_published", True) else "draft"
    published_at = datetime.now(timezone.utc) if status == "published" else None
    title = _coerce_text(chapter_data.get("title"), fallback=chapter.title)
    summary = sanitize_rich_html(_empty_to_none(chapter_data.get("aim")))

    if version is None:
        version = ChapterVersion(
            chapter_id=chapter.id,
            version_number=1,
            status=status,
            title=title,
            summary=summary,
            body=None,
            published_at=published_at,
        )
        db.add(version)
        db.flush()
    else:
        version.status = status
        version.title = title
        version.summary = summary
        version.body = None
        version.published_at = (version.published_at or published_at) if status == "published" else None

    return version


def _version_child_counts(db: Session, version: ChapterVersion) -> tuple[int, int]:
    concept_count = db.scalar(
        select(func.count()).select_from(Concept).where(Concept.chapter_version_id == version.id)
    )
    exhibit_count = db.scalar(
        select(func.count()).select_from(Exhibit).where(Exhibit.chapter_version_id == version.id)
    )
    return concept_count or 0, exhibit_count or 0


def _clear_version_content(db: Session, version: ChapterVersion) -> None:
    db.execute(delete(Exhibit).where(Exhibit.chapter_version_id == version.id))
    db.execute(delete(Concept).where(Concept.chapter_version_id == version.id))
    db.flush()


def _build_concept(version: ChapterVersion, concept_data: dict[str, Any], index: int) -> Concept:
    sort_order = _safe_int(
        concept_data.get("display_order"),
        default=_safe_int(concept_data.get("s_no"), default=index + 1),
    )
    source_id = concept_data.get("source_id")
    return Concept(
        chapter_version_id=version.id,
        title=_coerce_text(concept_data.get("title"), fallback=f"Concept {sort_order}"),
        slug=f"concept-{sort_order:03d}-{source_id}" if source_id else f"concept-{sort_order:03d}",
        description=sanitize_rich_html(_empty_to_none(concept_data.get("concept_description"))),
        learning_outcome=sanitize_rich_html(_empty_to_none(concept_data.get("learning_outcomes"))),
        teaching_material=sanitize_rich_html(_empty_to_none(concept_data.get("teaching_materials_methods"))),
        activities=sanitize_rich_html(_empty_to_none(concept_data.get("activity"))),
        sort_order=sort_order,
    )


def _build_exhibit(
    version: ChapterVersion,
    exhibit_data: dict[str, Any],
    index: int,
    concept_id: int | None,
) -> Exhibit:
    content = _exhibit_content(exhibit_data)
    field_type = _exhibit_field_type(exhibit_data, content)
    return Exhibit(
        chapter_version_id=version.id,
        concept_id=concept_id,
        title=_coerce_text(exhibit_data.get("field_key"), fallback=f"Exhibit {index + 1}"),
        field_type=field_type,
        field_format=_coerce_text(exhibit_data.get("field_type"), fallback=None),
        content=sanitize_rich_html(content) if field_type == "html" else content,
        sort_order=_safe_int(exhibit_data.get("sort_order"), default=index),
    )


def _build_chapter_pdf_exhibit(version: ChapterVersion, chapter_data: dict[str, Any]) -> Exhibit:
    content = _empty_to_none(chapter_data.get("pdf_url")) or _empty_to_none(chapter_data.get("pdf_filename"))
    return Exhibit(
        chapter_version_id=version.id,
        concept_id=None,
        title="Chapter resource",
        field_type="link",
        field_format="pdf",
        content=content,
        sort_order=10_000,
    )


def _exhibit_content(exhibit_data: dict[str, Any]) -> str | None:
    return (
        _empty_to_none(exhibit_data.get("file_url"))
        or _empty_to_none(exhibit_data.get("file_key"))
        or _empty_to_none(exhibit_data.get("field_value"))
    )


def _exhibit_field_type(exhibit_data: dict[str, Any], content: str | None) -> str:
    source_type = str(exhibit_data.get("field_type") or "").strip().lower()
    if source_type in {"html", "link", "image", "audio", "video"}:
        return source_type

    if not content:
        return "html"

    content_extension = Path(urlparse(content).path).suffix.lower()
    if content_extension in MEDIA_TYPES_BY_EXTENSION:
        return MEDIA_TYPES_BY_EXTENSION[content_extension]

    if _looks_like_url(content) and "<" not in content:
        return "link"

    return "html"


def _chapter_slug(source_id: Any, sort_order: int, title: Any) -> str:
    base = _slugify(str(title or ""))
    if base:
        base = base[:40].strip("-")
    if not base:
        base = "chapter"

    if source_id:
        return f"{base}-{sort_order:03d}-{source_id}"[:100].strip("-")
    return f"{base}-{sort_order:03d}"[:100].strip("-")


def _slugify(value: str) -> str:
    value = value.encode("ascii", errors="ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _coerce_text(value: Any, fallback: str | None) -> str | None:
    if value is None:
        return fallback

    text = _repair_mojibake_text(str(value)).strip()
    return text or fallback


def _empty_to_none(value: Any) -> str | None:
    if value is None:
        return None

    text = _repair_mojibake_text(str(value)).strip()
    return text or None


def _repair_mojibake(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _repair_mojibake(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_repair_mojibake(item) for item in value]
    if isinstance(value, str):
        return _repair_mojibake_text(value)
    return value


def _repair_mojibake_text(value: str) -> str:
    if not any(marker in value for marker in MOJIBAKE_MARKERS):
        return value

    repaired_bytes = bytearray()
    for character in value:
        codepoint = ord(character)
        if codepoint <= 255:
            repaired_bytes.append(codepoint)
        elif character in CP1252_REVERSE_TABLE:
            repaired_bytes.append(CP1252_REVERSE_TABLE[character])
        else:
            repaired_bytes.extend(character.encode("utf-8"))

    try:
        return bytes(repaired_bytes).decode("utf-8")
    except UnicodeDecodeError:
        return value


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
