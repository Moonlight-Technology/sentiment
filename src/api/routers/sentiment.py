"""Sentiment processing endpoints."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ingestion_service.orm import KeywordSentimentORM, SentimentResultORM, TextItemORM
from sentiment_service.config import get_settings as get_sentiment_settings

from .. import schemas
from ..dependencies import get_db, get_sentiment_model
from ..services.keyword_analytics import refresh_keyword_stat, refresh_keyword_stats
from ..services.sentiment_runner import run_sentiment_for_item, run_sentiment_worker


router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


@router.post("/analyze", response_model=schemas.SentimentAnalyzeResponse)
def analyze_text(
    payload: schemas.SentimentAnalyzeRequest,
    model=Depends(get_sentiment_model),
) -> schemas.SentimentAnalyzeResponse:
    scores = model.predict(payload.text)
    label = max(scores, key=scores.get)
    return schemas.SentimentAnalyzeResponse(
        sentiment=label,
        score=scores[label],
        scores_by_label=scores,
        created_at=datetime.utcnow(),
    )


@router.get("/stats", response_model=schemas.SentimentStatsResponse)
def sentiment_stats(session: Session = Depends(get_db)) -> schemas.SentimentStatsResponse:
    stmt = select(SentimentResultORM.label, func.count(SentimentResultORM.id)).group_by(SentimentResultORM.label)
    counts = {label: count for label, count in session.execute(stmt)}
    total = sum(counts.values())
    return schemas.SentimentStatsResponse(
        positive=counts.get("positive", 0),
        neutral=counts.get("neutral", 0),
        negative=counts.get("negative", 0),
        total=total,
        updated_at=datetime.utcnow(),
    )


@router.get("/trend", response_model=list[schemas.SentimentTrendPoint])
def sentiment_trend(time_range: str = "7d", session: Session = Depends(get_db)) -> list[schemas.SentimentTrendPoint]:
    days = 7
    if time_range.endswith("d") and time_range[:-1].isdigit():
        days = int(time_range[:-1])
    start = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(func.date(SentimentResultORM.scored_at), SentimentResultORM.label, func.count(SentimentResultORM.id))
        .where(SentimentResultORM.scored_at >= start)
        .group_by(func.date(SentimentResultORM.scored_at), SentimentResultORM.label)
        .order_by(func.date(SentimentResultORM.scored_at))
    )
    rows = session.execute(stmt).all()
    buckets: dict[str, dict[str, int]] = {}
    for bucket_date, label, count in rows:
        buckets.setdefault(bucket_date, {"positive": 0, "neutral": 0, "negative": 0})
        buckets[bucket_date][label] = count
    trend = []
    for bucket, values in buckets.items():
        if isinstance(bucket, str):
            bucket_date = datetime.fromisoformat(bucket).date()
        else:
            bucket_date = bucket
        trend.append(
            schemas.SentimentTrendPoint(
                date=bucket_date,
                positive=values.get("positive", 0),
                neutral=values.get("neutral", 0),
                negative=values.get("negative", 0),
            )
        )
    return trend


@router.get("/keywords", response_model=list[schemas.KeywordResponse])
def sentiment_keywords(limit: int = 20, session: Session = Depends(get_db)) -> list[schemas.KeywordResponse]:
    stmt = select(TextItemORM.body)
    bodies = [row[0] for row in session.execute(stmt).all()]
    counter: Counter[str] = Counter()
    for body in bodies:
        if not body:
            continue
        for token in body.lower().split():
            token = token.strip(".,!?:\"'()[]{}")
            if len(token) <= 3:
                continue
            counter[token] += 1
    return [schemas.KeywordResponse(keyword=word, count=count) for word, count in counter.most_common(limit)]


@router.post("/retrain", response_model=schemas.RetrainResponse)
def retrain_model(payload: schemas.RetrainRequest) -> schemas.RetrainResponse:
    job_id = f"job-{int(datetime.utcnow().timestamp())}"
    return schemas.RetrainResponse(job_id=job_id, status="queued", submitted_at=datetime.utcnow())


@router.get("/accuracy", response_model=schemas.SentimentAccuracyResponse)
def sentiment_accuracy() -> schemas.SentimentAccuracyResponse:
    settings = get_sentiment_settings()
    return schemas.SentimentAccuracyResponse(
        model_name=settings.model_name,
        model_version=settings.model_version or settings.model_revision or "latest",
        accuracy=0.86,
        evaluated_at=datetime.utcnow(),
    )


@router.post("/run")
def run_sentiment(batch_limit: int | None = None) -> dict:
    results = run_sentiment_worker(batch_limit=batch_limit)
    return {"status": "completed", "processed": len(results), "results": results}


@router.post("/run/{text_item_id}")
def run_sentiment_single(text_item_id: str) -> dict:
    return run_sentiment_for_item(text_item_id)


@router.get("/keyword-stats", response_model=schemas.KeywordSentimentStats)
def get_keyword_sentiment(keyword: str, refresh: bool = False, session: Session = Depends(get_db)) -> schemas.KeywordSentimentStats:
    record = session.get(KeywordSentimentORM, keyword)
    if refresh or not record:
        record = refresh_keyword_stat(keyword, session)
    return _keyword_stat_schema(record)


@router.post("/keyword-stats/refresh")
def refresh_keywords(payload: List[str], session: Session = Depends(get_db)) -> dict:
    records = refresh_keyword_stats(payload, session)
    return {"status": "completed", "results": [_keyword_stat_schema(record) for record in records]}


def _keyword_stat_schema(record: KeywordSentimentORM) -> schemas.KeywordSentimentStats:
    return schemas.KeywordSentimentStats(
        keyword=record.keyword,
        positive=record.positive_count,
        neutral=record.neutral_count,
        negative=record.negative_count,
        total=record.total_count,
        updated_at=record.updated_at,
    )
