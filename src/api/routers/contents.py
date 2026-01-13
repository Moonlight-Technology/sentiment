"""Content and sentiment result endpoints."""
from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ingestion_service.orm import SentimentResultORM, TextItemORM

from .. import schemas
from ..dependencies import get_db


router = APIRouter(prefix="", tags=["Contents"])


@router.get("/contents/brand", response_model=schemas.BrandSentimentResponse)
def brand_sentiment(
    label: str,
    limit: int = 20,
    session: Session = Depends(get_db),
) -> schemas.BrandSentimentResponse:
    stmt = select(TextItemORM).order_by(TextItemORM.ingested_at.desc()).limit(limit * 5)
    candidates = session.scalars(stmt).all()
    items = [item for item in candidates if item.labels and label in item.labels][:limit]
    sentiments = _latest_sentiments(session, [item.id for item in items])
    summary = {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
    }
    for result in sentiments.values():
        summary[result.label] = summary.get(result.label, 0) + 1
    return schemas.BrandSentimentResponse(
        label=label,
        positive=summary.get("positive", 0),
        neutral=summary.get("neutral", 0),
        negative=summary.get("negative", 0),
        total=sum(summary.values()),
        top_items=[_to_content_response(item, sentiments.get(item.id)) for item in items],
    )


@router.get("/contents", response_model=list[schemas.ContentResponse])
def list_contents(
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    keyword: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_db),
) -> list[schemas.ContentResponse]:
    items = _query_contents(session, source, date_from, date_to, limit, keyword)
    sentiments = _latest_sentiments(session, [item.id for item in items])
    responses = [_to_content_response(item, sentiments.get(item.id)) for item in items]
    if sentiment:
        responses = [c for c in responses if c.sentiment and c.sentiment.label == sentiment]
    return responses


@router.get("/contents/{content_id}", response_model=schemas.ContentResponse)
def get_content(content_id: UUID, session: Session = Depends(get_db)) -> schemas.ContentResponse:
    item = session.get(TextItemORM, str(content_id))
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    sentiments = _latest_sentiments(session, [item.id])
    return _to_content_response(item, sentiments.get(item.id))


@router.get("/contents/export", response_class=StreamingResponse)
def export_contents(session: Session = Depends(get_db)) -> StreamingResponse:
    items = _query_contents(session, None, None, None, 200)
    sentiments = _latest_sentiments(session, [item.id for item in items])
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "title", "source", "sentiment", "score", "published_at"])
    for item in items:
        sentiment = sentiments.get(item.id)
        writer.writerow(
            [
                item.id,
                item.title or "",
                item.source_type,
                sentiment.label if sentiment else "",
                sentiment.score if sentiment else "",
                item.published_at.isoformat() if item.published_at else "",
            ]
        )
    buffer.seek(0)
    filename = f"contents-export-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers=headers)


@router.get("/contents/search", response_model=list[schemas.ContentResponse])
def search_contents(
    keyword: str,
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_db),
) -> list[schemas.ContentResponse]:
    stmt = select(TextItemORM)
    like = f"%{keyword}%"
    stmt = stmt.where(or_(TextItemORM.title.ilike(like), TextItemORM.body.ilike(like)))
    stmt = stmt.order_by(TextItemORM.ingested_at.desc()).limit(limit)
    items = session.scalars(stmt).all()
    sentiments = _latest_sentiments(session, [item.id for item in items])
    return [_to_content_response(item, sentiments.get(item.id)) for item in items]


@router.get("/contents/filter", response_model=list[schemas.ContentResponse])
def filter_contents(
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    date: Optional[datetime] = None,
    session: Session = Depends(get_db),
) -> list[schemas.ContentResponse]:
    date_from = date
    date_to = date
    results = list_contents(source=source, sentiment=sentiment, date_from=date_from, date_to=date_to, session=session)  # type: ignore[arg-type]
    return results


@router.patch("/contents/{content_id}/label", response_model=schemas.ContentResponse)
def update_label(
    content_id: UUID,
    payload: schemas.LabelUpdateRequest,
    session: Session = Depends(get_db),
) -> schemas.ContentResponse:
    item = session.get(TextItemORM, str(content_id))
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    labels = item.labels or []
    if payload.label not in labels:
        labels.append(payload.label)
    item.labels = labels
    session.add(item)
    session.commit()
    session.refresh(item)
    sentiments = _latest_sentiments(session, [item.id])
    return _to_content_response(item, sentiments.get(item.id))




@router.get("/contents/{content_id}/history", response_model=list[schemas.SentimentHistory])
def sentiment_history(content_id: UUID, session: Session = Depends(get_db)) -> list[schemas.SentimentHistory]:
    stmt = (
        select(SentimentResultORM)
        .where(SentimentResultORM.text_item_id == str(content_id))
        .order_by(SentimentResultORM.scored_at.desc())
    )
    return [
        schemas.SentimentHistory(
            label=result.label,
            score=result.score,
            scored_at=result.scored_at,
            model_name=result.model_name,
            model_version=result.model_version,
        )
        for result in session.scalars(stmt).all()
    ]


def _query_contents(
    session: Session,
    source: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    limit: int,
    keyword: Optional[str] = None,
) -> List[TextItemORM]:
    stmt = select(TextItemORM)
    if source:
        stmt = stmt.where(TextItemORM.source_type == source)
    if date_from:
        stmt = stmt.where(TextItemORM.ingested_at >= date_from)
    if date_to:
        stmt = stmt.where(TextItemORM.ingested_at <= date_to)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(TextItemORM.title.ilike(like), TextItemORM.body.ilike(like)))
    stmt = stmt.order_by(TextItemORM.ingested_at.desc()).limit(limit)
    return session.scalars(stmt).all()


def _latest_sentiments(session: Session, item_ids: List[str]) -> dict[str, SentimentResultORM]:
    if not item_ids:
        return {}
    stmt = (
        select(SentimentResultORM)
        .where(SentimentResultORM.text_item_id.in_(item_ids))
        .order_by(SentimentResultORM.text_item_id, SentimentResultORM.scored_at.desc())
    )
    results: dict[str, SentimentResultORM] = {}
    for result in session.scalars(stmt).all():
        if result.text_item_id not in results:
            results[result.text_item_id] = result
    return results


def _to_content_response(item: TextItemORM, sentiment: Optional[SentimentResultORM]) -> schemas.ContentResponse:
    summary = None
    if sentiment:
        summary = schemas.SentimentSummary(
            label=sentiment.label,
            score=sentiment.score,
            scores_by_label=sentiment.scores_by_label,
            scored_at=sentiment.scored_at,
        )
    return schemas.ContentResponse(
        id=item.id,
        source_type=item.source_type,
        source_id=item.source_id,
        title=item.title,
        body=item.body,
        language=item.language,
        published_at=item.published_at,
        ingested_at=item.ingested_at,
        labels=item.labels,
        sentiment=summary,
    )
