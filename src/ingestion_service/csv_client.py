"""Client to read text items from CSV files."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4

from .models import ArticleSummary


class CsvSourceClient:
    def __init__(self, path: Path, encoding: str = "utf-8") -> None:
        self.path = Path(path)
        self.encoding = encoding

    def fetch(self) -> List[ArticleSummary]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding=self.encoding, newline="") as handle:
            reader = csv.DictReader(handle)
            articles: List[ArticleSummary] = []
            for row in reader:
                body = row.get("body") or row.get("text") or row.get("summary")
                if not body:
                    continue
                link = row.get("link") or row.get("url") or row.get("source_id")
                if not link or not link.startswith("http"):
                    link = f"https://csv.local/{uuid4()}"
                article = ArticleSummary(
                    id=row.get("id") or row.get("source_id") or str(uuid4()),
                    title=row.get("title") or "Untitled",
                    link=link,
                    summary=body,
                    published=_parse_published(row.get("published_at") or row.get("published")),
                )
                articles.append(article)
        return articles


def _parse_published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
