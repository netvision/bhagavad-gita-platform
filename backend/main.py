import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_admin, hash_password, verify_password
from database import Base, SessionLocal, engine, get_db
from models import AdminUser, Chapter, Concept, Exhibit
from sanitize import sanitize_file_key, sanitize_required_text, sanitize_text
from schemas import ChapterIn, ChapterOut, ConceptIn, ConceptOut, ExhibitIn, ExhibitOut, TokenOut


BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR.parent
FRONTEND_DIR = APP_DIR / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets" if (FRONTEND_DIST_DIR / "assets").exists() else FRONTEND_DIR
FRONTEND_INDEX = FRONTEND_DIST_DIR / "index.html" if (FRONTEND_DIST_DIR / "index.html").exists() else FRONTEND_DIR / "index.html"
UPLOADS_DIR = BASE_DIR / "uploads"
SEED_FILE = BASE_DIR / "seed_data" / "bhagavad_gita_export.json"


def file_url(filename: str | None) -> str | None:
    safe_name = sanitize_file_key(filename)
    return f"/uploads/{safe_name}" if safe_name else None


def exhibit_out(exhibit: Exhibit) -> dict:
    return {
        "id": exhibit.id,
        "source_id": exhibit.source_id,
        "field_key": sanitize_required_text(exhibit.field_key),
        "field_type": sanitize_text(exhibit.field_type) or "string",
        "field_value": sanitize_text(exhibit.field_value),
        "file_key": sanitize_file_key(exhibit.file_key),
        "file_url": file_url(exhibit.file_key),
        "sort_order": exhibit.sort_order,
    }


def concept_out(concept: Concept) -> ConceptOut:
    return ConceptOut(
        id=concept.id,
        source_id=concept.source_id,
        s_no=sanitize_text(concept.s_no),
        title=sanitize_required_text(concept.title),
        display_order=concept.display_order,
        concept_description=sanitize_text(concept.concept_description),
        sessions=sanitize_text(concept.sessions),
        learning_outcomes=sanitize_text(concept.learning_outcomes),
        integration_other_sub=sanitize_text(concept.integration_other_sub),
        teaching_materials_methods=sanitize_text(concept.teaching_materials_methods),
        library=sanitize_text(concept.library),
        activity=sanitize_text(concept.activity),
        life_lesson=sanitize_text(concept.life_lesson),
        remarks=sanitize_text(concept.remarks),
        exhibit_ref=sanitize_text(concept.exhibit_ref),
        exhibits=[ExhibitOut(**exhibit_out(exhibit)) for exhibit in concept.exhibits],
    )


def chapter_out(chapter: Chapter) -> ChapterOut:
    return ChapterOut(
        id=chapter.id,
        source_id=chapter.source_id,
        title=sanitize_required_text(chapter.title),
        aim=sanitize_text(chapter.aim),
        order_index=chapter.order_index,
        pdf_filename=sanitize_file_key(chapter.pdf_filename),
        pdf_url=file_url(chapter.pdf_filename),
        is_published=chapter.is_published,
        concepts=[concept_out(concept) for concept in chapter.concepts],
    )


def export_payload(db: Session) -> dict:
    chapters = db.query(Chapter).order_by(Chapter.order_index, Chapter.id).all()
    return {
        "format": "bhagavad-gita-app-export-v1",
        "app": "Bhagavad Gita",
        "chapters": [chapter_out(chapter).model_dump() for chapter in chapters],
    }


def clear_content(db: Session) -> None:
    try:
        db.execute(text("DELETE FROM concept_images"))
        db.commit()
    except Exception:
        db.rollback()
    db.query(Exhibit).delete()
    db.query(Concept).delete()
    db.query(Chapter).delete()
    db.commit()


def import_payload(db: Session, payload: dict) -> int:
    if payload.get("format") != "bhagavad-gita-app-export-v1":
        raise ValueError("Unsupported import format")
    clear_content(db)
    for chapter_data in payload.get("chapters", []):
        chapter = Chapter(
            source_id=chapter_data.get("source_id"),
            title=sanitize_required_text(chapter_data.get("title")),
            aim=sanitize_text(chapter_data.get("aim")),
            order_index=chapter_data.get("order_index") or 0,
            pdf_filename=sanitize_file_key(chapter_data.get("pdf_filename")),
            is_published=chapter_data.get("is_published", True),
        )
        db.add(chapter)
        db.flush()
        for concept_data in chapter_data.get("concepts", []):
            concept = Concept(
                source_id=concept_data.get("source_id"),
                chapter_id=chapter.id,
                s_no=sanitize_text(concept_data.get("s_no")),
                title=sanitize_required_text(concept_data.get("title")),
                display_order=concept_data.get("display_order") or 0,
                concept_description=sanitize_text(concept_data.get("concept_description")),
                sessions=sanitize_text(concept_data.get("sessions")),
                learning_outcomes=sanitize_text(concept_data.get("learning_outcomes")),
                integration_other_sub=sanitize_text(concept_data.get("integration_other_sub")),
                teaching_materials_methods=sanitize_text(concept_data.get("teaching_materials_methods")),
                library=sanitize_text(concept_data.get("library")),
                activity=sanitize_text(concept_data.get("activity")),
                life_lesson=sanitize_text(concept_data.get("life_lesson")),
                remarks=sanitize_text(concept_data.get("remarks")),
                exhibit_ref=sanitize_text(concept_data.get("exhibit_ref")),
            )
            db.add(concept)
            db.flush()
            for exhibit_data in concept_data.get("exhibits", []):
                db.add(Exhibit(
                    source_id=exhibit_data.get("source_id"),
                    concept_id=concept.id,
                    field_key=sanitize_required_text(exhibit_data.get("field_key")),
                    field_type=sanitize_text(exhibit_data.get("field_type")) or "string",
                    field_value=sanitize_text(exhibit_data.get("field_value")),
                    file_key=sanitize_file_key(exhibit_data.get("file_key")),
                    sort_order=exhibit_data.get("sort_order") or 0,
                ))
    db.commit()
    return db.query(Chapter).count()


