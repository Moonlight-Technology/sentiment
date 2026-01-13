"""Configuration for the sentiment worker."""
from functools import lru_cache
from typing import Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SENTIMENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///data/sentiment.db"
    model_name: str = "mdhugol/indonesia-bert-sentiment-classification"
    model_revision: Optional[str] = None
    model_version: Optional[str] = None
    batch_limit: int = 32
    pipeline_stage: str = "batch"
    device: Optional[str] = None
    label_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "LABEL_0": "negative",
            "LABEL_1": "neutral",
            "LABEL_2": "positive",
            "NEGATIVE": "negative",
            "NEG": "negative",
            "NEUTRAL": "neutral",
            "NEU": "neutral",
            "POSITIVE": "positive",
            "POS": "positive",
        }
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
