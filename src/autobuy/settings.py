"""Application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AUTOBUY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://autobuy:autobuy@localhost:5432/autobuy"
    redis_url: str = "redis://localhost:6379/0"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    internal_service_token: str | None = None
    redis_namespace: str = "autobuy"
    worker_heartbeat_ttl_seconds: int = Field(default=30, ge=5, le=300)
    worker_lease_ttl_seconds: int = Field(default=45, ge=10, le=600)
    profile_store_dir: Path = Path("data/profile-artifacts")


@lru_cache
def get_settings() -> Settings:
    return Settings()
