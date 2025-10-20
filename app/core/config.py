from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets
from functools import lru_cache


class Settings(BaseSettings):
    # Load environment variables from .env file
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    
       # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bank Support Agent"
    
    
    DATABASE_URL: str | None = None
    PYDANTIC_AI_MODEL: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    BASE_URL: str | None = None
    REDIS_URL: str | None = None
    LOGFIRE_TOKEN: str | None = None
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60  * 24
    OBP_BASE_URL: str | None = None
    OBP_ACCESS_TOKEN: str | None = None
    # Redis Cache
    REDIS_URL: str | None = None
    CACHE_EXPIRE_SECONDS: int = 300  # 5 minutes

@lru_cache()
def get_settings():
    return Settings()    

settings = get_settings()