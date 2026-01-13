"""Data source management endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ingestion_service.orm import SourceORM

from .. import schemas
from ..dependencies import get_db
from ..services.ingestion_runner import ingest_sources
from ..services.twitter_csv_importer import import_twitter_csv


router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=list[schemas.SourceResponse])
def list_sources(session: Session = Depends(get_db)) -> list[schemas.SourceResponse]:
    sources = session.scalars(select(SourceORM).order_by(SourceORM.created_at.desc())).all()
    return [_to_schema(source) for source in sources]


@router.post("", response_model=schemas.SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(payload: schemas.SourceBase, session: Session = Depends(get_db)) -> schemas.SourceResponse:
    source = SourceORM(
        id=str(uuid4()),
        name=payload.name,
        type=payload.type,
        config=payload.config,
        status=payload.status,
        schedule=payload.schedule,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return _to_schema(source)


@router.put("/{source_id}", response_model=schemas.SourceResponse)
def update_source(source_id: str, payload: schemas.SourceBase, session: Session = Depends(get_db)) -> schemas.SourceResponse:
    source = session.get(SourceORM, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    source.name = payload.name
    source.type = payload.type
    source.config = payload.config
    source.status = payload.status
    source.schedule = payload.schedule
    source.updated_at = datetime.utcnow()
    session.add(source)
    session.commit()
    session.refresh(source)
    return _to_schema(source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: str, session: Session = Depends(get_db)) -> None:
    source = session.get(SourceORM, source_id)
    if source:
        session.delete(source)
        session.commit()


@router.get("/status", response_model=schemas.SourceStatusResponse)
def source_status(session: Session = Depends(get_db)) -> schemas.SourceStatusResponse:
    sources = list_sources(session)
    return schemas.SourceStatusResponse(sources=sources, last_updated=datetime.utcnow())


@router.post("/reload")
def reload_sources(session: Session = Depends(get_db)) -> dict:
    sources = session.scalars(select(SourceORM)).all()
    if not sources:
        return {"status": "no_sources", "count": 0}

    now = datetime.utcnow()
    for source in sources:
        source.status = "running"
        source.updated_at = now
        session.add(source)
    session.commit()

    results = ingest_sources(sources)
    for source_id, count, error in results:
        source = session.get(SourceORM, source_id)
        if not source:
            continue
        source.last_run = datetime.utcnow()
        source.updated_at = datetime.utcnow()
        if error:
            source.status = "error"
            source.last_error = error
        else:
            source.status = "active"
            source.last_error = None
        session.add(source)
    session.commit()
    return {
        "status": "completed",
        "count": len(results),
        "results": [
            {"source_id": source_id, "inserted": count, "error": error}
            for source_id, count, error in results
        ],
    }


@router.post("/import/twitter-csv")
async def upload_twitter_csv(file: UploadFile, limit: int | None = None) -> dict:
    content = await file.read()
    stats = import_twitter_csv(content, limit)
    return {"status": "completed", **stats}


def _to_schema(source: SourceORM) -> schemas.SourceResponse:
    return schemas.SourceResponse(
        id=source.id,
        name=source.name,
        type=source.type,
        config=source.config or {},
        status=source.status,
        schedule=source.schedule,
        last_run=source.last_run,
        last_error=source.last_error,
    )
