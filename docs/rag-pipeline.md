# RAG Pipeline

## Overview

```
source ingestion
 → document parsing
 → cleaning
 → chunking
 → metadata extraction
 → embedding generation
 → vector storage (pgvector)
 → query embedding
 → similarity search
 → metadata filtering
 → retrieval ranking
 → evidence selection
 → recommendation grounding
```

## Source ingestion

Local knowledge lives under `knowledge/sources/<id>/`:

- `manifest.yaml` — real institutional metadata (title, org, year, URL, topic)
- `content.md` — retrieval-oriented summary derived from public guidance

CLI:

```bash
python scripts/ingest_knowledge.py --knowledge-dir knowledge
```

API:

`POST /api/v1/knowledge/ingest`

## Chunking

`KnowledgeIngestionService` cleans whitespace, splits on paragraphs, and builds
~700 character chunks with ~100 character overlap. Each chunk stores source
metadata for attribution.

## Embeddings

`EmbeddingProvider` abstraction:

- `mock` — deterministic hash embeddings (offline / CI)
- `openai` — API embeddings

Configured via `EMBEDDING_PROVIDER`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`,
`EMBEDDING_DIMENSIONS`.

## Vector storage

`knowledge_chunks.embedding` uses pgvector (`vector(384)` by default) with an
HNSW cosine index.

## Query → retrieval

1. Query analyzer extracts variables.
2. `RetrievalService.build_retrieval_query` expands variables into a retrieval string.
3. Query is embedded.
4. SQL cosine distance search returns top-k chunks with source joins.
5. Optional topic filter via `topic` parameter.
6. Minimum similarity threshold applied.
7. Lexical overlap fallback if no vector hits.

## Example retrieval flow

**User:** “Soil organic carbon is 0.3%, rainfall is low, wheat monoculture, biodiversity declining.”

**Retrieval query (simplified):**
`biodiversity decline soil organic carbon … rainfall water availability … monoculture habitat diversity …`

**Returned:** FAO soil carbon, FAO agroecology, IPCC land/climate, CBD connectivity chunks with similarity scores and URLs.

## Developer demonstration

`POST /api/v1/knowledge/search`

```json
{
  "query": "relationship between soil organic carbon biodiversity low rainfall monoculture",
  "top_k": 5
}
```

Returns chunk text, source metadata, similarity, topic.
