from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_MODE", "sqlite")
os.environ.setdefault("SQLITE_DATABASE_URL", "sqlite://")
os.environ.setdefault("USE_ML_SERVICE", "false")
os.environ.setdefault("LEARNPILOT_LLM_MODE", "template")
os.environ["PRODUCER_ASYNC_ENABLED"] = "false"

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.services.course_catalog import seed_ai_course


class EndToEndLearningJourneyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        with self.Session() as session:
            seed_ai_course(session)
            session.commit()

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_complete_personalized_learning_journey(self) -> None:
        registered = self.client.post(
            "/api/v1/auth/register",
            json={
                "username": "journey_student",
                "password": "secure-pass-123",
                "email": "journey@example.com",
                "display_name": "联调学生",
            },
        )
        self.assertEqual(registered.status_code, 200)
        account = registered.json()
        headers = {"Authorization": f"Bearer {account['access_token']}"}

        analyzed = self.client.post(
            "/api/v1/profile/analyze",
            headers=headers,
            json={
                "text": (
                    "我是计算机专业大二学生，正在学习人工智能，希望两个月内掌握 CNN 和反向传播。"
                    "我的数学基础一般，CNN 是薄弱点，偏好图示、代码案例和分步骤讲解。"
                )
            },
        )
        self.assertEqual(analyzed.status_code, 200)
        profile = analyzed.json()["profile"]
        dimensions = (
            "major",
            "grade",
            "course",
            "goal",
            "weak_points",
            "preference",
            "cognitive_style",
            "knowledge_level",
        )
        self.assertGreaterEqual(sum(bool(profile.get(name)) for name in dimensions), 6)
        self.assertIn("CNN", profile["weak_points"])

        started = self.client.post(
            "/api/v1/learning/start",
            headers=headers,
            json={
                "course_id": 1,
                "requirement": "从 CNN 基础开始，结合图示和代码练习制定两个月学习计划",
            },
        )
        self.assertEqual(started.status_code, 200)
        workflow = started.json()
        self.assertGreaterEqual(len(workflow["resources"]), 5)
        self.assertTrue(workflow["path"]["nodes"])
        path_id = workflow["path"]["path_id"]

        with patch("backend.app.api.producer._enqueue_producer_task", return_value=False):
            produced = self.client.post(
                "/producer/task",
                headers=headers,
                json={
                    "topic": "CNN 卷积与池化",
                    "requirement": "面向基础一般且偏好图示和代码的本科生",
                    "types": ["lecture", "mind_map", "exercise", "reading", "code", "video"],
                },
            )
        self.assertEqual(produced.status_code, 200)
        result = self.client.get(
            f"/producer/result/{produced.json()['task_id']}",
            headers=headers,
        )
        self.assertEqual(result.status_code, 200)
        generated = result.json()["result"]
        self.assertTrue(generated["lecture"]["content"])
        self.assertTrue(generated["mind_map"]["content"])
        self.assertTrue(generated["exercises"])
        self.assertTrue(generated["code_examples"])
        self.assertTrue(generated["videos"][0]["animation_html"])
        self.assertEqual(generated["videos"][0]["media_status"], "preview")
        self.assertFalse(generated["videos"][0]["mp4_available"])
        self.assertGreaterEqual(len(generated["agent_traces"]), 5)

        tutored = self.client.post(
            "/api/v1/tutor/ask",
            headers=headers,
            json={"course_id": 1, "question": "CNN 的卷积核为什么能提取局部特征？"},
        )
        self.assertEqual(tutored.status_code, 200)
        self.assertTrue(tutored.json()["grounded"])
        self.assertTrue(tutored.json()["evidence"])

        questions = self.client.get(
            "/api/v1/courses/1/assessment/questions?limit=1",
            headers=headers,
        )
        self.assertEqual(questions.status_code, 200)
        question = questions.json()[0]
        submitted = self.client.post(
            "/api/v1/evaluations/submit",
            headers=headers,
            json={
                "course_id": 1,
                "path_id": path_id,
                "answers": [
                    {
                        "question_id": question["id"],
                        "answer": "尚未掌握",
                        "elapsed_seconds": 20,
                    }
                ],
                "completed_resource_count": 2,
                "study_minutes": 15,
            },
        )
        self.assertEqual(submitted.status_code, 200)
        evaluation = submitted.json()
        self.assertEqual(evaluation["adaptation"]["trigger"], "evaluation_submitted")
        self.assertIn(evaluation["adaptation"]["strategy"], {"remediation", "consolidation", "advancement"})
        self.assertTrue(evaluation["adaptation"]["revised_steps"])

        history = self.client.get("/api/v1/evaluations/history", headers=headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()["items"][0]["evaluation_id"], evaluation["evaluation_id"])


if __name__ == "__main__":
    unittest.main()
