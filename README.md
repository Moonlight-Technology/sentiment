# Sentiment Dash Prototype

This repository holds the building blocks for a sentiment analysis dashboard. The initial milestone focuses on the ingestion service that normalizes text sources into the shared data contracts under `docs/`.

## Project layout

```
docs/                     # Data contracts + schemas
data/                     # Default location for local SQLite dev database
src/ingestion_service/    # Python ingestion worker package
src/sentiment_service/    # Batch sentiment scoring worker
src/api/                  # FastAPI backend exposing ingestion & sentiment data
web/                      # Next.js + shadcn dashboard (frontend)
```

## Requirements

- Python 3.10+
- `pip install -e .` (installs FastAPI, Pydantic, feedparser, httpx, etc.)
- Node.js 18+ (for the Next.js dashboard)
- PostgreSQL 13+ (recommended for multi-service deployments; SQLite works for local prototyping)

## Ingestion Service

The ingestion worker pulls RSS/Atom entries, converts them into `TextItem` payloads, validates via Pydantic, and stores them in a relational database through SQLAlchemy (Postgres in production, SQLite by default for local development). Configuration uses environment variables prefixed with `INGESTION_` and can be provided via a `.env` file (see `.env.example`).

### Configuration keys

| Variable | Description | Default |
| --- | --- | --- |
| `INGESTION_FEED_URL` | Source RSS/Atom URL | **required** |
| `INGESTION_SOURCE_TYPE` | High-level source label stored in each `TextItem` | `rss_feed` |
| `INGESTION_LANGUAGE` | ISO language code applied to each item | `en` |
| `INGESTION_STORAGE_PATH` | Legacy JSONL path (unused once DB is enabled) | `data/text_items.jsonl` |
| `INGESTION_DATABASE_URL` | SQLAlchemy database URL (Postgres or SQLite) | `sqlite:///data/sentiment.db` |

### Running a one-off ingestion

```bash
cp .env.example .env  # update the feed URL and database connection
python -m ingestion_service.ingestor
```

On startup the script auto-creates the required tables (if they do not exist) and logs how many new items were inserted. Each run skips entries whose `source_id` already exists in the database.

## Docker (VPS Deploy)

This setup runs Postgres and the ingestion worker in containers. The worker runs once per invocation; schedule it with cron if you want repeated ingestion.

### 1) Configure environment

Create a `.env` file at the repo root:

```bash
INGESTION_FEED_URL=https://www.cnnindonesia.com/nasional/rss
INGESTION_SOURCE_TYPE=rss_feed
INGESTION_LANGUAGE=id
INGESTION_DATABASE_URL=postgresql+psycopg://sentiment:sentiment@db:5432/sentiment_dash
```

### 2) Build and run

```bash
docker compose up -d --build
```

### 3) Run ingestion on a schedule (cron example)

```bash
crontab -e
```

Add a line like this (every 30 minutes):

```bash
*/30 * * * * cd /path/to/sentiment_dash && docker compose run --rm ingestor
```

### Database schema

Core tables:

- `text_items` – normalized ingestion payloads matching the `TextItem` data contract.
- `sentiment_results` – sentiment outputs linked via `text_item_id`.
- `sources` – configured ingestion sources (type, config, schedule, status) used by the API/front-end for CRUD and monitoring.
- `keyword_sentiments` – cached aggregates mapping keywords to sentiment distributions for fast keyword analytics.
- `keyword_sentiments` – cached aggregates mapping keywords to sentiment distributions for fast keyword analytics.

Trigger a re-crawl from the dashboard (or `POST /sources/reload`) to synchronously run the ingestion worker for every configured source. Each source row tracks status/last run/error fields reflecting the latest attempt.

Supported source types:

- `rss`/`twitter`/`instagram` – expect `config.url` in the source definition.
- `csv` – expect `config.path` pointing at a CSV file accessible to the backend (columns: `body`/`text` required, optional `title`, `published_at`, `link`).

