# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "Meetyfi"
    MONGODB_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GOOGLE_MAPS_API_KEY: str
    
    # Email settings
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    MAIL_FROM: str | None = None
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
