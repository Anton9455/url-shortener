"""Configuration settings for the URL Shortener application."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_token: str = Field(..., description="API token для авторизации")
    database_url: str = Field(
        default="sqlite:////data/shortener.db",
        description="Database connection string",
    )
    base_url: str = Field(..., description="Base URL для сокращённых ссылок")
    app_version: str = Field(default="1.0.0", description="Application version")
    link_ttl_minutes: int = Field(
        default=15,
        description="Время жизни короткой ссылки в минутах",
    )
