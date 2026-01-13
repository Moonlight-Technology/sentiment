"""Batch worker that scores TextItems with an IndoBERT model."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from ingestion_service.models import SentimentResult

from .config import Settings, get_settings
from .db import SessionLocal, init_db
from .model import SentimentModel
from .repository import SentimentRepository

logger = logging.getLogger(__name__)


class SentimentWorker:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.repository = SentimentRepository(SessionLocal)
        self.model = SentimentModel(
            model_name=self.settings.model_name,
            revision=self.settings.model_revision,
            device=self.settings.device,
            label_mapping=self.settings.label_mapping,
        )
        self.model_version = (
            self.settings.model_version
            or self.settings.model_revision
            or "latest"
        )

    def run(self) -> List[SentimentResult]:
        pending_items = self.repository.fetch_pending_items(
            model_name=self.settings.model_name,
            model_version=self.model_version,
            limit=self.settings.batch_limit,
        )
        if not pending_items:
            logger.info("No pending text items for model %s:%s", self.settings.model_name, self.model_version)
            return []
        logger.info("Scoring %s text items using %s:%s", len(pending_items), self.settings.model_name, self.model_version)
        stored_results: List[SentimentResult] = []
        for item in pending_items:
            try:
                scores = self.model.predict(item.body)
            except ValueError as exc:
                logger.warning("Skipping item %s: %s", item.id, exc)
                continue
            if not scores:
                logger.warning("No scores returned for item %s", item.id)
                continue
            label, score = _top_label(scores)
            result = SentimentResult(
                text_item_id=item.id,
                model_name=self.settings.model_name,
                model_version=self.model_version,
                pipeline_stage=self.settings.pipeline_stage,
                scored_at=datetime.utcnow(),
                label=label,
                score=score,
                scores_by_label=scores,
            )
            stored = self.repository.save_result(result)
            stored_results.append(stored)
            logger.debug("Stored sentiment for text_item_id=%s label=%s", item.id, label)
        logger.info("Sentiment scoring complete. Stored %s results", len(stored_results))
        return stored_results


def _top_label(scores_by_label: dict[str, float]) -> tuple[str, float]:
    label = max(scores_by_label, key=scores_by_label.get)
    return label, scores_by_label[label]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    worker = SentimentWorker()
    worker.run()
