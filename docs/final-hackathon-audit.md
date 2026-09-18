# Darukaa.Earth Final Hackathon Audit

**Project:** Darukaa.Earth — AI Biodiversity Intelligence Chatbot  
**Repository:** `/home/irfan/Ubuntu-workspace/darukaa-ai-chatbot`  
**Audit date:** 2026-09-18  
**Scope:** Standalone chatbot repository only (no dependency on other Darukaa apps)

Evidence labels used below:

- **Verified by execution** — exercised live API/DB/tests
- **Verified by code inspection** — read source/migrations/docs
- **Partially verified** — mixed evidence
- **Not verified** — not run or inconclusive
- **Missing** — absent from implementation

---

## 1. Executive Summary

This repository is a standalone FastAPI + React chatbot with PostgreSQL/pgvector RAG, conversation memory, multi-metric environmental reasoning, recommendation cards, and evidence validation. Live verification confirms:

- Database + pgvector ready
- 8 institutional knowledge sources / 29 embedded chunks
- Vector retrieval returns relevant FAO/IPCC/CBD/etc. chunks
- Clarifying questions + multi-turn memory + rainfall counterfactual context update
- Recommendations include action, reasoning, metrics, horizon, confidence, evidence
- Unsupported percentage fabrication not observed in adversarial runs
- Backend 13/13 pytest, frontend 3/3 vitest, production build OK
- Docker images build successfully; only DB container currently composed up

Remaining weaknesses: embeddings currently run in **mock** mode (Groq chat LLM configured); follow-up recommendation sets still similar after rainfall counterfactual; knowledge texts are institutional summaries (not full PDFs); no git commits yet; CI remote runs not verified; full `docker compose up` of all services not end-to-end tested due to local port occupancy.

---

## 2. Actual Architecture

```text
React (Vite) UI
  → HTTP /api/v1/*
FastAPI (app/main.py)
  → ChatPipeline (services/conversation/service.py)
      → QueryAnalyzer
      → Missing-info / clarification OR off-topic gate
      → RetrievalService (pgvector cosine + lexical fallback)
      → ReasoningEngine (multi-metric relationships)
      → RecommendationEngine (evidence-theme scoring)
      → EvidenceValidator
      → ResponseFormatter → StructuredAIResponse JSON
  → Frontend cards: context, reasoning, recommendations, evidence
```

Verified by code inspection + live `/health/ready` and chat pipeline execution.

---

## 3. Technology Stack

### Backend (executed)

| Component | Version |
|---|---|
| Python | 3.14.4 (local venv); CI uses 3.12 |
| FastAPI | 0.141.1 |
| Pydantic | 2.13.5 |
| SQLAlchemy | 2.0.54 |
| Alembic | 1.20.0 |
| pgvector (Python) | 0.5.0 |
| httpx / uvicorn / numpy | 0.28.1 / 0.53.0 / 2.5.3 |

### Frontend (package.json)

| Component | Version |
|---|---|
| React | ^18.3.1 |
| TypeScript | ^5.6.3 |
| Vite | ^5.4.10 |
| Vitest + Testing Library | ^2.1.4 / ^16.0.1 |
| Router | react-router-dom ^6.28.0 |
| HTTP | native `fetch` |

No Redux/Zustand; local React state.

### Database (executed)

- PostgreSQL **16.15** via `pgvector/pgvector:pg16`
- Port mapping **5433→5432**
- Extension `vector` enabled
- Embedding column dims **384**
- HNSW index `ix_knowledge_chunks_embedding`

### AI/RAG (executed + inspection)

| Item | Current value |
|---|---|
| LLM abstraction | `LLMProvider` (`mock` / `openai` / `anthropic`) |
| Active LLM | OpenAI-compatible client → **Groq** (`LLM_BASE_URL=https://api.groq.com/openai/v1`, model `openai/gpt-oss-20b`) |
| Embedding abstraction | `EmbeddingProvider` (`mock` / `openai`) |
| Active embeddings | **mock** (deterministic hash vectors) |
| Retrieval | pgvector cosine distance SQL + lexical fallback |
| Prompts | `backend/app/prompts/*.py` |

### Infrastructure

- `docker-compose.yml` (db, backend, frontend)
- GitHub Actions `.github/workflows/ci.yml` (backend+pgvector, frontend, docker build)
- Deploy notes: `deploy/render.md`, `deploy/vercel.md`
- Env templates: `.env.example`, `frontend/.env` (gitignored)

---

## 4. Database Audit

**Status: PASS (Verified by execution)**

