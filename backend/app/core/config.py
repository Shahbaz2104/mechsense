"""Application settings loaded from environment variables and .env files."""

import json
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MechSense API"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://shahbaz@localhost:5432/mechsense"
    test_database_url: str = "postgresql+psycopg://shahbaz@localhost:5432/mechsense_test"

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    # Accepts a comma-separated list (documented in .env.example) or a JSON array.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    log_level: str = "INFO"

    simulation_seed: int = 42
    simulation_max_batch: int = 500

    import_max_file_mb: int = 10
    import_max_rows: int = 100_000

    default_page_size: int = 25
    max_page_size: int = 500

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [origin.strip() for origin in text.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
