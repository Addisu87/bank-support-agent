import secrets
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load environment variables
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")
    
    # Environment
    ENV_STATE: Literal["dev", "prod", "test"] = "dev"

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bank Support Agent"
    
    # Database
    DATABASE_URL: str | None = None
    TEST_DATABASE_URL: str | None = None
    
    # AI/ML Configuration
    PYDANTIC_AI_MODEL: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    BASE_URL: str | None = None
    
    # Redis Cache
    REDIS_URL: str | None = None
    CACHE_EXPIRE_SECONDS: int = 300
    
    # Logging
    LOGFIRE_TOKEN: str | None = None
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # App
    PORT: int = 8000
    DEBUG: bool = True
    
    # Email
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str | None = None
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = False
    
    @property
    def current_database_url(self) -> str:
        """Get PostgreSQL database URL - convert format if needed"""
        # Use test database for test environment
        if self.ENV_STATE == "test":
            if not self.TEST_DATABASE_URL:
                raise ValueError("TEST_DATABASE_URL is required for test environment")
            db_url = self.TEST_DATABASE_URL
        else:
            if not self.DATABASE_URL:
                raise ValueError("DATABASE_URL is required")
            db_url = self.DATABASE_URL
        
        # Convert postgres:// to postgresql+asyncpg:// for SQLAlchemy
        if db_url.startswith("postgres://"):
            return db_url.replace("postgres://", "postgresql+asyncpg://")
        return db_url


@lru_cache()
def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


settings = get_settings()