from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "LinkAid"
    app_version: str = "0.1.0"
    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    checkpoint_db_path: str = Field(default="./data/checkpoints.db", alias="CHECKPOINT_DB_PATH")
    outreach_limit_db_path: str = Field(
        default="./data/outreach_limits.db", alias="OUTREACH_LIMIT_DB_PATH"
    )
    max_daily_outreach: int = Field(default=20, alias="MAX_DAILY_OUTREACH")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")

    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com", alias="LANGFUSE_HOST"
    )

    database_url: str = Field(
        default="sqlite:///./data/linkaid.db", alias="DATABASE_URL"
    )
    chroma_persist_dir: str = Field(
        default="./data/chroma", alias="CHROMA_PERSIST_DIR"
    )

    @property
    def is_development(self) -> bool:
        return self.env.lower() in ("development", "dev", "local")

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
