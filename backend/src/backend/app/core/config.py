from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="LearnPilot Backend", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_port: int = Field(default=8001, alias="APP_PORT")

    database_mode: str = Field(default="mysql", alias="DATABASE_MODE")
    postgres_database_url: str | None = Field(default=None, alias="DATABASE_URL")
    sqlite_database_url: str = Field(default="sqlite:///./learnpilot.db", alias="SQLITE_DATABASE_URL")

    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="", alias="MYSQL_PASSWORD")
    mysql_database: str = Field(default="learning_agent", alias="MYSQL_DATABASE")

    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    ml_service_url: str = Field(default="http://127.0.0.1:8000", alias="ML_SERVICE_URL")
    use_ml_service: bool = Field(default=True, alias="USE_ML_SERVICE")
    ml_service_timeout_seconds: float = Field(default=90.0, alias="ML_SERVICE_TIMEOUT_SECONDS")
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_expire_minutes: int = Field(default=1440, alias="JWT_EXPIRE_MINUTES")
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="REDIS_URL")
    producer_async_enabled: bool = Field(default=True, alias="PRODUCER_ASYNC_ENABLED")
    producer_job_timeout_seconds: int = Field(default=600, alias="PRODUCER_JOB_TIMEOUT_SECONDS")
    video_render_enabled: bool = Field(default=False, alias="LEARNPILOT_VIDEO_RENDER_ENABLED")
    video_output_dir: str = Field(default="backend/generated/videos", alias="LEARNPILOT_VIDEO_OUTPUT_DIR")
    xfyun_tts_app_id: str = Field(default="", alias="XFYUN_TTS_APP_ID")
    xfyun_tts_api_key: str = Field(default="", alias="XFYUN_TTS_API_KEY")
    xfyun_tts_api_secret: str = Field(default="", alias="XFYUN_TTS_API_SECRET")
    xfyun_tts_voice: str = Field(default="x4_xiaoyan", alias="XFYUN_TTS_VOICE")
    xfyun_tts_speed: int = Field(default=50, ge=0, le=100, alias="XFYUN_TTS_SPEED")
    xfyun_tts_volume: int = Field(default=55, ge=0, le=100, alias="XFYUN_TTS_VOLUME")
    xfyun_tts_timeout_seconds: int = Field(default=45, ge=5, le=180, alias="XFYUN_TTS_TIMEOUT_SECONDS")
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    spark_api_password: str = Field(default="", alias="SPARK_API_PASSWORD")
    spark_model: str = Field(default="xop3qwen1b7", alias="SPARK_MODEL")
    spark_base_url: str = Field(default="https://maas-api.cn-huabei-1.xf-yun.com/v2", alias="SPARK_BASE_URL")
    spark_timeout_seconds: int = Field(default=90, alias="SPARK_TIMEOUT_SECONDS")
    qwen_model: str = Field(default="qwen3.7-plus", alias="QWEN_MODEL")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="QWEN_BASE_URL",
    )
    qwen_timeout_seconds: int = Field(default=30, alias="QWEN_TIMEOUT_SECONDS")
    learnpilot_llm_provider: str = Field(default="spark", alias="LEARNPILOT_LLM_PROVIDER")
    learnpilot_llm_mode: str = Field(default="auto", alias="LEARNPILOT_LLM_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        mode = self.database_mode.lower()
        if mode == "sqlite":
            return self.sqlite_database_url
        if mode == "postgres":
            if not self.postgres_database_url:
                raise ValueError("DATABASE_URL is required when DATABASE_MODE=postgres")
            if self.postgres_database_url.startswith("postgres://"):
                return self.postgres_database_url.replace("postgres://", "postgresql+psycopg2://", 1)
            if self.postgres_database_url.startswith("postgresql://"):
                return self.postgres_database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return self.postgres_database_url
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def is_sqlite(self) -> bool:
        return self.database_mode.lower() == "sqlite"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def xfyun_tts_credentials(self) -> tuple[str, str] | None:
        if self.xfyun_tts_api_key and self.xfyun_tts_api_secret:
            return self.xfyun_tts_api_key, self.xfyun_tts_api_secret
        if ":" in self.spark_api_password:
            api_key, api_secret = self.spark_api_password.split(":", 1)
            if api_key and api_secret:
                return api_key, api_secret
        return None

    @property
    def video_output_path(self) -> Path:
        configured = Path(self.video_output_dir).expanduser()
        if configured.is_absolute():
            return configured.resolve()
        repository_root = Path(__file__).resolve().parents[5]
        return (repository_root / configured).resolve()

    @property
    def video_font_candidates(self) -> list[Path]:
        return [
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/msyhbd.ttc"),
            Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        ]

    def validate_runtime(self) -> None:
        if self.app_env.lower() != "production":
            return
        if self.jwt_secret_key in {"change-me-in-production", "replace-with-a-long-random-secret"}:
            raise ValueError("JWT_SECRET_KEY must be replaced in production")
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters in production")
        if self.cors_origins.strip() == "*":
            raise ValueError("CORS_ORIGINS must list trusted origins in production")
        if self.app_debug:
            raise ValueError("APP_DEBUG must be false in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
