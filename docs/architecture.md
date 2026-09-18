# System Architecture

Darukaa.Earth AI Biodiversity Intelligence Chatbot is an **AI environmental
intelligence system** rather than an LLM-only chatbot. Every recommendation is
produced through retrieval, multi-metric reasoning, and evidence validation.

## Pipeline

```
USER
 ↓
CHAT API
 ↓
QUERY ANALYZER
 ↓
MISSING INFORMATION DETECTOR
 ↓
ENVIRONMENTAL CONTEXT BUILDER
 ↓
RAG RETRIEVER (pgvector)
 ↓
VECTOR DATABASE
 ↓
EVIDENCE CONTEXT
 ↓
MULTI-METRIC REASONING ENGINE
 ↓
RECOMMENDATION ENGINE
 ↓
EVIDENCE VALIDATOR
 ↓
STRUCTURED RESPONSE
 ↓
FRONTEND
```

## Components

### Chat API (`backend/app/api/routes/chat.py`)
Creates conversations, stores messages, and invokes the chat pipeline.

### Query Analyzer (`backend/app/services/ai/query_analyzer.py`)
Extracts environmental variables, problems, land-use types, climate conditions,
biodiversity indicators, geography, numerical values, and units. Merges with
conversation memory.

### Missing Information Detector
Part of query analysis. Tracks `known_variables`, `missing_variables`,
`critical_variables`, and `optional_variables`. Asks targeted clarifying
questions when fewer than three material variables are available.

### Environmental Context (`backend/app/services/ai/context_builder.py`)
Builds a structured environmental state (soil, climate, land use, biodiversity,
human impact, geography) with provenance markers.

### RAG Retriever (`backend/app/services/ai/retrieval.py`)
Embeds the retrieval query, searches `knowledge_chunks.embedding` with pgvector
cosine distance, applies optional topic filters, ranks by similarity, and
returns source metadata with each chunk. Lexical fallback exists if vectors are
empty.

### Multi-metric Reasoning (`backend/app/services/ai/reasoning_engine.py`)
Connects ≥3 variables when available, producing concise evidence-supported
relationship summaries (not private chain-of-thought).

### Recommendation Engine (`backend/app/services/ai/recommendation_engine.py`)
Scores intervention candidates by **retrieved evidence themes + environmental
state tags**. Does not hard-code `if wheat then cover crops` chatbot replies.

### Evidence Validator (`backend/app/services/ai/evidence_validator.py`)
Rejects recommendations without evidence, strips unsupported quantitative
claims, removes fabricated URLs, and adjusts confidence.

### Frontend
React assistant UI for chat, context, reasoning, recommendations, evidence,
history, retrieval debug, and demo mode.
