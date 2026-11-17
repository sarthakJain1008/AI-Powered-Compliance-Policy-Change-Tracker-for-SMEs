"""Application configuration loaded from environment / .env file.

All settings are centralised here via pydantic-settings so every module
imports from a single, validated source of truth.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Values are read from environment variables first, then from a `.env`
    file in the working directory (or project root).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Allow extra env-vars without raising a validation error
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/compliance_tracker"

    # ------------------------------------------------------------------ #
    # JWT / token settings
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = "change_this_to_a_long_random_secret_key_minimum_32_chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440       # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24

    # ------------------------------------------------------------------ #
    # Application metadata
    # ------------------------------------------------------------------ #
    APP_NAME: str = "Compliance Tracker"
    FRONTEND_URL: str = "http://localhost:3000"

    # ------------------------------------------------------------------ #
    # SMTP / email
    # ------------------------------------------------------------------ #
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_NAME: str = "Compliance Tracker"
    EMAILS_FROM_EMAIL: str = "no-reply@compliance-tracker.com"


# Singleton instance imported throughout the application
settings = Settings()
