from __future__ import annotations

import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))


def percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * ratio) - 1))
    return ordered[index]


def measure(label: str, count: int, request_fn) -> dict:
    durations = []
    statuses = []
    started = time.perf_counter()
    for _ in range(count):
        item_started = time.perf_counter()
        response = request_fn()
        durations.append((time.perf_counter() - item_started) * 1000)
        statuses.append(response.status_code)
    elapsed = time.perf_counter() - started
    return {
        "label": label,
        "requests": count,
        "successes": sum(200 <= status < 300 for status in statuses),
        "p50_ms": round(statistics.median(durations), 2),
        "p95_ms": round(percentile(durations, 0.95), 2),
        "max_ms": round(max(durations), 2),
        "throughput_rps": round(count / elapsed, 2),
    }


def render_report(rows: list[dict]) -> str:
    lines = [
        "# 性能冒烟测试报告",
        "",
        "测试在离线模板模式和临时 SQLite 数据库上单进程顺序执行，用于发现明显性能回退，不替代生产压测。",
        "",
        "| 场景 | 请求数 | 成功数 | P50 | P95 | 最大值 | 吞吐 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['label']} | {row['requests']} | {row['successes']} | {row['p50_ms']} ms | "
            f"{row['p95_ms']} ms | {row['max_ms']} ms | {row['throughput_rps']} req/s |"
        )
    lines.extend(
        [
            "",
            "验收阈值：健康检查 P95 < 250 ms，PBKDF2 登录 P95 < 500 ms，离线同步多智能体生成 P95 < 3 s，成功率 100%。生产环境使用 Redis/RQ 后，创建任务只负责入队，长内容生成通过阶段进度反馈。",
            "",
            "正式答辩前应在目标部署环境补充 20 并发、持续 10 分钟的容量测试和真实星火延迟分布。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="learnpilot-performance-") as temp_dir:
        os.environ["DATABASE_MODE"] = "sqlite"
        os.environ["SQLITE_DATABASE_URL"] = f"sqlite:///{Path(temp_dir) / 'performance.db'}"
        os.environ["USE_ML_SERVICE"] = "false"
        os.environ["PRODUCER_ASYNC_ENABLED"] = "false"
        os.environ["LEARNPILOT_LLM_MODE"] = "template"

        from backend.app.core.database import SessionLocal, engine
        from backend.app.core.security import hash_password
        from backend.app.main import app
        from backend.app.models import Course, KnowledgePoint, User
        from fastapi.testclient import TestClient

        with SessionLocal() as db:
            db.add(Course(id=1, name="人工智能", description="性能测试课程"))
            db.add(KnowledgePoint(id=1, course_id=1, name="卷积神经网络", difficulty="medium"))
            db.add(
                User(
                    username="performance",
                    email="performance@example.com",
                    password_hash=hash_password("performance-secret"),
                    role="student",
                    status="active",
                )
            )
            db.commit()

        client = TestClient(app)
        login_payload = {"email": "performance@example.com", "password": "performance-secret"}
        token = client.post("/api/auth/login", json=login_payload).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        rows = [
            measure("健康检查", 50, lambda: client.get("/health")),
            measure("登录鉴权", 20, lambda: client.post("/api/auth/login", json=login_payload)),
            measure(
                "离线同步资源生成",
                5,
                lambda: client.post(
                    "/producer/task",
                    headers=headers,
                    json={"topic": "卷积神经网络", "requirement": "大二入门复习", "types": ["lecture", "exercise"]},
                ),
            ),
        ]
        thresholds = {"健康检查": 250, "登录鉴权": 500, "离线同步资源生成": 3000}
        failures = [
            row for row in rows if row["successes"] != row["requests"] or row["p95_ms"] >= thresholds[row["label"]]
        ]
        report_path = ROOT / "docs" / "performance-report.md"
        report_path.write_text(render_report(rows), encoding="utf-8")
        for row in rows:
            print(row)
        client.close()
        engine.dispose()
        if failures:
            raise SystemExit(f"Performance thresholds failed: {failures}")
        print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
