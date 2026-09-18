# Backend deployment (Render)

## Service type
Web Service

## Runtime
Python 3

## Root directory
`backend`

## Build command
```bash
pip install -r requirements.txt
```

## Start command
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Required environment variables
- `DATABASE_URL` — Render PostgreSQL connection string (use `postgresql+psycopg://...`)
- `LLM_PROVIDER` — `mock` | `openai` | `anthropic`
- `LLM_API_KEY`
- `LLM_MODEL`
- `EMBEDDING_PROVIDER` — `mock` | `openai`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSIONS` — must match migration vector size (default `384`)
- `CORS_ORIGINS` — your Vercel frontend URL
- `SECRET_KEY`

## Database
Provision PostgreSQL and enable the `vector` extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

If using a standard Render Postgres image without pgvector, provision an external
pgvector-compatible database instead.

## Post-deploy
Run knowledge ingestion once (Render shell or one-off job):

```bash
python ../scripts/ingest_knowledge.py --knowledge-dir ../knowledge
```

Ensure the `knowledge/` directory is available in the deploy artifact or mount.
