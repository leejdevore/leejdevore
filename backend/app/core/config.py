"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://devsight:devsight_dev@localhost:5432/devsight"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # AI
    anthropic_api_key: str = ""

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Application
    debug: bool = False
    environment: str = "development"

    # Tiles
    tiles_url: str = "http://localhost:3001"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
