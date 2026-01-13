"""Compute and persist keyword sentiment stats."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Dict, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ingestion_service.orm import KeywordSentimentORM, SentimentResultORM, TextItemORM


def _latest_sentiments(session: Session, item_ids: Iterable[str]) -> Dict[str, SentimentResultORM]:
    if not item_ids:
        return {}
    stmt = (
        select(SentimentResultORM)
        .where(SentimentResultORM.text_item_id.in_(list(item_ids)))
        .order_by(SentimentResultORM.text_item_id, SentimentResultORM.scored_at.desc())
    )
    cache: Dict[str, SentimentResultORM] = {}
    for result in session.scalars(stmt).all():
        if result.text_item_id not in cache:
            cache[result.text_item_id] = result
    return cache


def refresh_keyword_stat(keyword: str, session: Session, limit: int = 500) -> KeywordSentimentORM:
    like = f"%{keyword}%"
    stmt = (
        select(TextItemORM.id)
        .where((TextItemORM.title.ilike(like)) | (TextItemORM.body.ilike(like)))
        .order_by(TextItemORM.ingested_at.desc())
        .limit(limit)
    )
    item_ids = [row[0] for row in session.execute(stmt).all()]
    sentiments = _latest_sentiments(session, item_ids)
    counter = Counter(result.label for result in sentiments.values())
    total = sum(counter.values())

    record = session.get(KeywordSentimentORM, keyword)
    now = datetime.utcnow()
    if record:
        record.positive_count = counter.get("positive", 0)
        record.neutral_count = counter.get("neutral", 0)
        record.negative_count = counter.get("negative", 0)
        record.total_count = total
        record.updated_at = now
    else:
        record = KeywordSentimentORM(
            keyword=keyword,
            positive_count=counter.get("positive", 0),
            neutral_count=counter.get("neutral", 0),
            negative_count=counter.get("negative", 0),
            total_count=total,
            updated_at=now,
        )
        session.add(record)
    session.commit()
    session.refresh(record)
    return record


def refresh_keyword_stats(keywords: Iterable[str], session: Session) -> list[KeywordSentimentORM]:
    return [refresh_keyword_stat(keyword, session) for keyword in keywords]
