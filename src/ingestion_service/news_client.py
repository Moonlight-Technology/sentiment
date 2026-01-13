"""Fetches articles from RSS/Atom feeds."""
from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List

import feedparser
import httpx

from .models import ArticleSummary


class NewsFeedClient:
    def __init__(self, feed_url: str, timeout: float = 10.0):
        self.feed_url = feed_url
        self.timeout = timeout

    def fetch(self) -> List[ArticleSummary]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self.feed_url)
            response.raise_for_status()
        parsed = feedparser.parse(response.text)
        articles: List[ArticleSummary] = []
        for entry in parsed.entries:
            published = _parse_datetime(getattr(entry, "published", None))
            article = ArticleSummary(
                id=getattr(entry, "id", getattr(entry, "link", "")),
                title=getattr(entry, "title", "Untitled"),
                link=getattr(entry, "link"),
                summary=getattr(entry, "summary", getattr(entry, "description", "")),
                published=published,
            )
            articles.append(article)
        return articles


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (ValueError, TypeError):
        return None
