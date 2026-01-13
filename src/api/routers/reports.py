"""Analytics and reporting endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ingestion_service.orm import SentimentResultORM, TextItemORM

from .. import schemas
from ..dependencies import get_db
from ..store import fake_db


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/overview")
def report_overview(session: Session = Depends(get_db)) -> dict:
    sentiment_stmt = select(SentimentResultORM.label, func.count()).group_by(SentimentResultORM.label)
    sentiment_counts = {label: count for label, count in session.execute(sentiment_stmt)}
    source_stmt = select(TextItemORM.source_type, func.count()).group_by(TextItemORM.source_type)
    source_counts = {source: count for source, count in session.execute(source_stmt)}
    return {
        "sentiments": sentiment_counts,
        "sources": source_counts,
        "generated_at": datetime.utcnow(),
    }


@router.get("/trend")
def report_trend(session: Session = Depends(get_db)) -> list[dict]:
    stmt = (
        select(func.date(TextItemORM.ingested_at), TextItemORM.source_type, func.count())
        .group_by(func.date(TextItemORM.ingested_at), TextItemORM.source_type)
        .order_by(func.date(TextItemORM.ingested_at))
    )
    return [
        {"date": bucket, "source": source, "count": count}
        for bucket, source, count in session.execute(stmt).all()
    ]


@router.get("/category")
def report_category(session: Session = Depends(get_db)) -> list[dict]:
    stmt = select(TextItemORM.labels)
    counter: dict[str, int] = {}
    for (labels,) in session.execute(stmt).all():
        if not labels:
            continue
        for label in labels:
            counter[label] = counter.get(label, 0) + 1
    return [{"label": label, "count": count} for label, count in counter.items()]


@router.post("/generate", response_model=schemas.ReportResponse)
def generate_report(payload: schemas.ReportGenerateRequest) -> schemas.ReportResponse:
    job = fake_db.log_report_job({"type": payload.type, "date_range": payload.date_range})
    job["download_url"] = f"/reports/download/{job['id']}"
    return schemas.ReportResponse(
        id=job["id"],
        status=job["status"],
        generated_at=job["generated_at"],
        download_url=job.get("download_url"),
    )


@router.get("/download/{report_id}", response_model=schemas.ReportResponse)
def download_report(report_id: str) -> schemas.ReportResponse:
    report = fake_db.reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report["download_url"] = f"https://example.com/reports/{report_id}.pdf"
    return schemas.ReportResponse(
        id=report["id"],
        status=report["status"],
        generated_at=report["generated_at"],
        download_url=report.get("download_url"),
    )
