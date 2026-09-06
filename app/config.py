"""
Configuration settings for Script-to-Screen Guardian.

All secrets are pulled from environment variables — never hardcode credentials.
Copy `.env.example` to `.env` and fill in real values before running.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Google Cloud / Gemini ---
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

    # --- ClickHouse (partner integration) ---
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    clickhouse_native_port: int = int(os.getenv("CLICKHOUSE_NATIVE_PORT", "9000"))
    clickhouse_database: str = os.getenv("CLICKHOUSE_DATABASE", "production_db")
    clickhouse_user: str = os.getenv("CLICKHOUSE_USER", "default")
    clickhouse_password: str = os.getenv("CLICKHOUSE_PASSWORD", "")

    # --- App ---
    app_env: str = os.getenv("APP_ENV", "development")
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