| Question | Answer |
|---|---|
| Knowledge sources | `knowledge_sources` (8 rows) |
| Chunks | `knowledge_chunks` (29 rows, all with embeddings) |
| Embeddings | `knowledge_chunks.embedding vector(384)` |
| Generation | ingest → `EmbeddingProvider.embed` |
| Search | `1 - (embedding <=> query)` cosine similarity |
| Conversations | `conversations`, `conversation_messages`, `conversation_context` |
| Environmental context | JSONB on `conversation_context` + optional `environmental_observations` |
| Context persisted | Yes (verified via GET conversation after multi-turn) |
| Vector similarity used | Yes (live search returned ranked similarity scores) |
| PostgreSQL used | Yes (`localhost:5433/darukaa_ai`) |
| pgvector enabled | Yes (`/health/ready` + `pg_extension`) |
| Migrations reproducible | Alembic `0001_initial` present; upgrade succeeded previously |

---

## 5. Knowledge System Audit

**Status: PASS / PARTIAL depth**

| Metric | Value |
|---|---|
| Sources | 8 |
| Documents | 8 |
| Chunks | 29 |
| Orgs | FAO, IPCC, CBD, UNCCD, IPBES |
| Topics | soil_health, land_use, climate, biodiversity, human_impact |
| Content type | Institutional guidance **summaries** (not full PDFs) |
| Fabricated papers | Not found; URLs point to real org pages (inspection) |

Pipeline (inspection): manifest YAML + markdown → clean → chunk → embed → store (`KnowledgeIngestionService`).

CLI: `python scripts/ingest_knowledge.py`

---

## 6. RAG Verification

**Status: PASS (Verified by execution)** via `POST /api/v1/knowledge/search`

| Query | Hits | Top source (example) | Similarity |
|---|---|---|---|
| Soil organic carbon ↔ biodiversity | 5 | FAO Soil Organic Carbon | ~0.46 |
| Low rainfall ↔ habitat quality | 5 | CBD connectivity themes | present |
| Monoculture ↔ soil/biodiversity | 5 | FAO Agroecology | present |
| Land-use change ↔ fragmentation | 5 | IPBES land degradation | present |
| Practices improve soil carbon + biodiversity | 5 | FAO Soil Organic Carbon | present |

Chat turns with enough variables used retrieval (`sources_used` 3–4, `chunks_used` 6) and attached evidence titles to recommendations.

**Caveat:** active embeddings are mock; retrieval still ranked relevant institutional text, but this does **not** prove OpenAI embedding quality.

---

## 7. Query Analysis

**Status: PASS (Verified by execution)**

Natural language extract example:

- Input declining biodiversity + lower rainfall + continuous wheat
- Detected: rainfall=low, land_use=continuous_monoculture, crop=wheat

Structured analyze / structured chat input:

- Variables accepted via `structured_input` and `/environment/analyze`
- Structured chat produced ≥3 variables and recommendations (execution)

Invalid `soil_organic_carbon: "abc"` now rejected/dropped after fix (known={}).

---

## 8. Clarification System

**Status: PASS**

Turn 1 “Biodiversity is declining on my land.” → `needs_clarification=true`, asks SOC / rainfall / land use; no recommendations.

---

## 9. Conversation Memory

**Status: PASS (context) / PARTIAL (answer specificity before fix)**

Verified sequence:

1. Clarification asked
2. Values stored (`soil_organic_carbon=0.3`, `rainfall=low`, wheat monoculture)
3. Follow-ups did not re-ask those values
4. “What if rainfall increases…” updated context rainfall → `high`
5. Persisted context via GET conversation

Before fix, “Why would that help?” / “Which metrics…” returned near-identical generic recommendation blurbs. After fix, tailored answers verified.

---

## 10. Multi-Metric Reasoning

**Status: PASS (Verified by execution)**

Scenario with SOC + rainfall + monoculture (+crop):

- `variables_considered` included soil organic carbon, rainfall, land use, crop
- Reasoning summaries referenced combined soil/climate/land-use pressure
- Recommendations targeted cover crops, water retention, reduced disturbance

Scenario B (pH, rainfall, intensive agriculture, pollution): variables detected.

Scenario C (temperature, rainfall decline, fragmentation, deforestation): variables detected with LLM assist.

Counterfactual rainfall update changes context; recommendation **titles** can remain similar (PARTIAL adaptation depth).

---

## 11. Recommendation System

**Status: PASS**

Observed fields on live recommendations:

- title, action, scientific_reasoning
- impacted_metrics
- time_horizon (short/medium/long)
- confidence (0–1)
- evidence[] with source_title/org/year/url/snippet
- estimated_effect set to non-fabricated uncertainty text when unsupported

Specificity is intervention-level (cover crops, corridors, etc.), not only “be sustainable”.

---

## 12. Evidence Validation

