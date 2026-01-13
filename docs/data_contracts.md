# Sentiment Dash Data Contracts

This document defines the canonical payloads flowing through the ingestion and sentiment services. JSON Schema files live in `docs/schemas/` for programmatic validation.

## 1. Text Item Contract (`TextItem`)
Represents any textual artifact pulled into the platform (news, Instagram captions, comments).

- Schema: [`schemas/text_item.schema.json`](schemas/text_item.schema.json)
- Primary key: `id` (UUID v4 recommended)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | ✅ | Stable identifier issued when the item enters the pipeline. |
| `source_type` | string | ✅ | Logical channel: `news_api`, `rss_feed`, `instagram_post`, etc. |
| `source_id` | string | ✅ | Identifier native to the source (URL, IG media/comment id). |
| `source_metadata` | object | | Flexible blob for source-specific attributes (author, follower count). |
| `ingested_at` | string (date-time) | ✅ | UTC timestamp when we stored the item. |
| `published_at` | string (date-time) | | Original publish time when available. |
| `language` | string | ✅ | ISO 639-1/639-3 code from language detection. |
| `title` | string | | Title, headline, or summary. |
| `body` | string | ✅ | Cleaned text body (HTML stripped, normalized). |
| `entities` | array<object> | | Optional entity extraction results with `type`, `value`, `confidence`. |
| `labels` | array<string> | | Manual QA/training labels. |

### Sample Payload
```json
{
  "id": "48c8c9c6-41a0-4b9d-94fb-fb8819c8f5a3",
  "source_type": "rss_feed",
  "source_id": "https://example.com/news/123",
  "source_metadata": {
    "author": "Jane Smith",
    "section": "Markets"
  },
  "ingested_at": "2024-05-12T08:33:21Z",
  "published_at": "2024-05-12T08:00:00Z",
  "language": "en",
  "title": "Tech stocks rally on upbeat forecasts",
  "body": "Shares of major tech companies rose on Monday after analysts raised their forecasts...",
  "entities": [
    {"type": "ticker", "value": "AAPL", "confidence": 0.93},
    {"type": "company", "value": "Microsoft", "confidence": 0.88}
  ],
  "labels": ["watchlist"]
}
```

## 2. Sentiment Result Contract (`SentimentResult`)
Represents the output of a sentiment model run tied to a `TextItem`.

- Schema: [`schemas/sentiment_result.schema.json`](schemas/sentiment_result.schema.json)
- Primary key: `id`
- Foreign key: `text_item_id` → `TextItem.id`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | ✅ | Unique inference identifier (UUID). |
| `text_item_id` | string | ✅ | Links back to the originating `TextItem`. |
| `model_name` | string | ✅ | Short name (`hf_roberta`, `vader`, `custom_roberta`). |
| `model_version` | string | ✅ | Semantic version, git SHA, or API version. |
| `pipeline_stage` | string | | Where the inference occurred (`batch`, `realtime`, `retrain_eval`). |
| `scored_at` | string (date-time) | ✅ | UTC timestamp when the score was produced. |
| `label` | enum | ✅ | Primary sentiment class (`positive`, `neutral`, `negative`). |
| `score` | number | ✅ | Confidence/likelihood for `label` (0–1). |
| `scores_by_label` | object | | Optional distribution map, e.g., `{ "positive": 0.74, ... }`. |
| `explanations` | array<object> | | Token-level attributions (`text`, `importance`). |
| `annotations` | object | | Manual reviewer notes or overrides. |

### Sample Payload
```json
{
  "id": "6fa4f6cb-3fdf-4d6f-b3db-2c8a0cd52a83",
  "text_item_id": "48c8c9c6-41a0-4b9d-94fb-fb8819c8f5a3",
  "model_name": "hf_roberta",
  "model_version": "1.0.0",
  "pipeline_stage": "batch",
  "scored_at": "2024-05-12T08:34:10Z",
  "label": "positive",
  "score": 0.82,
  "scores_by_label": {
    "positive": 0.82,
    "neutral": 0.14,
    "negative": 0.04
  },
  "explanations": [
    {"text": "rally", "importance": 0.53},
    {"text": "upbeat", "importance": 0.42}
  ],
  "annotations": {
    "reviewer": "analyst_1",
    "status": "approved"
  }
}
```

## 3. Event Flow & Versioning
1. **Ingestion service** emits a `TextItem` JSON blob and stores it (database or object storage). The `id` acts as the correlation handle for all downstream processing.
2. **Preprocessing** can enrich the same record with `entities`, `language`, or `labels` but must preserve the original `id` and raw text snapshot.
3. **Sentiment worker** consumes a `TextItem`, produces a `SentimentResult`, and stores it with `text_item_id` referencing the source item.
4. **Dashboard/API** query pattern:
   - Fetch latest `SentimentResult` per `text_item_id` for standard views.
   - Keep multiple rows per `text_item_id` when testing model variants; clients filter by `model_name`/`model_version`.

Version compatibility advice:
- Introduce additive fields as optional first, then backfill, so consumers remain forward-compatible.
- Bump `model_version` whenever weights or preprocessing steps change.

## 4. Future Extensions
- Add `media` arrays to `TextItem` when Instagram assets arrive (store URLs + alt text).
- Extend `label` enum for fine-grained moods (`very_positive`, `mixed`) without breaking existing clients by keeping `scores_by_label` authoritative.
- Define a `FeedbackEvent` contract once human-in-the-loop review is required.
