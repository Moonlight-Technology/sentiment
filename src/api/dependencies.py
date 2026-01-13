"""Shared dependencies for FastAPI routes."""
from __future__ import annotations

from functools import lru_cache
from typing import Generator

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from ingestion_service.db import SessionLocal, init_db
from sentiment_service.config import get_settings as get_sentiment_settings
from sentiment_service.model import SentimentModel


def init_application_state() -> None:
    """Ensure database tables exist before the API starts."""
    init_db()


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_role(x_role: str = Header("analyst", alias="X-Role")) -> str:
    return x_role.lower()


def require_admin(role: str = Header("analyst", alias="X-Role")) -> str:
    role_value = role.lower()
    if role_value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return role_value


@lru_cache
def get_sentiment_model() -> SentimentModel:
    settings = get_sentiment_settings()
    return SentimentModel(
        model_name=settings.model_name,
        revision=settings.model_revision,
        device=settings.device,
        label_mapping=settings.label_mapping,
    )
