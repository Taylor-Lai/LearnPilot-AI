from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_MODE", "sqlite")
os.environ.setdefault("SQLITE_DATABASE_URL", "sqlite://")
os.environ.setdefault("USE_ML_SERVICE", "false")
os.environ.setdefault("LEARNPILOT_LLM_MODE", "template")

from backend.app.api.producer import _execute_producer_task
from backend.app.core.database import Base, get_db
from backend.app.core.security import hash_password
from backend.app.main import app
from backend.app.models import Course, KnowledgePoint, LearningPath, Question, User
from fastapi.testclient import TestClient


class ProductionApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        with self.Session() as db:
            db.add(Course(id=1, name="人工智能", description="AI"))
            db.add(KnowledgePoint(id=1, course_id=1, name="CNN", description="Conv", difficulty="hard"))
            db.add(
                Question(
                    id=1,
                    course_id=1,
                    knowledge_point_id=1,
                    question_type="short_answer",
                    stem="卷积核的主要作用是什么？",
                    answer="提取局部特征",
                    explanation="卷积核通过局部感受野提取空间特征。",
                    difficulty=0.4,
                    source="test",
                )
            )
            db.add(
                User(
                    username="teacher1",
                    email="teacher1@example.com",
                    password_hash=hash_password("secret123"),
                    role="teacher",
                    is_admin=False,
                    status="active",
                )
            )
            db.commit()

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_auth_import_and_question_flow(self) -> None:
        teacher = self.client.post("/api/v1/auth/login", json={"username": "teacher1", "password": "secret123"})
        self.assertEqual(teacher.status_code, 200)
        token = teacher.json()["access_token"]
        self.assertEqual(teacher.headers["x-content-type-options"], "nosniff")
        self.assertEqual(teacher.headers["x-frame-options"], "DENY")
        self.assertIn("x-request-id", teacher.headers)

        imported = self.client.post(
            "/api/v1/courses/1/resources/import",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "filename": "cnn.md",
                "source_type": "markdown",
                "content": "# CNN 入门\nCNN 包含卷积、池化和特征图。",
            },
        )
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(imported.json()["status"], "completed")

        resources = self.client.get("/api/v1/courses/1/resources")
        self.assertEqual(resources.status_code, 200)
        self.assertEqual(resources.json()[0]["title"], "CNN 入门")

        questions = self.client.post(
            "/api/v1/courses/1/resources/import",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "filename": "questions.json",
                "source_type": "question_json",
                "content": '{"questions":[{"stem":"CNN 中池化有什么作用？","answer":"降采样","difficulty":0.4}]}',
            },
        )
        self.assertEqual(questions.status_code, 200)
        listed = self.client.get("/api/v1/courses/1/questions", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(listed.status_code, 200)
        self.assertIn("CNN 中池化有什么作用？", [item["stem"] for item in listed.json()])

    def test_student_cannot_import_resources(self) -> None:
        student = self.client.post(
            "/api/v1/auth/register",
            json={"username": "student1", "password": "secret123", "role": "student"},
        )
        token = student.json()["access_token"]
        response = self.client.post(
            "/api/v1/courses/1/resources/import",
            headers={"Authorization": f"Bearer {token}"},
            json={"filename": "x.md", "source_type": "markdown", "content": "# x"},
        )
        self.assertEqual(response.status_code, 403)

    def test_public_registration_cannot_self_assign_privileged_roles(self) -> None:
        compat = self.client.post(
            "/api/auth/register",
            json={"username": "admin", "email": "not-admin@example.com", "password": "secret123"},
        )
        self.assertEqual(compat.status_code, 200)
        self.assertFalse(compat.json()["user"]["is_admin"])
        self.assertEqual(compat.json()["user"]["role"], "USER")

        versioned = self.client.post(
            "/api/v1/auth/register",
            json={"username": "attacker", "password": "secret123", "role": "admin"},
        )
        self.assertEqual(versioned.status_code, 200)
        self.assertEqual(versioned.json()["user"]["role"], "student")

    def test_frontend_producer_flow_and_task_authorization(self) -> None:
        owner = self.client.post(
            "/api/auth/register",
            json={"username": "owner", "email": "owner@example.com", "password": "secret123"},
        ).json()
        owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}

        created = self.client.post(
            "/producer/task",
            headers=owner_headers,
            json={"topic": "卷积神经网络", "requirement": "面向初学者", "types": ["lecture", "exercise"]},
        )
        self.assertEqual(created.status_code, 200)
        task_id = created.json()["task_id"]

        listed = self.client.get("/producer/tasks", headers=owner_headers)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["items"][0]["task_id"], task_id)

        result = self.client.get(f"/producer/result/{task_id}", headers=owner_headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["status"], "completed")
        self.assertIn("lecture", result.json()["result"])
        self.assertTrue(result.json()["result"]["generation_fallback"])
        animation = result.json()["result"]["videos"][0]
        self.assertTrue(animation["generated"])
        self.assertIn("卷积神经网络", animation["animation_html"])
        self.assertIn("<style>", animation["animation_html"])
        self.assertNotIn("<script", animation["animation_html"])

        tutor = self.client.post(
            "/api/v1/tutor/ask",
            headers=owner_headers,
            json={"question": "卷积神经网络为什么能提取局部特征？", "course_id": 1},
        )
        self.assertEqual(tutor.status_code, 200)
        self.assertTrue(tutor.json()["grounded"])
        self.assertTrue(tutor.json()["evidence"])
        self.assertEqual(len(tutor.json()["visual_aid"]["nodes"]), 4)

        for file_format, signature, content_type in (
            ("docx", b"PK", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("pptx", b"PK", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
            ("pdf", b"%PDF", "application/pdf"),
        ):
            exported = self.client.get(
                f"/producer/export/{task_id}?format={file_format}",
                headers=owner_headers,
            )
            self.assertEqual(exported.status_code, 200)
            self.assertEqual(exported.headers["content-type"], content_type)
            self.assertTrue(exported.content.startswith(signature))
            self.assertIn("attachment", exported.headers["content-disposition"])

        stranger = self.client.post(
            "/api/auth/register",
            json={"username": "stranger", "email": "stranger@example.com", "password": "secret123"},
        ).json()
        stranger_headers = {"Authorization": f"Bearer {stranger['access_token']}"}
        self.assertEqual(self.client.get(f"/producer/result/{task_id}").status_code, 401)
        self.assertEqual(self.client.get(f"/producer/result/{task_id}", headers=stranger_headers).status_code, 403)
        self.assertEqual(
            self.client.get(f"/producer/export/{task_id}?format=docx", headers=stranger_headers).status_code,
            403,
        )

    def test_producer_queues_when_worker_backend_is_available(self) -> None:
        account = self.client.post(
            "/api/auth/register",
            json={"username": "queued", "email": "queued@example.com", "password": "secret123"},
        ).json()
        headers = {"Authorization": f"Bearer {account['access_token']}"}
        with patch("backend.app.api.producer._enqueue_producer_task", return_value=True):
            created = self.client.post(
                "/producer/task",
                headers=headers,
                json={"topic": "Transformer", "types": ["lecture", "exercise"]},
            )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["execution_mode"], "async")
        self.assertEqual(created.json()["status"], "pending")
        task_id = created.json()["task_id"]

        stranger = self.client.post(
            "/api/auth/register",
            json={"username": "queue_stranger", "email": "queue-stranger@example.com", "password": "secret123"},
        ).json()
        stranger_headers = {"Authorization": f"Bearer {stranger['access_token']}"}
        self.assertEqual(
            self.client.post(f"/producer/task/{task_id}/cancel", headers=stranger_headers).status_code,
            403,
        )

        with patch("backend.app.api.producer._cancel_queued_job"):
            cancelled = self.client.post(f"/producer/task/{task_id}/cancel", headers=headers)
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["status"], "cancelled")
        self.assertEqual(cancelled.json()["progress"], 0)

        with patch("backend.app.api.producer._enqueue_producer_task", return_value=True):
            retried = self.client.post(f"/producer/task/{task_id}/retry", headers=headers)
        self.assertEqual(retried.status_code, 200)
        self.assertEqual(retried.json()["status"], "pending")
        self.assertEqual(retried.json()["execution_mode"], "async")

        with self.Session() as db:
            _execute_producer_task(db, task_id)

        completed = self.client.get(f"/producer/task/{task_id}", headers=headers)
        self.assertEqual(completed.json()["status"], "completed")
        self.assertEqual(completed.json()["progress"], 100)
        self.assertEqual(self.client.post(f"/producer/task/{task_id}/cancel", headers=headers).status_code, 409)
        self.assertEqual(self.client.post(f"/producer/task/{task_id}/retry", headers=headers).status_code, 409)

    def test_admin_task_console_is_protected(self) -> None:
        with self.Session() as db:
            admin = User(
                username="system_admin",
                email="system-admin@example.com",
                password_hash=hash_password("secret123"),
                role="admin",
                is_admin=True,
                status="active",
            )
            db.add(admin)
            db.commit()

        student = self.client.post(
            "/api/auth/register",
            json={"username": "student2", "email": "student2@example.com", "password": "secret123"},
        ).json()
        admin = self.client.post(
            "/api/auth/login", json={"email": "system-admin@example.com", "password": "secret123"}
        ).json()

        self.assertEqual(
            self.client.get(
                "/admin/producer/tasks", headers={"Authorization": f"Bearer {student['access_token']}"}
            ).status_code,
            403,
        )
        self.assertEqual(self.client.get("/admin/users/page").status_code, 401)
        self.assertEqual(
            self.client.get(
                "/admin/statistics", headers={"Authorization": f"Bearer {student['access_token']}"}
            ).status_code,
            403,
        )
        response = self.client.get(
            "/admin/producer/tasks", headers={"Authorization": f"Bearer {admin['access_token']}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.json())

        statistics = self.client.get("/admin/statistics", headers={"Authorization": f"Bearer {admin['access_token']}"})
        self.assertEqual(statistics.status_code, 200)
        payload = statistics.json()
        self.assertIn("overview", payload)
        self.assertIn("trends", payload)
        self.assertIn("distributions", payload)
        self.assertGreaterEqual(payload["overview"]["userCount"], 2)
        self.assertEqual(len(payload["trends"]["dates"]), 7)

    def test_assessment_is_graded_by_backend_and_history_is_private(self) -> None:
        account = self.client.post(
            "/api/auth/register",
            json={"username": "learner", "email": "learner@example.com", "password": "secret123"},
        ).json()
        headers = {"Authorization": f"Bearer {account['access_token']}"}

        questions = self.client.get("/api/v1/courses/1/assessment/questions", headers=headers)
        self.assertEqual(questions.status_code, 200)
        self.assertNotIn("answer", questions.json()[0])

        submitted = self.client.post(
            "/api/v1/evaluations/submit",
            headers=headers,
            json={
                "course_id": 1,
                "answers": [{"question_id": 1, "answer": "提取局部特征", "elapsed_seconds": 12}],
                "study_minutes": 5,
            },
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.json()["correct_count"], 1)
        self.assertEqual(submitted.json()["score"], 100.0)
        self.assertEqual(submitted.json()["adaptation"]["strategy"], "advancement")
        self.assertEqual(submitted.json()["adaptation"]["trigger"], "evaluation_submitted")
        self.assertIn("CNN", submitted.json()["adaptation"]["after_mastery"])
        self.assertEqual(submitted.json()["adaptation"]["before_mastery"]["CNN"], 0.5)
        self.assertGreater(submitted.json()["adaptation"]["mastery_delta"]["CNN"], 0)
        evaluation_id = submitted.json()["evaluation_id"]

        history = self.client.get("/api/v1/evaluations/history", headers=headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()["items"][0]["evaluation_id"], evaluation_id)
        self.assertEqual(
            self.client.get(f"/api/v1/evaluations/{evaluation_id}", headers=headers).status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/v1/evaluations/history").status_code, 401)

    def test_failed_assessment_reduces_neutral_mastery(self) -> None:
        account = self.client.post(
            "/api/auth/register",
            json={"username": "remedial_learner", "email": "remedial@example.com", "password": "secret123"},
        ).json()
        headers = {"Authorization": f"Bearer {account['access_token']}"}

        submitted = self.client.post(
            "/api/v1/evaluations/submit",
            headers=headers,
            json={
                "course_id": 1,
                "answers": [{"question_id": 1, "answer": "unrelated answer", "elapsed_seconds": 8}],
                "study_minutes": 3,
            },
        )

        self.assertEqual(submitted.status_code, 200)
        adaptation = submitted.json()["adaptation"]
        self.assertEqual(adaptation["strategy"], "remediation")
        self.assertEqual(adaptation["before_mastery"]["CNN"], 0.5)
        self.assertLess(adaptation["after_mastery"]["CNN"], 0.5)
        self.assertLess(adaptation["mastery_delta"]["CNN"], 0)
        self.assertIn("CNN", adaptation["weak_points"])

    def test_feedback_and_platform_settings_are_persisted(self) -> None:
        created = self.client.post(
            "/api/feedback",
            json={"content": "生成的讲义缺少示例代码", "contact": "student@example.com", "type": "功能建议"},
        )
        self.assertEqual(created.status_code, 200)
        feedback_id = created.json()["feedback"]["id"]

        with self.Session() as db:
            db.add(
                User(
                    username="feedback_admin",
                    email="feedback-admin@example.com",
                    password_hash=hash_password("secret123"),
                    role="admin",
                    is_admin=True,
                    status="active",
                )
            )
            db.commit()
        admin = self.client.post(
            "/api/auth/login", json={"email": "feedback-admin@example.com", "password": "secret123"}
        ).json()
        headers = {"Authorization": f"Bearer {admin['access_token']}"}

        listed = self.client.get("/admin/feedback", headers=headers)
        self.assertEqual(listed.json()["items"][0]["id"], feedback_id)
        resolved = self.client.put(f"/admin/feedback/{feedback_id}/status", headers=headers, json={"status": "已解决"})
        self.assertEqual(resolved.json()["status"], "已解决")

        saved = self.client.put("/admin/settings", headers=headers, json={"siteName": "汇知灵创"})
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(self.client.get("/admin/settings", headers=headers).json()["siteName"], "汇知灵创")

    def test_learning_path_delete_requires_owner_and_removes_it_from_history(self) -> None:
        owner = self.client.post(
            "/api/auth/register",
            json={"username": "path_owner", "email": "path-owner@example.com", "password": "secret123"},
        ).json()
        stranger = self.client.post(
            "/api/auth/register",
            json={"username": "path_stranger", "email": "path-stranger@example.com", "password": "secret123"},
        ).json()
        owner_id = owner["user"]["id"]
        with self.Session() as db:
            path = LearningPath(
                user_id=owner_id,
                course_id=1,
                title="待删除路径",
                goal="验证删除链路",
                status="active",
                progress=0,
            )
            db.add(path)
            db.commit()
            db.refresh(path)
            path_id = path.id

        stranger_headers = {"Authorization": f"Bearer {stranger['access_token']}"}
        self.assertEqual(
            self.client.delete(f"/path/delete?pathId={path_id}", headers=stranger_headers).status_code,
            403,
        )

        owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
        deleted = self.client.delete(f"/path/delete?pathId={path_id}", headers=owner_headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()["success"])

        history = self.client.get(f"/path/list?userId={owner_id}", headers=owner_headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()["items"], [])
        self.assertEqual(self.client.delete(f"/path/delete?pathId={path_id}", headers=owner_headers).status_code, 404)


if __name__ == "__main__":
    unittest.main()
