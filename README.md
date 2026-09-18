# Darukaa.Earth — AI Biodiversity Intelligence Chatbot

An **AI environmental intelligence system** rather than an LLM-only chatbot.

This standalone project retrieves scientific/institutional knowledge with
**pgvector RAG**, reasons across **multiple environmental variables**, asks
**clarifying questions**, maintains **multi-turn conversation memory**, and
returns **evidence-validated recommendations**.

It has **no dependency** on any previous Darukaa Earth full-stack application.

## Problem statement

Land managers and evaluators need decision support that:

1. Understands soil, climate, land use, biodiversity, and human-impact context
2. Retrieves credible environmental knowledge
3. Connects multiple metrics (not single-variable tips)
4. Shows why a recommendation was made, with sources

## Hackathon requirements addressed

See [`docs/hackathon-compliance.md`](docs/hackathon-compliance.md) for the full
checklist. Coverage includes soil health, land use/cover, biodiversity, climate,
human impact, RAG retrieval, clarifying questions, conversation memory,
structured recommendations with evidence, Docker, CI/CD, and deployment docs.

## System architecture

See [`docs/architecture.md`](docs/architecture.md).

```
User → Chat API → Query Analyzer → Missing-Info Check
     → Environmental Context → RAG Retriever (pgvector)
     → Multi-metric Reasoning → Recommendation Engine
     → Evidence Validator → Structured JSON → Frontend
```

## RAG architecture

See [`docs/rag-pipeline.md`](docs/rag-pipeline.md).

## Technology stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL + pgvector |
| AI | Pluggable LLM + Embedding providers (`mock` / `openai` / `anthropic`) |
| Frontend | React, TypeScript, Vite |
| Tests | Pytest, Vitest |
| DevOps | Docker Compose, GitHub Actions |

## Folder structure

```
.
├── backend/           # FastAPI app, migrations, tests
├── frontend/          # React assistant UI
├── knowledge/         # Ingestible institutional knowledge sources
├── scripts/           # Ingestion CLI, DB init
├── docs/              # Architecture, RAG, compliance
├── tests/evaluator/   # Evaluator scenario documentation
├── deploy/            # Render / Vercel notes
├── docker-compose.yml
├── .env.example
└── README.md
```

## Database schema

- `knowledge_sources`, `knowledge_documents`, `knowledge_chunks` (+ embedding)
- `conversations`, `conversation_messages`, `conversation_context`
- `environmental_observations`
- Optional `users` table (auth not required for demo)

## Knowledge sources

Attributed institutional summaries (not invented papers), including:

- FAO — soil organic carbon, agroecology, water/land resources, pollinators
- IPCC — Climate Change and Land (SRCCL)
- CBD — habitat connectivity themes
- UNCCD — land degradation / restoration themes
- IPBES — land degradation and restoration assessment themes

## Local setup

### Prerequisites

- Docker & Docker Compose **or** local PostgreSQL 16 + pgvector
- Python 3.12+
- Node.js 20+

### 1. Environment

```bash
cp .env.example .env
```

Default providers are `mock` so the system runs without API keys.

### 2. Start database + apps (Docker)

```bash
docker compose up --build
```

- API: http://localhost:8001/docs
- UI: http://localhost:5174
- Health: http://localhost:8001/health
- Database: localhost:5433 (mapped to avoid conflicts with other local Postgres instances)

### 3. Local development (without full compose)

```bash
# DB only
docker compose up -d db

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
cd ..
python scripts/ingest_knowledge.py
cd backend && uvicorn app.main:app --reload --port 8001

# Frontend (new terminal)
cd frontend
npm install
npm run dev -- --port 5174
```

## Knowledge ingestion

```bash
python scripts/ingest_knowledge.py --knowledge-dir knowledge
```

Or `POST /api/v1/knowledge/ingest` with document body + source metadata.

## API (selected)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/health/ready` | DB + pgvector readiness |
| POST | `/api/v1/chat/conversations` | Create conversation |
| POST | `/api/v1/chat/conversations/{id}/messages` | Chat turn |
| GET | `/api/v1/chat/conversations` | List |
| GET | `/api/v1/chat/conversations/{id}` | Detail + context |
| POST | `/api/v1/knowledge/search` | Retrieval debug |
| POST | `/api/v1/knowledge/ingest` | Ingest document |
| GET | `/api/v1/knowledge/sources` | List sources |
| POST | `/api/v1/environment/analyze` | Parse/analyze variables |
| POST | `/api/v1/environment/observations` | Store observation |

OpenAPI: `/docs`

## Frontend

Screens:

1. AI Assistant
2. Conversation History
3. Environmental Context
4. Knowledge Retrieval (developer/evaluator)
5. Demo Mode

Recommendation cards show action, reasoning, metrics, direction, horizon,
confidence, and expandable evidence.

## Demo scenarios

Labeled **Synthetic Demo Data** in the UI. See also
`tests/evaluator/scenarios.md`.

Example evaluator prompt:

> Soil organic carbon is 0.3%, rainfall is low, I grow wheat continuously in a
> semi-arid region and biodiversity is declining.

Then ask:

> Why did you recommend that?

> What if rainfall increases?

## Environment variables

See `.env.example`:

- `DATABASE_URL`
- `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_MODEL`
- `EMBEDDING_PROVIDER` / `EMBEDDING_API_KEY` / `EMBEDDING_MODEL`
- `CORS_ORIGINS`
- `SECRET_KEY`
- `VITE_API_URL`

Never commit real secrets.

## Tests

```bash
# Backend
cd backend
pytest -q

# Frontend
cd frontend
npm test
npm run build
```

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):

- Backend: ruff, migrations, knowledge ingest, pytest (with pgvector service)
- Frontend: test + production build
- Docker Compose build

## Deployment

- Frontend → Vercel (`deploy/vercel.md`)
- Backend → Render (`deploy/render.md`)
- Database → PostgreSQL with `vector` extension

## Example questions

- Biodiversity is declining on my land.
- Soil organic carbon is 0.3%, rainfall is low, wheat monoculture, semi-arid.
- Habitat fragmentation is high and species richness is 12.
- Elevated pollution on degraded land — what should I prioritize?

## Limitations

- Mock LLM/embeddings are deterministic and offline-friendly; production quality
  improves with real provider keys.
- Knowledge texts are institutional summaries for RAG grounding, not full PDFs.
- Geographic support is attribute-level (region/lat/lon), not a full GIS stack.
- Auth is intentionally minimal for hackathon evaluation speed.

## Future improvements

- Full document PDF parsing
- Stronger cross-encoder re-ranking
- Optional PostGIS layers for regional priors
- Streaming chat responses
- Evaluator scorecards persisted per scenario

## License

Hackathon / evaluation use. Respect upstream source licenses when redistributing
knowledge content.
