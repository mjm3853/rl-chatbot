"""Server configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/rl_chatbot.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # OpenAI (inherited from existing config)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_temperature: float = 1.0

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
