from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.services.course_catalog import seed_ai_course


def main() -> int:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        result = seed_ai_course(session)
        session.commit()
    print(
        "AI course seeded. "
        f"chapters={result['chapters']}, knowledge_points={result['knowledge_points']}, "
        f"resources_written={result['resources_written']}, questions_created={result['questions_created']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
