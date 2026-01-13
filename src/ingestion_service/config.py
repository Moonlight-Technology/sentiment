"""Configuration for ingestion service."""
from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INGESTION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    feed_url: AnyHttpUrl
    source_type: str = "rss_feed"
    language: str = "en"
    storage_path: Path = Path("data/text_items.jsonl")
    database_url: str = "sqlite:///data/sentiment.db"
    csv_path: Path | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
