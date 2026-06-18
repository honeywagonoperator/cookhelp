from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


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

    # App
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Embedding
    embedding_dimension: int = Field(default=1024, validation_alias="EMBEDDING_DIMENSION")
    embedding_model: str = Field(
        default="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        validation_alias="EMBEDDING_MODEL",
    )

    @property
    def async_database_url(self) -> str:
        return self.database_url


settings = Settings()