"""Persistence helpers for ingestion outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Set

from .models import TextItem


class JsonlRepository:
    """Stores TextItem payloads inside a JSON Lines file."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list_items(self) -> Iterable[TextItem]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                yield TextItem.model_validate(payload)

    def existing_source_ids(self) -> Set[str]:
        return {item.source_id for item in self.list_items()}

    def append(self, item: TextItem) -> None:
        serialized = json.dumps(item.model_dump(mode="json"))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(serialized + "\n")
