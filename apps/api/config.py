from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parent
ROOT_DIR = API_DIR.parent.parent


class Settings(BaseSettings):
    # apps/api/.env first, then repo root .env (root wins if both define a key)
    model_config = SettingsConfigDict(
        env_file=(API_DIR / ".env", ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://katalyzu:katalyzu@localhost:5432/katalyzu"
    redis_url: str = "redis://localhost:6379/0"

    supabase_url: str = "https://ybvxucxndarcycjzmywt.supabase.co"
    supabase_project_ref: str = "ybvxucxndarcycjzmywt"

    jwt_secret: str = "change-me-in-production"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    llm_provider: str = "gemini"
    llm_mock: bool = False

    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"
    resend_webhook_secret: str = ""

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @field_validator("database_url", mode="after")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://") and "+asyncpg" not in value:
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
