from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.security import hash_password  # noqa: E402
from app.modules.users.models import User  # noqa: E402


def load_env_file(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def reset_super_admin_password(db: Session, email: str, password: str) -> User:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    user = db.scalar(select(User).where(User.email == email, User.role == "super_admin"))
    if user is None:
        raise LookupError(f"No super_admin found with email: {email}")

    user.hashed_password = hash_password(password)
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset the Gita Learning super admin password.")
    parser.add_argument("--email", default=os.getenv("SUPER_ADMIN_EMAIL"), help="Super admin email address.")
    parser.add_argument("--password", default=os.getenv("NEW_SUPER_ADMIN_PASSWORD"), help="New password.")
    parser.add_argument("--env-file", default="/etc/gita-learning.env", help="Environment file to load.")
    args = parser.parse_args()

    load_env_file(args.env_file)

    email = args.email or os.getenv("SUPER_ADMIN_EMAIL")
    if not email:
        email = input("Super admin email: ").strip()

    password = args.password or os.getenv("NEW_SUPER_ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm new password: ")
        if password != confirm:
            raise SystemExit("Passwords do not match.")

    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user = reset_super_admin_password(db, email, password)
    finally:
        db.close()

    print(f"Password updated for super admin: {user.email}")


if __name__ == "__main__":
    main()
