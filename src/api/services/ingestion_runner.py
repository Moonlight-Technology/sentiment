"""Helpers to execute ingestion runs per source."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ingestion_service.config import Settings, get_settings
from ingestion_service.ingestor import IngestionService
from ingestion_service.db import init_db
from ingestion_service.orm import SourceORM


def ingest_source(source: SourceORM) -> int:
    base_settings = get_settings()
    update_payload = {
        "feed_url": source.config.get("url", str(base_settings.feed_url)) if source.config else str(base_settings.feed_url),
        "source_type": source.type or base_settings.source_type,
        "language": (source.config.get("language") if source.config else None) or base_settings.language,
    }
    if (source.type or base_settings.source_type) in {"csv", "csv_file"}:
        csv_path = source.config.get("path") if source.config else None
        if not csv_path:
            raise ValueError("source config missing path for csv source")
        update_payload["csv_path"] = Path(csv_path)
    settings = base_settings.model_copy(update=update_payload)
    init_db()
    service = IngestionService(settings=settings)
    new_items = service.run()
    return len(new_items)


def ingest_sources(sources: Iterable[SourceORM]) -> list[tuple[str, int, str | None]]:
    results: list[tuple[str, int, str | None]] = []
    for source in sources:
        if not source.config:
            results.append((source.id, 0, "source config missing"))
            continue
        if (source.type or "rss") in {"csv", "csv_file"} and "path" not in source.config:
            results.append((source.id, 0, "source config missing path"))
            continue
        if (source.type or "rss") not in {"csv", "csv_file"} and "url" not in source.config:
            results.append((source.id, 0, "source config missing url"))
            continue
        try:
            count = ingest_source(source)
            results.append((source.id, count, None))
        except Exception as exc:  # noqa: BLE001
            results.append((source.id, 0, str(exc)))
    return results