When pointing at Postgres, ensure the configured user has privileges to create these tables (or run the script once with an admin role).

## Sentiment Worker

The sentiment worker scores any ingested `TextItem` records that do not yet have a `SentimentResult` for the configured model. By default it uses Hugging Face's IndoBERT checkpoints which work well for Bahasa Indonesia news/articles.

```bash
# configure the model/database connection (optional if you reuse ingestion defaults)
export SENTIMENT_MODEL_NAME=mdhugol/indonesia-bert-sentiment-classification
export SENTIMENT_DATABASE_URL=sqlite:///data/sentiment.db

python -m sentiment_service.worker
```

Environment keys (prefixed with `SENTIMENT_`):

| Variable | Description | Default |
| --- | --- | --- |
| `MODEL_NAME` | Hugging Face model id used for scoring. | `mdhugol/indonesia-bert-sentiment-classification` |
| `MODEL_REVISION` | Optional git/ref tag for deterministic weights. | `latest available` |
| `MODEL_VERSION` | Value persisted to `sentiment_results.model_version`. Falls back to revision/`latest`. | `None` |
| `DATABASE_URL` | SQLAlchemy URL (reuse ingestion DB). | `sqlite:///data/sentiment.db` |
| `BATCH_LIMIT` | Max records scored per run. | `32` |
| `PIPELINE_STAGE` | Stored `pipeline_stage` value. | `batch` |

> ⚠️ The first run will download the selected model from Hugging Face, so make sure the host has network access and enough disk/memory.

## Database & Migrations

The ingestion worker, sentiment worker, and FastAPI app all share the same relational database. For collaborative environments, point the following environment variables to the same Postgres DSN:

- `DATABASE_URL`
- `INGESTION_DATABASE_URL`
- `SENTIMENT_DATABASE_URL`

Migrations are managed via Alembic:

```bash
# apply latest schema changes
alembic upgrade head

# create a new revision after updating SQLAlchemy models
alembic revision -m "add users table"
```

Use `ALEMBIC_DATABASE_URL` if you prefer the migration CLI to connect with a different URL than the running services.

## FastAPI Backend

Launch the API to access authentication, source management, content listings, sentiment analytics, and reporting endpoints defined in the product spec.

```bash
uvicorn api.main:app --reload
```

Auth-sensitive routes expect an `X-Role` header (set to `admin` to unlock admin-only endpoints). Sample requests:

- `POST /auth/login` – username/password both `admin` for the seeded admin user.
- `GET /contents` – lists ingested items with their latest sentiment.
- `POST /sentiment/analyze` – runs on-demand IndoBERT scoring for ad-hoc text.
- `POST /sentiment/run` – executes the batch worker to score pending items.
- `GET /sentiment/keyword-stats?keyword=bbm` – returns cached sentiment distribution for a keyword (`refresh=true` to recompute).
- `POST /sources/import/twitter-csv` – upload Sentiment140-style CSV and ingest tweets into `text_items`.

## Frontend Dashboard

The `web/` folder hosts a Next.js 14 + shadcn UI that consumes the FastAPI service. Configure the base URL via `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

```bash
cd web
npm install
npm run dev
```

The dashboard ships with routes for:

- `/` – overview cards, trend charts, keyword badges.
- `/users`, `/sources`, `/sentiment`, `/reports`, `/branding`, `/security`, `/system` – cover the v1 feature list (user/data source CRUD stubs, sentiment monitor, analytics, white-label settings, audit/security, ops status).

Login via `/login` (seeded `admin/admin` credentials) to store the issued token + role in `localStorage` for subsequent API calls.

## Next steps

1. Hook the ingestion run into a scheduler (cron, Prefect, etc.).
2. Secure the API with real JWT-based auth + persistent user store.
3. Build the dashboard UI and wire it to the new endpoints.