def create_default_admin(db: Session) -> None:
    email = os.getenv("ADMIN_EMAIL", "admin@bhagavadgita.local").lower()
    password = os.getenv("ADMIN_PASSWORD", "ChangeMe@123")
    if db.query(AdminUser).filter(AdminUser.email == email).first():
        return
    db.add(AdminUser(email=email, name="Bhagavad Gita Admin", password_hash=hash_password(password)))
    db.commit()


def seed_if_empty(db: Session) -> None:
    if db.query(Chapter).count() or not SEED_FILE.exists():
        return
    with SEED_FILE.open("r", encoding="utf-8") as handle:
        import_payload(db, json.load(handle))


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_default_admin(db)
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Bhagavad Gita App", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8001").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="assets")


@app.get("/")
def index():
    return FileResponse(FRONTEND_INDEX)


@app.get("/api/health")
def health():
    return {"ok": True, "app": "Bhagavad Gita"}


@app.get("/api/meta")
def meta(db: Session = Depends(get_db)):
    return {
        "title": "Bhagavad Gita",
        "chapter_count": db.query(Chapter).filter(Chapter.is_published.is_(True)).count(),
    }


@app.get("/api/chapters", response_model=list[ChapterOut])
def list_public_chapters(db: Session = Depends(get_db)):
    chapters = db.query(Chapter).filter(Chapter.is_published.is_(True)).order_by(Chapter.order_index, Chapter.id).all()
    return [chapter_out(chapter) for chapter in chapters]


@app.get("/api/chapters/{chapter_id}", response_model=ChapterOut)
def get_public_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.is_published.is_(True)).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter_out(chapter)


@app.post("/api/admin/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.email == form.username.lower(), AdminUser.is_active.is_(True)).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenOut(
        access_token=create_access_token(user.email),
        user={"email": user.email, "name": user.name},
    )


@app.get("/api/admin/chapters", response_model=list[ChapterOut])
def list_admin_chapters(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return [chapter_out(chapter) for chapter in db.query(Chapter).order_by(Chapter.order_index, Chapter.id).all()]


@app.post("/api/admin/chapters", response_model=ChapterOut, status_code=201)
def create_chapter(body: ChapterIn, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    chapter = Chapter(**body.model_dump())
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter_out(chapter)


@app.put("/api/admin/chapters/{chapter_id}", response_model=ChapterOut)
def update_chapter(chapter_id: int, body: ChapterIn, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    for key, value in body.model_dump().items():
        setattr(chapter, key, value)
    db.commit()
    db.refresh(chapter)
    return chapter_out(chapter)


@app.delete("/api/admin/chapters/{chapter_id}")
def delete_chapter(chapter_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    db.delete(chapter)
    db.commit()
    return {"deleted": True}


@app.post("/api/admin/concepts", response_model=ConceptOut, status_code=201)
def create_concept(body: ConceptIn, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    if not db.query(Chapter).filter(Chapter.id == body.chapter_id).first():
        raise HTTPException(status_code=404, detail="Chapter not found")
    concept = Concept(**body.model_dump())
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept_out(concept)


@app.put("/api/admin/concepts/{concept_id}", response_model=ConceptOut)
def update_concept(concept_id: int, body: ConceptIn, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    for key, value in body.model_dump().items():
        setattr(concept, key, value)
    db.commit()
    db.refresh(concept)
    return concept_out(concept)


@app.delete("/api/admin/concepts/{concept_id}")
def delete_concept(concept_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    db.delete(concept)
    db.commit()
    return {"deleted": True}


@app.post("/api/admin/exhibits", response_model=ExhibitOut, status_code=201)
def create_exhibit(body: ExhibitIn, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    if not db.query(Concept).filter(Concept.id == body.concept_id).first():
        raise HTTPException(status_code=404, detail="Concept not found")
    exhibit = Exhibit(**body.model_dump())
    db.add(exhibit)
    db.commit()
    db.refresh(exhibit)
    return ExhibitOut(**exhibit_out(exhibit))


@app.delete("/api/admin/exhibits/{exhibit_id}")
def delete_exhibit(exhibit_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    exhibit = db.query(Exhibit).filter(Exhibit.id == exhibit_id).first()
    if not exhibit:
        raise HTTPException(status_code=404, detail="Exhibit not found")
    db.delete(exhibit)
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/export")
def download_export(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    export_path = BASE_DIR / "bhagavad_gita_export.latest.json"
    with export_path.open("w", encoding="utf-8") as handle:
        json.dump(export_payload(db), handle, ensure_ascii=False, indent=2)
    return FileResponse(export_path, filename="bhagavad_gita_export.json", media_type="application/json")


@app.post("/api/admin/import")
async def restore_export(file: UploadFile = File(...), _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        payload = json.loads((await file.read()).decode("utf-8"))
        count = import_payload(db, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Import failed: {exc}") from exc
    return {"restored_chapters": count}
