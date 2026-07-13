from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_MODE", "sqlite")
os.environ.setdefault("SQLITE_DATABASE_URL", "sqlite://")

from backend.app.core.database import Base
from backend.app.models import Course, CourseResource, KnowledgePoint, Question, ResourceCenter
from backend.app.services.course_catalog import ai_prerequisites, load_ai_course_catalog, seed_ai_course


class ArtificialIntelligenceCourseCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_catalog_has_complete_course_structure(self) -> None:
        catalog = load_ai_course_catalog()
        points = [point for chapter in catalog["chapters"] for point in chapter["knowledge_points"]]
        questions = [item for chapter in catalog["chapters"] for item in chapter["questions"]]

        self.assertEqual(len(catalog["chapters"]), 8)
        self.assertEqual(len(points), 32)
        self.assertGreaterEqual(len(questions), 16)
        self.assertEqual(catalog["course"]["total_hours"], 64)
        self.assertIn("反向传播", ai_prerequisites()["CNN"])
        self.assertIn("Transformer", ai_prerequisites()["大模型与RAG"])

    def test_seed_is_idempotent_and_writes_learning_materials(self) -> None:
        with self.Session() as session:
            first = seed_ai_course(session)
            session.commit()
            second = seed_ai_course(session)
            session.commit()

            course = session.query(Course).filter(Course.name == "人工智能").one()
            self.assertEqual(first["knowledge_points"], 32)
            self.assertEqual(second["resources_written"], 0)
            self.assertEqual(
                session.query(KnowledgePoint).filter(KnowledgePoint.course_id == course.id).count(),
                32,
            )
            self.assertEqual(
                session.query(CourseResource).filter(CourseResource.course_id == course.id).count(),
                16,
            )
            self.assertEqual(session.query(Question).filter(Question.course_id == course.id).count(), 16)
            self.assertEqual(session.query(ResourceCenter).count(), 8)

    def test_seed_reuses_pending_course_in_existing_transaction(self) -> None:
        with self.Session() as session:
            session.add(Course(id=1, name="人工智能", description="旧演示课程"))
            result = seed_ai_course(session)
            session.commit()

            self.assertEqual(result["course_id"], 1)
            self.assertEqual(session.query(Course).filter(Course.name == "人工智能").count(), 1)
            self.assertEqual(
                session.query(KnowledgePoint).filter(KnowledgePoint.course_id == 1).count(),
                32,
            )


if __name__ == "__main__":
    unittest.main()
