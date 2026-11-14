from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "BrandSentinel"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "brandsentinel_secret_key_change_in_production_jwt_2026_super_secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Persistence
    DATABASE_URL: str = "sqlite:///./brandsentinel.db"
    UPLOAD_DIR: str = "./uploads"

    # AI Configuration
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-004"
    LLM_MODEL: str = "gemini-2.0-flash"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure uploads directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
