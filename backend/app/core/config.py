# backend/app/core/config.py

from pydantic_settings import BaseSettings
from typing import ClassVar


class Settings(BaseSettings):
    # App
    APP_NAME: str = "IntelliVerify"
    DEBUG: bool = True
    SECRET_KEY: str

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ML Service
    ML_SERVICE_URL: str = "http://localhost:8001"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"          # tells Pydantic to read from .env file
        env_file_encoding = "utf-8"
        case_sensitive = True      # DATABASE_URL ≠ database_url


# Single instance — import this everywhere
settings = Settings()