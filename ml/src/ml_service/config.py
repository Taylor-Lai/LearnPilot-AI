"""Central paths and environment-backed service settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ML_ROOT = PACKAGE_DIR.parents[1]
DATA_DIR = ML_ROOT / "data"
GENERATED_DATA_DIR = DATA_DIR / "generated"
ARTIFACT_DIR = ML_ROOT / "artifacts"
REPORT_DIR = ML_ROOT / "reports"
DOTENV_CANDIDATES = (ML_ROOT / ".env", ML_ROOT.parent / ".env")


@dataclass(frozen=True)
class LLMSettings:
    mode: str = "auto"
    api_key: str | None = None
    model: str = "qwen3.7-plus"
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> LLMSettings:
        return cls(
            mode=os.getenv("LEARNPILOT_LLM_MODE", "auto").lower(),
            api_key=os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY"),
            model=os.getenv("QWEN_MODEL", "qwen3.7-plus"),
            base_url=os.getenv("QWEN_BASE_URL", cls.base_url).rstrip("/"),
            timeout_seconds=int(os.getenv("QWEN_TIMEOUT_SECONDS", "30")),
        )
