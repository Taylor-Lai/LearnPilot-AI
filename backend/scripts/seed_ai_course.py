from __future__ import annotations

import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.services.course_catalog import seed_ai_course
from backend.app.services.course_materials import course_materials_available, ingest_ai_for_beginners


def wait_for_database(attempts: int = 30, delay_seconds: float = 2.0) -> None:
    """Wait for the database TCP listener to become usable after its health check."""
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == attempts:
                raise
            time.sleep(delay_seconds)


def main() -> int:
    wait_for_database()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        result = seed_ai_course(session)
        materials = (
            ingest_ai_for_beginners(session, int(result["course_id"]))
            if course_materials_available()
            else None
        )
        session.commit()
    print(
        "AI course seeded. "
        f"chapters={result['chapters']}, knowledge_points={result['knowledge_points']}, "
        f"resources_written={result['resources_written']}, questions_created={result['questions_created']}"
    )
    if materials is None:
        print("AI course materials skipped: synchronize the external source before ingestion.")
    else:
        print(
            "AI course materials ingested. "
            f"documents={materials['documents']}, chunks_written={materials['chunks_written']}, "
            f"source_revision={materials['source_revision']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