**Status: PASS (Verified by execution + inspection)**

- Validator runs before response (`EvidenceValidator.validate`)
- Recommendations without evidence rejected
- Quantitative claims without supporting snippet stripped / uncertainty text used
- Adversarial “91%” / “73%” requests did not produce those fabricated percentages
- No API key leakage observed

Limitation: validation is heuristic + schema checks; not a formal citation verifier against remote URLs.

---

## 13. Structured Input

**Status: PASS**

- `MessageCreate.structured_input` supported
- `/api/v1/environment/analyze` accepts `variables`
- Live structured chat produced multi-metric recommendations

---

## 14. API Audit

Endpoints (OpenAPI):

- `GET /health`, `GET /health/ready`
- `POST/GET /api/v1/chat/conversations`, `GET .../{id}`, `POST .../{id}/messages`
- `POST /api/v1/knowledge/search|ingest`, `GET /api/v1/knowledge/sources`
- `POST /api/v1/environment/analyze|observations`

Error handling verified:

- empty message → 422
- missing conversation → 404

Auth: not required (intentional for demo).

---

## 15. Frontend Audit

**Status: PASS (component tests + build); integration Partially verified**

Screens: AI Assistant, History, Context, Knowledge Retrieval, Demo Mode.

Component tests cover recommendation cards, environmental context, reasoning summary.

Browser UI previously verified against API after VITE_API_URL fix; this audit re-confirmed frontend build/tests, not a fresh full browser walkthrough of every page.

---

## 16. End-to-End Test

**Status: PASS (API execution)** — 6-turn evaluator script run against live `:8001`.

See Section 13 of the console report for turn-by-turn evidence. Post-fix follow-ups for why/metrics verified separately.

---

## 17. Adversarial Tests

| Test | Result | Notes |
|---|---|---|
| Generic biodiversity ask | PASS | Clarifies rather than hallucinating site advice |
| Missing data (“land unhealthy”) | PASS | Clarifies |
| Contradictory rainfall | PARTIAL | Clarifies / LLM may encode conflict string; no dedicated contradiction explainer |
| Unsupported exact % | PASS | No fabricated %; uncertainty effect text |
| Citation pressure 73% | PASS | No 73% fabricated |
| Prompt injection fake DOI/91% | PASS | No 91% / no key leak |
| Irrelevant programming Q | PASS (after fix) | Declines off-topic |
| Reveal API keys | PASS | No secrets in response |

---

## 18. Test Suite Results

| Suite | Result |
|---|---|
| Backend pytest | **13 passed**, 2 warnings |
| Frontend vitest | **3 passed** |
| Frontend build | **PASS** |
| Ruff check | **PASS** (after format) |
| Ruff format --check | **PASS** (after format) |

Coverage tooling not used to publish %. Important gaps: limited frontend integration tests; no dedicated adversarial pytest; CI remote not run.

---

## 19. Docker Verification

| Check | Result |
|---|---|
| `docker compose config` | PASS (exit 0) |
| `docker compose build` | PASS (backend+frontend images built) |
| `docker compose ps` | DB healthy on 5433; backend/frontend not composed up in this audit (local uvicorn/vite already bound) |
| Full compose E2E of all 3 services | **NOT VERIFIED** (avoided port conflict with running local stack) |

---

## 20. CI/CD Verification

| Check | Result |
|---|---|
| Workflow present | `.github/workflows/ci.yml` |
| Local syntax/logic inspection | PASS |
| Jobs | backend (pgvector service, ruff, migrate, ingest, pytest), frontend (lint/test/build), docker build |
| Remote GitHub Actions run | **NOT VERIFIED** (no commits/remote yet) |

---

## 21. Security Audit

| Area | Finding |
|---|---|
| Secrets in git tracked files | No API keys found in tracked source via pattern search |
| `.env` gitignore | Yes (`.env`, `frontend/.env`, `backend/.env` ignored) |
| CORS | Explicit localhost/127.0.0.1 origins |
| SQL injection | Parameterized SQLAlchemy/text binds used for retrieval |
| Prompt injection | Declined fabricating stats/keys in tested cases |
| Auth | Absent by design (demo) |
| Process env override risk | Empty/mock shell env vars can override `.env` if exported (ops caveat) |

---

## 22. Documentation Audit

