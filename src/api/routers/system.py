"""System and maintenance endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from ingestion_service.orm import SentimentResultORM, TextItemORM
from sentiment_service.config import get_settings as get_sentiment_settings

from .. import schemas
from ..dependencies import get_db
from ..store import fake_db


router = APIRouter(prefix="/system", tags=["System"])


@router.get("/status", response_model=schemas.SystemStatusResponse)
def system_status(session: Session = Depends(get_db)) -> schemas.SystemStatusResponse:
    ingested = session.scalar(select(func.count(TextItemORM.id))) or 0
    pending_stmt = (
        select(func.count())
        .select_from(TextItemORM)
        .where(~exists().where(SentimentResultORM.text_item_id == TextItemORM.id))
    )
    pending = session.scalar(pending_stmt) or 0
    return schemas.SystemStatusResponse(
        status="ok",
        ingested_items=ingested,
        pending_sentiments=pending,
        timestamp=datetime.utcnow(),
    )


@router.get("/logs", response_model=schemas.SystemLogsResponse)
def system_logs() -> schemas.SystemLogsResponse:
    return schemas.SystemLogsResponse(logs=fake_db.audit_logs[-50:])


@router.post("/backup", response_model=schemas.BackupResponse)
def run_backup() -> schemas.BackupResponse:
    fake_db._log("backup", "Manual backup triggered")
    return schemas.BackupResponse(status="started", started_at=datetime.utcnow())


@router.get("/version", response_model=schemas.VersionResponse)
def version_info() -> schemas.VersionResponse:
    settings = get_sentiment_settings()
    return schemas.VersionResponse(
        api_version="v1",
        model_version=settings.model_version or settings.model_revision or "latest",
        git_sha="dev",
    )
