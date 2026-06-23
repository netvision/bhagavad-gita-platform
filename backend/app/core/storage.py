from pathlib import Path
import shutil
from typing import BinaryIO

from app.core.config import get_settings


BACKEND_DIR = Path(__file__).resolve().parents[2]


def upload_root() -> Path:
    upload_dir = Path(get_settings().upload_dir)
    if not upload_dir.is_absolute():
        upload_dir = BACKEND_DIR / upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def upload_file(file_obj: BinaryIO, key: str, content_type: str | None = None) -> None:
    destination = _path_for_key(key)
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_obj.seek(0)
    with destination.open("wb") as output:
        shutil.copyfileobj(file_obj, output)


def delete_file(key: str) -> None:
    path = _path_for_key(key)
    if path.exists():
        path.unlink()


def get_file_url(key: str) -> str:
    return f"/uploads/{_safe_key(key)}"


def _path_for_key(key: str) -> Path:
    root = upload_root().resolve()
    path = (root / _safe_key(key)).resolve()
    if root != path and root not in path.parents:
        raise ValueError("Storage key escapes upload directory")
    return path


def _safe_key(key: str) -> str:
    parts = [part for part in Path(key).parts if part not in ("", ".", "..")]
    return "/".join(parts)
