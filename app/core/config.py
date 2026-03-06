from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    LINKEDIN_CLIENT_ID: str
    LINKEDIN_CLIENT_SECRET: str

    ENV: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()