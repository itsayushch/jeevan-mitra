import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    NODE_ENV: str = "development"
    PORT: int = 4000
    HOST: str = "0.0.0.0"
    DATABASE_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "jeevanmitra.db")
    JWT_SECRET: str = "supersecret_jwt_key_for_dev_only"
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
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    QUALIFICATION_REVIEW_DAYS: int = 180
    OPPORTUNITY_REVIEW_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()

if settings.NODE_ENV == "production":
    if not settings.JWT_SECRET or settings.JWT_SECRET == "supersecret_jwt_key_for_dev_only":
        raise ValueError("JWT_SECRET must be set in production")
