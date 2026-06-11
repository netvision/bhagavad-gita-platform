from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.seed import seed_initial_data  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        result = seed_initial_data(db)
        print(
            "Seed complete: "
            f"{result.phase_count} phases, "
            f"{result.chapter_count} chapters, "
            f"{result.chapter_version_count} versions, "
            f"{result.concept_count} concepts, "
            f"{result.exhibit_count} exhibits."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
