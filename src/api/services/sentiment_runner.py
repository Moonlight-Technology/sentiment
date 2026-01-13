"""Trigger the sentiment worker synchronously."""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select

from ingestion_service.models import SentimentResult
from ingestion_service.orm import SentimentResultORM, TextItemORM
from sentiment_service.db import SessionLocal
from sentiment_service.worker import SentimentWorker
from sentiment_service.worker import _top_label


def run_sentiment_worker(batch_limit: int | None = None) -> List[dict]:
    worker = SentimentWorker()
    if batch_limit is not None:
        worker.settings.batch_limit = batch_limit
    results = worker.run()
    return [
        {
            "text_item_id": str(result.text_item_id),
            "label": result.label,
            "score": result.score,
            "model_version": result.model_version,
        }
        for result in results
    ]


def run_sentiment_for_item(text_item_id: str) -> dict:
    worker = SentimentWorker()
    with SessionLocal() as session:
        orm_item = session.get(TextItemORM, text_item_id)
        if not orm_item:
            raise ValueError("Text item not found")
        existing = session.scalar(
            select(SentimentResultORM.id)
            .where(SentimentResultORM.text_item_id == text_item_id)
            .where(SentimentResultORM.model_name == worker.settings.model_name)
            .where(SentimentResultORM.model_version == worker.model_version)
        )
        if existing:
            return {"status": "skipped", "reason": "already_processed"}
        text_item = orm_item.to_model()
    scores = worker.model.predict(text_item.body)
    if not scores:
        raise ValueError("No scores returned")
    label, score = _top_label(scores)
    result = SentimentResult(
        text_item_id=text_item.id,
        model_name=worker.settings.model_name,
        model_version=worker.model_version,
        pipeline_stage=worker.settings.pipeline_stage,
        scored_at=datetime.utcnow(),
        label=label,
        score=score,
        scores_by_label=scores,
    )
    stored = worker.repository.save_result(result)
    return {
        "status": "completed",
        "text_item_id": str(stored.text_item_id),
        "label": stored.label,
        "score": stored.score,
    }
