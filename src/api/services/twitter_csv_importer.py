"""Import TextItems from Twitter CSV dataset uploads."""
from __future__ import annotations

import csv
import io
from email.utils import parsedate_to_datetime
from typing import Dict

from ingestion_service.models import TextItem
from ingestion_service.sql_repository import DatabaseRepository
from ingestion_service.db import SessionLocal


def import_twitter_csv(content: bytes, limit: int | None = None) -> Dict[str, int]:
    text = content.decode("latin-1")
    reader = csv.reader(io.StringIO(text))
    repository = DatabaseRepository(SessionLocal)
    inserted = 0
    skipped = 0
    for index, row in enumerate(reader):
        if limit is not None and inserted >= limit:
            break
        if len(row) < 6:
            skipped += 1
            continue
        sentiment_code, tweet_id, published_at, query, username, body = row[:6]
        if not body:
            skipped += 1
            continue
        text_item = TextItem(
            source_type="twitter_csv",
            source_id=tweet_id,
            source_metadata={
                "username": username,
                "query": query,
                "tweet_index": index,
            },
            published_at=_parse_datetime(published_at),
            language="en",
            title=body[:120],
            body=body,
            labels=[_label_from_code(sentiment_code)] if sentiment_code else None,
        )
        stored = repository.save_if_new(text_item)
        if stored:
            inserted += 1
        else:
            skipped += 1
    return {"inserted": inserted, "skipped": skipped}


def _parse_datetime(value: str | None):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (ValueError, TypeError):
        return None


def _label_from_code(code: str) -> str:
    mapping = {
        "0": "negative",
        "2": "neutral",
        "4": "positive",
    }
    return mapping.get(code, "unknown")
