from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.storage import upload_root
from app.modules.auth.router import router as auth_router
from app.modules.content.router import admin_router as content_admin_router
from app.modules.content.router import learning_router
from app.modules.media.router import admin_router as media_admin_router
from app.modules.media.router import media_router
from app.modules.feedback.router import admin_router as feedback_admin_router
from app.modules.feedback.router import router as feedback_router
from app.modules.reflections.router import router as reflections_router
from app.modules.subscriptions.router import router as subscriptions_admin_router
from app.modules.users.router import router as users_admin_router


settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(learning_router, tags=["learning"])
app.include_router(content_admin_router, tags=["content-admin"])
app.include_router(media_admin_router, tags=["media-admin"])
app.include_router(media_router, tags=["media"])
app.include_router(feedback_router, tags=["feedback"])
app.include_router(feedback_admin_router, tags=["feedback-admin"])
app.include_router(reflections_router, tags=["reflections"])
app.include_router(users_admin_router, tags=["users-admin"])
app.include_router(subscriptions_admin_router, tags=["subscriptions-admin"])


@app.get("/api/health")
def health():
    return {"ok": True, "app": settings.app_name}


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

app.mount("/uploads", StaticFiles(directory=upload_root()), name="uploads")


@app.get("/{path:path}", include_in_schema=False)
def frontend_fallback(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    candidate = FRONTEND_DIST / path
    if candidate.is_file():
        return FileResponse(candidate)

    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)

    raise HTTPException(status_code=404, detail="Frontend build not found")
