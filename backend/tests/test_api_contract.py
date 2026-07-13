"""Guard the HTTP paths already consumed by the frontend and backend-to-ML adapter."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("DATABASE_MODE", "sqlite")
os.environ.setdefault("SQLITE_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("USE_ML_SERVICE", "false")
os.environ.setdefault("LEARNPILOT_LLM_MODE", "template")

from backend.app.main import app as backend_app
from ml_service.api import app as ml_app


class ApiContractTest(unittest.TestCase):
    def test_frontend_facing_backend_routes_remain_available(self) -> None:
        paths = backend_app.openapi()["paths"]
        required = {
            "/health": "get",
            "/api/auth/login": "post",
            "/api/auth/register": "post",
            "/api/user/info": "get",
            "/api/ml/profile/questions": "get",
            "/api/ml/profile/answer": "post",
            "/api/ml/profile/generate": "post",
            "/api/ml/profile/current": "get",
            "/api/ml/learning-path/generate": "post",
            "/profile-builder/start": "post",
            "/profile-builder/answer": "post",
            "/profile-builder/result": "get",
            "/path/list": "get",
            "/path/detail": "get",
            "/path/progress": "get",
            "/path/progress/update": "post",
            "/path/resources": "get",
            "/path/recommend": "get",
            "/path/feedback": "post",
            "/resources": "get",
            "/resources/{resource_id}": "get",
            "/producer/task": "post",
            "/producer/tasks": "get",
            "/producer/task/{task_id}": "get",
            "/producer/result/{task_id}": "get",
            "/producer/chat": "post",
            "/producer/roadmap": "get",
            "/admin/statistics": "get",
            "/admin/producer/tasks": "get",
            "/admin/producer/tasks/{task_id}": "get",
            "/api/feedback": "post",
            "/admin/feedback": "get",
            "/admin/feedback/{feedback_id}/status": "put",
            "/admin/settings": "get",
            "/api/v1/courses/{course_id}/questions": "get",
            "/api/v1/courses/{course_id}/assessment/questions": "get",
            "/api/v1/evaluations/submit": "post",
            "/api/v1/evaluations/history": "get",
            "/api/v1/evaluations/{evaluation_id}": "get",
            "/api/v1/learning/start": "post",
            "/api/v1/profile/analyze": "post",
            "/api/v1/paths/plan": "post",
            "/api/v1/tutor/ask": "post",
        }
        for path, method in required.items():
            self.assertIn(path, paths)
            self.assertIn(method, paths[path])

    def test_backend_facing_ml_routes_remain_available(self) -> None:
        paths = ml_app.openapi()["paths"]
        required = {
            "/health": "get",
            "/diagnose": "post",
            "/recommend": "post",
            "/path": "post",
            "/generate": "post",
            "/feedback": "post",
            "/student/update-profile": "post",
            "/assessment/diagnose": "post",
            "/tutor/ask": "post",
        }
        for path, method in required.items():
            self.assertIn(path, paths)
            self.assertIn(method, paths[path])


if __name__ == "__main__":
    unittest.main()
