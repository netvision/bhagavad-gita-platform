import json
import shutil
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DB = ROOT / "backend" / "lesson_plans.db"
SOURCE_UPLOADS = ROOT / "backend" / "uploads"
APP_DIR = Path(__file__).resolve().parents[1]
TARGET_JSON = APP_DIR / "backend" / "seed_data" / "bhagavad_gita_export.json"
TARGET_UPLOADS = APP_DIR / "backend" / "uploads"
CLASS_NAME = "Class 9"
SUBJECT_NAME = "Bhagwad geeta"


def row_dict(row):
    return {key: row[key] for key in row.keys()}


def copy_upload(filename, copied):
    if not filename or filename in copied:
        return
    source = SOURCE_UPLOADS / filename
    if source.exists():
        TARGET_UPLOADS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, TARGET_UPLOADS / filename)
        copied.add(filename)


def main():
    conn = sqlite3.connect(SOURCE_DB)
    conn.row_factory = sqlite3.Row
    subject = conn.execute(
        """
        SELECT s.id, s.name subject_name, c.name class_name
        FROM subjects s
        JOIN classes c ON c.id = s.class_id
        WHERE c.name = ? AND s.name = ?
        """,
        (CLASS_NAME, SUBJECT_NAME),
    ).fetchone()
    if not subject:
        raise SystemExit(f"Could not find {CLASS_NAME} / {SUBJECT_NAME}")

    copied = set()
    chapters = []
    for chapter in conn.execute(
        """
        SELECT * FROM chapters
        WHERE subject_id = ?
        ORDER BY order_index, id
        """,
        (subject["id"],),
    ):
        copy_upload(chapter["pdf_filename"], copied)
        concepts = []
        for concept in conn.execute(
            "SELECT * FROM concepts WHERE chapter_id = ? ORDER BY display_order, id",
            (chapter["id"],),
        ):
            exhibits = []
            for exhibit in conn.execute(
                "SELECT * FROM exhibits WHERE concept_id = ? ORDER BY sort_order, id",
                (concept["id"],),
            ):
                copy_upload(exhibit["file_key"], copied)
                exhibits.append({
                    "source_id": exhibit["id"],
                    "field_key": exhibit["field_key"],
                    "field_type": exhibit["field_type"],
                    "field_value": exhibit["field_value"],
                    "file_key": exhibit["file_key"],
                    "file_url": f"/uploads/{exhibit['file_key']}" if exhibit["file_key"] else None,
                    "sort_order": exhibit["sort_order"] or 0,
                })
            images = []
            for image in conn.execute(
                "SELECT * FROM concept_images WHERE concept_id = ? ORDER BY sort_order, id",
                (concept["id"],),
            ):
                copy_upload(image["filename"], copied)
                images.append({
                    "source_id": image["id"],
                    "filename": image["filename"],
                    "original_name": image["original_name"],
                    "sort_order": image["sort_order"] or 0,
                    "url": f"/uploads/{image['filename']}",
                })
            concepts.append({
                "source_id": concept["id"],
                "s_no": concept["s_no"],
                "title": concept["title"],
                "display_order": concept["display_order"] or 0,
                "concept_description": concept["concept_description"],
                "sessions": concept["sessions"],
                "learning_outcomes": concept["learning_outcomes"],
                "integration_other_sub": concept["integration_other_sub"],
                "teaching_materials_methods": concept["teaching_materials_methods"],
                "library": concept["library"],
                "activity": concept["activity"],
                "life_lesson": concept["life_lesson"],
                "remarks": concept["remarks"],
                "exhibit_ref": concept["exhibit_ref"],
                "exhibits": exhibits,
                "images": images,
            })
        chapters.append({
            "source_id": chapter["id"],
            "title": chapter["title"],
            "aim": chapter["aim"],
            "order_index": chapter["order_index"] or 0,
            "pdf_filename": chapter["pdf_filename"],
            "pdf_url": f"/uploads/{chapter['pdf_filename']}" if chapter["pdf_filename"] else None,
            "is_published": bool(chapter["is_approved"]),
            "concepts": concepts,
        })

    payload = {
        "format": "bhagavad-gita-app-export-v1",
        "app": "Bhagavad Gita",
        "source": f"{subject['class_name']} {subject['subject_name']}",
        "chapters": chapters,
    }
    TARGET_JSON.parent.mkdir(parents=True, exist_ok=True)
    TARGET_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(chapters)} chapters to {TARGET_JSON}")
    print(f"Copied {len(copied)} upload files to {TARGET_UPLOADS}")


if __name__ == "__main__":
    main()

