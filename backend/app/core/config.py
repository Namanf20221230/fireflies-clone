from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fireflies Clone API"
    database_url: str = "sqlite:///./data/fireflies.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    upload_dir: str = "./data/uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
