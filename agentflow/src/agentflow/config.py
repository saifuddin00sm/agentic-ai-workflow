"""Configuration via environment variables using pydantic-settings."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514")

    # Optional tools
    tavily_api_key: str | None = Field(default=None, description="Tavily API key (optional)")

    # Pipeline
    pipeline_stage_timeout_s: int = Field(default=60, ge=10, le=300)
    pipeline_max_research_tasks: int = Field(default=8, ge=1, le=20)
    pipeline_research_concurrency: int = Field(default=4, ge=1, le=10)
    pipeline_max_agent_iterations: int = Field(default=10, ge=3, le=30)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json", pattern="^(json|text)$")


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
