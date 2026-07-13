"""Installed command-line entry points for local and deployment workflows."""

from __future__ import annotations

import json
import os

from .application.pipeline import LearningMLPipeline
from .config import GENERATED_DATA_DIR, ML_ROOT
from .datasets.demo_cases import DEMO_CASES
from .datasets.synthetic import SEED, write_synthetic_dataset
from .evaluation import run_builtin_evaluation
from .infrastructure.content_generator import OpenAICompatibleClient, load_dotenv_if_present
from .training import train_from_generated_data


def _print(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def generate() -> None:
    _print(write_synthetic_dataset(GENERATED_DATA_DIR, seed=SEED))


def train() -> None:
    _print(train_from_generated_data())


def evaluate() -> None:
    os.environ.setdefault("LEARNPILOT_LLM_MODE", "template")
    _print(run_builtin_evaluation(ML_ROOT, write_report=True))


def demo() -> None:
    student = DEMO_CASES["steady"]["student"]
    _print(LearningMLPipeline().recommend(**student, top_k=5))


def check_qwen() -> None:
    load_dotenv_if_present()
    os.environ["LEARNPILOT_LLM_MODE"] = "auto"
    os.environ["LEARNPILOT_LLM_PROVIDER"] = "qwen"
    client = OpenAICompatibleClient.from_env()
    if client is None or client.provider != "qwen":
        raise SystemExit("DASHSCOPE_API_KEY is required for the Qwen connectivity check.")
    result = client.generate('请仅返回 JSON：{"title":"Qwen 连通性测试","explanation":"连接成功"}')
    _print({"provider": client.provider, "model": client.model, "result": result})


def check_spark() -> None:
    load_dotenv_if_present()
    os.environ["LEARNPILOT_LLM_MODE"] = "auto"
    os.environ["LEARNPILOT_LLM_PROVIDER"] = "spark"
    client = OpenAICompatibleClient.from_env()
    if client is None or client.provider != "spark":
        raise SystemExit("SPARK_API_PASSWORD is required for the Spark connectivity check.")
    result = client.generate('请仅返回 JSON：{"title":"讯飞星火连通性测试","explanation":"连接成功"}')
    _print({"provider": client.provider, "model": client.model, "result": result})


def serve() -> None:
    import uvicorn

    uvicorn.run(
        "ml_service.api:app",
        host=os.getenv("ML_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", os.getenv("ML_PORT", "8000"))),
    )
