# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    FRONTEND_BASE_URL: str = "https://yourfrontend.com"
    ANALYTICS_URL: str | None = None
    AI_SUMMARY_URL: str | None = None
    DATABASE_URL: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
