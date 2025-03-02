from pydantic_settings import BaseSettings  # Use pydantic_settings instead of pydantic
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"  # Default value for algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # Default value of 24 hours

    # Email Configuration (Hostinger SMTP)
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str

    class Config:
        # The env_file tells pydantic where to load environment variables from
        env_file = ".env"

# Instantiate the settings object
settings = Settings()

# Optional: You can add custom validations for the environment variables if needed
if not settings.SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
