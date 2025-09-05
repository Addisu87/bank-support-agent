from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets

class Settings(BaseSettings):
    # Load environment variables from .env file
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    
    DATABASE_URL: str | None = None
    PYDANTIC_AI_MODEL: str | None = None
    OPENAI_API_KEY: str | None = None
    REDIS_URL: str | None = None
    LOGFIRE_TOKEN: str | None = None
    JWT_SECRET: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"


settings = Settings()