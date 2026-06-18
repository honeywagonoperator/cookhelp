import logging

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    postgres_db: str = Field(default="cookhelp", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="cookhelp", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="cookhelp", validation_alias="POSTGRES_PASSWORD")
    database_url: str = Field(
        default="postgresql+asyncpg://cookhelp:cookhelp@localhost:5432/cookhelp",
        validation_alias="DATABASE_URL",
    )

    # OpenRouter
    openrouter_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")

    # Telegram
    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    bot_use_webhook: bool = Field(default=False, validation_alias="BOT_USE_WEBHOOK")
    bot_webhook_url: str = Field(default="", validation_alias="BOT_WEBHOOK_URL")

    # App
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = logging.getLevelNamesMapping()
        if v.upper() not in valid:
            raise ValueError(f"Invalid log level: {v}. Valid: {', '.join(valid)}")
        return v.upper()
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Embedding
    embedding_dimension: int = Field(default=2048, validation_alias="EMBEDDING_DIMENSION")
    embedding_model: str = Field(
        default="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        validation_alias="EMBEDDING_MODEL",
    )

    @property
    def async_database_url(self) -> str:
        return self.database_url


settings = Settings()