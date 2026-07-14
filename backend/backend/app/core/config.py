from functools import lru_cache

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
    producer_job_timeout_seconds: int = Field(default=180, alias="PRODUCER_JOB_TIMEOUT_SECONDS")
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    spark_api_password: str = Field(default="", alias="SPARK_API_PASSWORD")
    spark_model: str = Field(default="4.0Ultra", alias="SPARK_MODEL")
    spark_base_url: str = Field(default="https://spark-api-open.xf-yun.com/v1", alias="SPARK_BASE_URL")
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
