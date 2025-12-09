from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Opinion Platform"
    DATABASE_URL: str = "sqlite:///./opinion.db"
    JWT_SECRET: str = "supersecret123"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"

settings = Settings()
