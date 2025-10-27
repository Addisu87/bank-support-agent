import secrets
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load environment variables from .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore",  env_file_encoding="utf-8")
    
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
    CACHE_EXPIRE_SECONDS: int = 300  # 5 minutes
    
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
    
    
    @property
    def current_database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        if self.ENV_STATE == "test":
            if self.TEST_DATABASE_URL is None:
                raise ValueError("TEST_DATABASE_URL is not set for test environment")
            return self.TEST_DATABASE_URL
        
        if self.DATABASE_URL is None:
            raise ValueError("DATABASE_URL is not set")
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


settings = get_settings()