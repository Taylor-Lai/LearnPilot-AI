from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models import CourseResource, ResourceChunk
from backend.app.services.course_catalog import seed_ai_course
from backend.app.services.course_materials import ingest_ai_for_beginners


class CourseMaterialIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)

    def test_ingestion_is_attributed_chunked_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.Session() as session:
            source_root = Path(directory)
            (source_root / ".learnpilot-source.json").write_text(
                json.dumps(
                    {
                        "source_id": "microsoft-ai-for-beginners",
                        "revision": "0b3a28c7c3d081a7de625e496f6be6461188fe93",
                    }
                ),
                encoding="utf-8",
            )
            lessons = source_root / "translations" / "zh-CN" / "lessons"
            intro = lessons / "1-Intro" / "README.md"
            lab = lessons / "3-NeuralNetworks" / "03-Perceptron" / "lab" / "README.md"
            intro.parent.mkdir(parents=True)
            lab.parent.mkdir(parents=True)
            intro.write_text("# 人工智能简介\n\n人工智能研究智能系统。", encoding="utf-8")
            lab.write_text("# 感知机实验\n\n实现并验证一个感知机。", encoding="utf-8")

            catalog = seed_ai_course(session)
            first = ingest_ai_for_beginners(session, int(catalog["course_id"]), source_root)
            session.commit()
            second = ingest_ai_for_beginners(session, int(catalog["course_id"]), source_root)
            session.commit()

            self.assertEqual(first["documents"], 2)
            self.assertEqual(first["resources_created"], 2)
            self.assertEqual(second["resources_created"], 0)
            resources = session.query(CourseResource).filter(CourseResource.source.like("ai-for-beginners:%")).all()
            self.assertEqual(len(resources), 2)
            self.assertEqual({item.resource_type for item in resources}, {"reading", "lab"})
            self.assertTrue(all(item.resource_metadata["content_license"] == "MIT" for item in resources))
            self.assertEqual(session.query(ResourceChunk).count(), second["chunks_written"])


if __name__ == "__main__":
    unittest.main()