| Doc | Status |
|---|---|
| README.md | Present; ports 8001/5174/5433 documented |
| docs/architecture.md | Present; matches pipeline |
| docs/rag-pipeline.md | Present |
| docs/hackathon-compliance.md | Present (pre-audit self-checklist) |
| deploy/* | Present |
| Stale risk | Compliance doc may overstate embedding “production” mode while local default embeddings are mock |

---

## 23. Hackathon Requirement Matrix

| Requirement | Status | Evidence | File/API/Test |
|---|---|---|---|
| AI biodiversity intelligence | PASS | Environmental clarification + multi-metric recs | ChatPipeline live E2E |
| Knowledge layer | PASS | 8 sources / 29 chunks | DB counts + knowledge/ |
| Soil health | PASS | SOC/pH/moisture extraction + FAO SOC source | query_analyzer + knowledge |
| Land use / cover | PASS | monoculture/agroforestry etc. | query_analyzer + FAO agroecology |
| Biodiversity indicators | PASS | richness/habitat diversity | analyzer + CBD/FAO pollinators |
| Climate factors | PASS | rainfall/temperature | analyzer + IPCC/FAO water |
| Human impact | PASS | pollution/deforestation/fragmentation | analyzer + IPBES/UNCCD |
| RAG | PASS | live search + chat retrieval meta | `/knowledge/search`, ChatPipeline |
| Clarifying questions | PASS | Turn 1 E2E | ChatPipeline |
| Conversation memory | PASS | Turns 2–6 retain vars | conversation_context |
| Evidence-backed recommendations | PASS | evidence arrays + validator | recommendation_engine + evidence_validator |
| Multi-metric reasoning | PASS | ≥3 vars in E2E/scenarios | reasoning_engine |
| Text input | PASS | chat messages | `/messages` |
| Structured input | PASS | structured_input + analyze | schemas/chat.py |
| Geographic context | PARTIAL | region/lat/lon parsed; no map/PostGIS | query_analyzer |
| Recommendation output | PASS | cards + schema | frontend + StructuredAIResponse |
| Impacted metrics | PASS | field populated | live recs |
| Time horizon | PASS | short/medium/long | live recs |
| Confidence | PASS | 0–1 values | live recs |

---

## 24. Environmental Variables Supported

Non-secret names only:

`DATABASE_URL`, `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, `EMBEDDING_PROVIDER`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `CORS_ORIGINS`, `SECRET_KEY`, `APP_ENV`, `LOG_LEVEL`, `API_PREFIX`, `VITE_API_URL`, `RETRIEVAL_TOP_K`, `RETRIEVAL_MIN_SIMILARITY`

---

## 25. Issues Found

### CRITICAL

None blocking core demo path after fixes.

### HIGH

1. **Follow-up answer collapse (fixed)** — `ChatPipeline.handle_message` reused identical recommendation blurb for “why/metrics” questions.  
2. **Embedding provider mock in active env** — retrieval quality not production-embedding verified; OpenAI embeddings previously 429.

### MEDIUM

3. **Counterfactual recommendations weakly adapt** — rainfall→high updates context but often keeps water-retention-first ranking.  
4. **Contradiction handling shallow** — conflicting rainfall not explicitly explained.  
5. **Knowledge depth** — summaries vs full scientific PDFs.  
6. **No remote CI / no commits** — GitHub Actions never executed on a remote.  
7. **Full docker compose app stack E2E** — build verified; all-services runtime not verified here.

### LOW

8. Frontend lint is `tsc --noEmit` only (no ESLint ruleset).  
9. Limited frontend integration/e2e tests.  
10. Clarification copy historically said “default” for unknown problem label (UX).

---

## 26. Fixes Applied During This Audit

1. `backend/app/services/conversation/service.py` — off-topic gate; why/metrics/counterfactual answer shaping  
2. `backend/app/services/environment/service.py` — reject non-numeric metric strings like `"abc"`  
3. Ruff format cleanup across touched files  
4. Created this document: `docs/final-hackathon-audit.md`

---

## 27. Remaining Issues

- Switch embeddings to a working provider when quota allows; re-ingest  
- Improve counterfactual re-ranking when climate variables change  
- Explicit contradiction responses  
- Commit repo + push to enable CI  
- Optional: full `docker compose up` E2E on free ports  
- Optional: richer PDF ingestion

---

## 28. Final Verification Results

Commands run (selected):

```bash
curl /health /health/ready
pytest -q
npm test && npm run build
ruff check && ruff format --check
docker compose config
docker compose build
python audit script → /tmp/darukaa-audit-results.json
```

| Area | Result |
|---|---|
| Backend tests | 13 passed |
| Frontend tests | 3 passed |
| Build | PASS |
| Docker build | PASS |
| Docker full stack E2E | NOT VERIFIED |
| RAG | PASS (mock embeddings) |
| Conversation memory | PASS |
| Multi-metric reasoning | PASS |
| Evidence validation | PASS |
| Frontend integration | PARTIAL |
| Security | PASS (local scan) |
| Documentation | PASS / PARTIAL freshness |
