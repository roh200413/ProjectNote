from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ProjectNote API"
    environment: str = "local"
    database_url: str = Field(default="sqlite:///./projectnote.db")
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
