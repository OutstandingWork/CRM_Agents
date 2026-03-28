from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SalesOps Agent API"
    environment: str = "development"
    crm_provider: str = "mock"
    api_prefix: str = "/api"
    espo_base_url: str = "http://espocrm"
    espo_api_key: str | None = None
    espo_username: str = "admin"
    espo_password: str = "password"
    espo_seed_demo_data: bool = True
    llm_provider: str = "gemini"
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CRM_AGENT_GEMINI_API_KEY", "GEMINI_API_KEY"),
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash-lite",
        validation_alias=AliasChoices("CRM_AGENT_GEMINI_MODEL", "GEMINI_MODEL"),
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://frontend:5173"]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CRM_AGENT_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
