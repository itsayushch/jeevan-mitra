import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any


class Settings(BaseSettings):
    APP_ENV: str = "local"  # "local" | "staging" | "production"
    NODE_ENV: str = "development"
    PORT: int = 4000
    HOST: str = "0.0.0.0"

    DATABASE_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "jeevanmitra.db")
    DATABASE_URL: str = "sqlite:///./jeevanmitra.db"
    ALLOW_SQLITE_IN_PRODUCTION: bool = False

    JWT_SECRET: str = "supersecret_jwt_key_for_dev_only_32_chars_min_len!!"
    JWT_ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7

    WORKER_API_KEY: str = ""
    WORKER_ID: str = ""
    WORKER_NAME: str = ""

    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    AI_API_KEY: str = ""

    DEFAULT_DISTRICT: str = "Moradabad"
    DEFAULT_STATE: str = "Uttar Pradesh"
    CONFIDENCE_THRESHOLD: float = 0.75
    API_PREFIX: str = "/api/v1"

    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    FRONTEND_URL: str = "http://localhost:3000"

    STORAGE_PROVIDER: str = "local"  # "local" | "s3" | "gcs"
    STORAGE_BUCKET: str = "jeevanmitra-private"
    STORAGE_PRIVATE_PREFIX: str = "evidence/"
    EXPORT_RETENTION_DAYS: int = 7
    PLANNING_MIN_CELL_COUNT: int = 5

    NEXT_PUBLIC_API_BASE_URL: str = "http://localhost:4000/api/v1"
    NEXT_PUBLIC_DEMO_AUTH_FALLBACK: bool = False

    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    QUALIFICATION_REVIEW_DAYS: int = 180
    OPPORTUNITY_REVIEW_DAYS: int = 30

    IVR_PROVIDER: str = "mock"
    IVR_DEFAULT_LANGUAGE: str = "hi-IN"
    IVR_SESSION_TIMEOUT_SECONDS: int = 600
    IVR_MAX_INVALID_ATTEMPTS: int = 2
    IVR_SIMULATOR_ENABLED: bool = True
    IVR_AUDIO_BASE_URL: str = ""
    EXOTEL_SID: str = ""
    EXOTEL_API_KEY: str = ""
    EXOTEL_API_TOKEN: str = ""
    EXOTEL_CALLER_ID: str = ""
    EXOTEL_WEBHOOK_SECRET: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    PUBLIC_BASE_URL: str = "http://localhost:4000"

    RELEASE_VERSION: str = "2.0.0-rc1"
    GIT_COMMIT_SHA: str = "dev-local"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production" or self.NODE_ENV.lower() == "production"

    def is_staging(self) -> bool:
        return self.APP_ENV.lower() == "staging"

    def validate_production_constraints(self) -> None:
        """Enforces critical security and environment invariants."""
        if self.is_production():
            # 1. JWT_SECRET strength
            if (
                not self.JWT_SECRET
                or "supersecret" in self.JWT_SECRET
                or len(self.JWT_SECRET) < 32
            ):
                raise ValueError(
                    "Production startup rejected: JWT_SECRET must be configured with at least 32 cryptographically strong characters."
                )

            # 2. Database engine check (reject SQLite unless explicit demo flag set)
            if ("sqlite" in self.DATABASE_URL or "sqlite" in self.DATABASE_PATH) and not self.ALLOW_SQLITE_IN_PRODUCTION:
                raise ValueError(
                    "Production startup rejected: SQLite is not approved for production deployment without ALLOW_SQLITE_IN_PRODUCTION=true."
                )

            # 3. Demo auth fallback rejected
            if self.NEXT_PUBLIC_DEMO_AUTH_FALLBACK:
                raise ValueError(
                    "Production startup rejected: NEXT_PUBLIC_DEMO_AUTH_FALLBACK must be false in production."
                )

        if self.is_staging():
            if self.NEXT_PUBLIC_DEMO_AUTH_FALLBACK:
                raise ValueError(
                    "Staging startup rejected: NEXT_PUBLIC_DEMO_AUTH_FALLBACK must be false in staging."
                )

    def get_safe_config_report(self) -> Dict[str, Any]:
        """Returns safe configuration summary without exposing sensitive credentials."""
        db_type = "sqlite" if "sqlite" in self.DATABASE_URL else "postgresql"
        return {
            "app_env": self.APP_ENV,
            "release_version": self.RELEASE_VERSION,
            "git_commit_sha": self.GIT_COMMIT_SHA[:8] if len(self.GIT_COMMIT_SHA) >= 8 else self.GIT_COMMIT_SHA,
            "database_provider": db_type,
            "jwt_secret_configured": bool(self.JWT_SECRET and len(self.JWT_SECRET) >= 32 and "supersecret" not in self.JWT_SECRET),
            "jwt_access_expiry_minutes": self.JWT_ACCESS_TOKEN_MINUTES,
            "refresh_token_expiry_days": self.REFRESH_TOKEN_DAYS,
            "cors_allowed_origins_count": len(self.CORS_ALLOWED_ORIGINS),
            "storage_provider": self.STORAGE_PROVIDER,
            "storage_bucket": self.STORAGE_BUCKET,
            "export_retention_days": self.EXPORT_RETENTION_DAYS,
            "planning_min_cell_count": self.PLANNING_MIN_CELL_COUNT,
            "demo_auth_fallback_enabled": self.NEXT_PUBLIC_DEMO_AUTH_FALLBACK,
            "sentry_enabled": bool(self.SENTRY_DSN),
            "log_level": self.LOG_LEVEL,
            "ivr_provider": self.IVR_PROVIDER,
            "ivr_simulator_enabled": self.IVR_SIMULATOR_ENABLED,
        }


settings = Settings()

# Validate startup constraints
try:
    settings.validate_production_constraints()
except ValueError as e:
    # Only raise in production/staging environments
    if settings.is_production() or settings.is_staging():
        raise
