"""Application settings, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- App ----
    app_name: str = "InterviewPilot AI"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api"

    # ---- Security ----
    secret_key: str = "dev-only-change-me-before-deploying"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"
    # NoDecode: accept a plain comma-separated string, not JSON, from the environment.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # ---- Database ----
    database_url: str = (
        "postgresql+psycopg://interviewpilot:interviewpilot@localhost:5433/interviewpilot"
    )
    redis_url: str = "redis://localhost:6380/0"

    # ---- AI ----
    ai_provider: str = "auto"  # auto | openai | mock
    openai_api_key: str | None = None
    openai_model: str = "gpt-5"
    openai_model_fast: str = "gpt-5-mini"
    openai_stt_model: str = "gpt-4o-transcribe"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"

    # ---- Auth ----
    auth_provider: str = "local"  # local | clerk
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None

    # ---- Email verification ----
    require_email_verification: bool = True
    otp_ttl_minutes: int = 10
    otp_max_attempts: int = 5
    otp_max_sends_per_hour: int = 5
    otp_resend_cooldown_seconds: int = 60

    # ---- Email delivery ----
    email_provider: str = "auto"  # auto | smtp | console
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    # ---- Storage ----
    storage_dir: str = "./storage"
    max_upload_mb: int = 10

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_ai_provider(self) -> str:
        """`auto` picks OpenAI when a key exists, otherwise the deterministic mock."""
        if self.ai_provider == "auto":
            return "openai" if self.openai_api_key else "mock"
        return self.ai_provider

    @property
    def resolved_email_provider(self) -> str:
        """`auto` picks SMTP when a host is configured, otherwise logs to the console."""
        if self.email_provider == "auto":
            return "smtp" if self.smtp_host else "console"
        return self.email_provider


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
