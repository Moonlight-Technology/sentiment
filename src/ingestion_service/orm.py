"""SQLAlchemy ORM models mirroring the data contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .models import SentimentResult, TextItem


class Base(DeclarativeBase):
    pass


class TextItemORM(Base):
    __tablename__ = "text_items"
    __table_args__ = (UniqueConstraint("source_id", name="uq_text_items_source_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[str] = mapped_column(String(512), nullable=False)
    source_metadata: Mapped[Optional[Dict[str, object]]] = mapped_column(JSON, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    entities: Mapped[Optional[List[Dict[str, object]]]] = mapped_column(JSON, nullable=True)
    labels: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    sentiments: Mapped[List["SentimentResultORM"]] = relationship(back_populates="text_item", cascade="all, delete-orphan")

    def to_model(self) -> TextItem:
        return TextItem(
            id=UUID(self.id),
            source_type=self.source_type,
            source_id=self.source_id,
            source_metadata=self.source_metadata,
            ingested_at=self.ingested_at,
            published_at=self.published_at,
            language=self.language,
            title=self.title,
            body=self.body,
            entities=self.entities,
            labels=self.labels,
        )

    @classmethod
    def from_model(cls, model: TextItem) -> "TextItemORM":
        return cls(
            id=str(model.id),
            source_type=model.source_type,
            source_id=model.source_id,
            source_metadata=model.source_metadata,
            ingested_at=model.ingested_at,
            published_at=model.published_at,
            language=model.language,
            title=model.title,
            body=model.body,
            entities=model.entities,
            labels=model.labels,
        )


class SentimentResultORM(Base):
    __tablename__ = "sentiment_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    text_item_id: Mapped[str] = mapped_column(ForeignKey("text_items.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(128))
    model_version: Mapped[str] = mapped_column(String(64))
    pipeline_stage: Mapped[str] = mapped_column(String(32))
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    label: Mapped[str] = mapped_column(String(32))
    score: Mapped[float] = mapped_column(Float, nullable=False)
    scores_by_label: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)
    explanations: Mapped[Optional[List[Dict[str, object]]]] = mapped_column(JSON, nullable=True)
    annotations: Mapped[Optional[Dict[str, object]]] = mapped_column(JSON, nullable=True)

    text_item: Mapped[TextItemORM] = relationship(back_populates="sentiments")

    def to_model(self) -> SentimentResult:
        return SentimentResult(
            id=UUID(self.id),
            text_item_id=UUID(self.text_item_id),
            model_name=self.model_name,
            model_version=self.model_version,
            pipeline_stage=self.pipeline_stage,
            scored_at=self.scored_at,
            label=self.label,
            score=self.score,
            scores_by_label=self.scores_by_label,
            explanations=self.explanations,
            annotations=self.annotations,
        )

    @classmethod
    def from_model(cls, model: SentimentResult) -> "SentimentResultORM":
        return cls(
            id=str(model.id),
            text_item_id=str(model.text_item_id),
            model_name=model.model_name,
            model_version=model.model_version,
            pipeline_stage=model.pipeline_stage,
            scored_at=model.scored_at,
            label=model.label,
            score=model.score,
            scores_by_label=model.scores_by_label,
            explanations=model.explanations,
            annotations=model.annotations,
        )


class SourceORM(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    config: Mapped[Optional[Dict[str, object]]] = mapped_column(JSON, nullable=True)
    schedule: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="inactive")
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class KeywordSentimentORM(Base):
    __tablename__ = "keyword_sentiments"

    keyword: Mapped[str] = mapped_column(String(128), primary_key=True)
    positive_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
