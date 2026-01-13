"""Helpers to read pending text items and persist sentiment results."""
from __future__ import annotations

from typing import List

from sqlalchemy import exists, select
from sqlalchemy.orm import sessionmaker

from ingestion_service.models import SentimentResult, TextItem
from ingestion_service.orm import SentimentResultORM, TextItemORM


class SentimentRepository:
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory

    def fetch_pending_items(
        self,
        model_name: str,
        model_version: str,
        limit: int,
    ) -> List[TextItem]:
        with self._session_factory() as session:
            stmt = (
                select(TextItemORM)
                .where(
                    ~exists()
                    .where(SentimentResultORM.text_item_id == TextItemORM.id)
                    .where(SentimentResultORM.model_name == model_name)
                    .where(SentimentResultORM.model_version == model_version)
                )
                .order_by(TextItemORM.ingested_at.asc())
                .limit(limit)
            )
            return [orm_item.to_model() for orm_item in session.scalars(stmt).all()]

    def save_result(self, result: SentimentResult) -> SentimentResult:
        with self._session_factory() as session:
            orm_result = SentimentResultORM.from_model(result)
            session.add(orm_result)
            session.commit()
            session.refresh(orm_result)
            return orm_result.to_model()
