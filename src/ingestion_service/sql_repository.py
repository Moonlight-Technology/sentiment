"""SQLAlchemy-backed repository."""
from __future__ import annotations

from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .models import TextItem
from .orm import TextItemORM


SessionFactory = Callable[[], Session]


class DatabaseRepository:
    def __init__(self, session_factory: sessionmaker | SessionFactory):
        self._session_factory = session_factory

    def save_if_new(self, item: TextItem) -> Optional[TextItem]:
        """Persist a TextItem if its source_id is new. Returns the stored item or None if skipped."""
        with self._session_factory() as session:
            exists = session.scalar(select(TextItemORM.id).where(TextItemORM.source_id == item.source_id))
            if exists:
                return None
            orm_item = TextItemORM.from_model(item)
            session.add(orm_item)
            session.commit()
            session.refresh(orm_item)
            return orm_item.to_model()
