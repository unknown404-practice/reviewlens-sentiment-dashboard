"""
ReviewLens Backend Configuration Module
=======================================
Typed environment settings management using Pydantic Settings.
Reads configuration from environment variables with safe local defaults.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings schema and environment variable loader."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = Field(default="ReviewLens Sentiment API", description="Public name of the application")
    APP_VERSION: str = Field(default="1.0.0", description="API semantic version")
    ENVIRONMENT: str = Field(default="development", description="Runtime environment (development, production, test)")
    HOST: str = Field(default="127.0.0.1", description="Host address for binding")
    PORT: int = Field(default=8000, description="Listening port number")
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501,http://127.0.0.1:8501,null",
        description="Comma-separated list of permitted CORS origins",
    )
    MAX_REVIEWS_PER_REQUEST: int = Field(default=50, ge=1, le=500, description="Max reviews returned or processed per batch")
    MAX_TEXT_LENGTH: int = Field(default=5000, ge=10, le=50000, description="Max character length for review text analysis")
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30, ge=1, le=120, description="HTTP and scraper timeout in seconds")
    ENABLE_PLAYWRIGHT_SCRAPING: bool = Field(default=False, description="Flag to enable/disable live Playwright extraction")
    RATE_LIMIT_PER_MINUTE: int = Field(default=30, ge=1, le=600, description="Rate limit per client IP per minute")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level threshold")

    @field_validator("ENABLE_PLAYWRIGHT_SCRAPING", mode="before")
    @classmethod
    def parse_bool_safe(cls, v: object) -> bool:
        """Safely parse boolean values from string or boolean representations."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"true", "1", "yes", "t", "on"}
        if isinstance(v, (int, float)):
            return bool(v)
        return False

    @property
    def cors_origins(self) -> List[str]:
        """Return allowed origins as a clean list of strings."""
        if isinstance(self.ALLOWED_ORIGINS, list):
            return [o.strip() for o in self.ALLOWED_ORIGINS if o.strip()]
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8501", "http://127.0.0.1:8501", "null"]



@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retrieve cached application configuration settings.

    Returns:
        Singleton instance of Settings.
    """
    return Settings()
