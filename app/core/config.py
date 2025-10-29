import os
import secrets
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    # Load environment variables from .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")
    ENV_STATE: Literal["dev", "prod", "test"] = "dev"


class GlobalConfig(BaseConfig):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bank Support Agent"

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None

    # AI/ML
    PYDANTIC_AI_MODEL: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_URL: str | None = None

    # Redis
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


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_", extra="ignore")
    # fallback if DATABASE_URL not in env
    DATABASE_URL: str = os.environ.get(
        "DEV_DATABASE_URL", "postgresql+asyncpg://postgres:bank87@localhost:5432/bankdb"
    )


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_", extra="ignore")
    DEBUG: bool = False


class TestConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="TEST_", extra="ignore")
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:bank87@localhost:5432/test_bankdb"
    DB_FORCE_ROLL_BACK: bool = True
    PYDANTIC_AI_MODEL: str = "test-model"
    DEEPSEEK_API_KEY: str = "test-key"


@lru_cache()
def get_settings() -> GlobalConfig:
    env_state = BaseConfig().ENV_STATE
    configs: dict[str, type[GlobalConfig]] = {
        "dev": DevConfig,
        "prod": ProdConfig,
        "test": TestConfig,
    }
    return configs[env_state]()
    

settings = get_settings()
