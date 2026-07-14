"""Central paths and environment-backed service settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ML_ROOT = Path(os.getenv("LEARNPILOT_ML_ROOT", PACKAGE_DIR.parents[1])).expanduser().resolve()
DATA_DIR = ML_ROOT / "data"
GENERATED_DATA_DIR = DATA_DIR / "generated"
_training_data_value = os.getenv("LEARNPILOT_TRAINING_DATA_DIR", "").strip()
_training_data_path = Path(_training_data_value).expanduser() if _training_data_value else None
if _training_data_path is not None and not _training_data_path.is_absolute():
    _training_data_path = ML_ROOT.parent / _training_data_path
TRAINING_DATA_DIR = _training_data_path.resolve() if _training_data_path is not None else GENERATED_DATA_DIR
ARTIFACT_DIR = ML_ROOT / "artifacts"
DEPLOYED_MODEL_DIR = ML_ROOT / "models" / "ranker"
_ranker_model_dir_value = os.getenv("LEARNPILOT_RANKER_MODEL_DIR", "").strip()
RANKER_MODEL_DIR = (
    Path(_ranker_model_dir_value).expanduser().resolve()
    if _ranker_model_dir_value
    else DEPLOYED_MODEL_DIR
)
REPORT_DIR = ML_ROOT / "reports"
DOTENV_CANDIDATES = (ML_ROOT / ".env", ML_ROOT.parent / ".env")


@dataclass(frozen=True)
class LLMSettings:
    mode: str = "auto"
    provider: str = "spark"
    api_key: str | None = None
    model: str = "xop3qwen1b7"
    base_url: str = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
    timeout_seconds: int = 90

    @classmethod
    def from_env(cls) -> LLMSettings:
        provider = os.getenv("LEARNPILOT_LLM_PROVIDER", "spark").strip().lower()
        if provider not in {"spark", "qwen"}:
            provider = "spark"
        if provider == "qwen":
            api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
            model = os.getenv("QWEN_MODEL", "qwen3.7-plus")
            base_url = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            timeout = os.getenv("QWEN_TIMEOUT_SECONDS", "30")
        else:
            api_key = os.getenv("SPARK_API_PASSWORD")
            model = os.getenv("SPARK_MODEL", "xop3qwen1b7")
            base_url = os.getenv("SPARK_BASE_URL", "https://maas-api.cn-huabei-1.xf-yun.com/v2")
            timeout = os.getenv("SPARK_TIMEOUT_SECONDS", "90")
        return cls(
            mode=os.getenv("LEARNPILOT_LLM_MODE", "auto").lower(),
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url.rstrip("/"),
            timeout_seconds=int(timeout),
        )
