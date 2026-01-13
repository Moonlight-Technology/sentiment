"""Pydantic models aligned with docs/schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Entity(BaseModel):
    type: str
    value: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class TextItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_type: str
    source_id: str
    source_metadata: Dict[str, object] | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    language: str = Field(min_length=2, max_length=5)
    title: Optional[str] = None
    body: str
    entities: List[Entity] | None = None
    labels: List[str] | None = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError("language must be alphabetic ISO code")
        return value.lower()


class SentimentScores(BaseModel):
    label: str
    score: float = Field(ge=0.0, le=1.0)
    scores_by_label: Dict[str, float] | None = None


class SentimentResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    text_item_id: UUID
    model_name: str
    model_version: str
    pipeline_stage: str = "batch"
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    label: str
    score: float = Field(ge=0.0, le=1.0)
    scores_by_label: Dict[str, float] | None = None
    explanations: Optional[List[Dict[str, object]]] = None
    annotations: Optional[Dict[str, object]] = None


class ArticleSummary(BaseModel):
    """Lightweight representation of a feed entry."""

    id: str
    title: str
    link: HttpUrl
    summary: str
    published: Optional[datetime]
