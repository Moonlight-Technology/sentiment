"""High-level ingestion workflow."""
from __future__ import annotations

import logging
from typing import Iterable, List

from .config import Settings, get_settings
from .db import SessionLocal, init_db
from .models import ArticleSummary, TextItem
from .news_client import NewsFeedClient
from .csv_client import CsvSourceClient
from .sql_repository import DatabaseRepository

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = _build_client(self.settings)
        self.repository = DatabaseRepository(SessionLocal)

    def run(self) -> List[TextItem]:
        logger.info("Fetching articles from %s", self.settings.feed_url)
        articles = self.client.fetch()
        new_items: List[TextItem] = []
        for article in _dedupe(articles):
            source_id = str(article.link)
            item = self._to_text_item(article)
            stored = self.repository.save_if_new(item)
            if stored:
                new_items.append(stored)
                logger.info("Stored article %s", source_id)
            else:
                logger.debug("Skipping duplicate article %s", source_id)
        logger.info("Ingestion complete. Stored %s new items", len(new_items))
        return new_items

    def _to_text_item(self, article: ArticleSummary) -> TextItem:
        metadata = {
            "feed_url": str(self.settings.feed_url),
        }
        published = article.published
        return TextItem(
            source_type=self.settings.source_type,
            source_id=str(article.link),
            source_metadata=metadata,
            published_at=published,
            language=self.settings.language,
            title=article.title,
            body=article.summary,
        )


def _dedupe(articles: Iterable[ArticleSummary]) -> List[ArticleSummary]:
    seen: set[str] = set()
    unique: List[ArticleSummary] = []
    for article in articles:
        marker = article.id or str(article.link)
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(article)
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    service = IngestionService()
    service.run()


def _build_client(settings: Settings) -> NewsFeedClient | CsvSourceClient:
    if settings.source_type in {"csv", "csv_file"}:
        if not settings.csv_path:
            raise ValueError("csv_path is required for csv sources")
        return CsvSourceClient(settings.csv_path)
    return NewsFeedClient(str(settings.feed_url))
