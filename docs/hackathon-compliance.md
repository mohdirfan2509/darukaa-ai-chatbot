# Hackathon Compliance Checklist

Status legend: **IMPLEMENTED** | **PARTIALLY IMPLEMENTED** | **NOT IMPLEMENTED**

| Requirement | Status | Location |
|---|---|---|
| Environmental knowledge base | IMPLEMENTED | `knowledge/sources/`, `knowledge_*` tables |
| Soil health | IMPLEMENTED | knowledge sources + query analyzer metrics |
| Land use / land cover | IMPLEMENTED | analyzer + FAO agroecology knowledge |
| Biodiversity indicators | IMPLEMENTED | analyzer + CBD/FAO pollinator knowledge |
| Climate factors | IMPLEMENTED | analyzer + IPCC/FAO water knowledge |
| Human impact | IMPLEMENTED | pollution/deforestation/fragmentation + IPBES/UNCCD |
| RAG | IMPLEMENTED | `services/ai/retrieval.py`, chat pipeline |
| Embeddings / vector retrieval | IMPLEMENTED | pgvector + `EmbeddingProvider` |
| Scientific sources | IMPLEMENTED | FAO, IPCC, CBD, UNCCD, IPBES manifests (real orgs/URLs) |
| Demonstrable retrieval | IMPLEMENTED | `POST /api/v1/knowledge/search`, Retrieval UI |
| Text input | IMPLEMENTED | chat messages |
| Structured input | IMPLEMENTED | `MessageCreate.structured_input` |
| Clarifying questions | IMPLEMENTED | missing-info path in `ChatPipeline` |
| Conversation memory | IMPLEMENTED | `conversation_context.known_variables` |
| Context awareness | IMPLEMENTED | multi-turn merge in query analyzer |
| Actionable recommendations | IMPLEMENTED | recommendation engine + UI cards |
| Non-obvious recommendations | IMPLEMENTED | evidence+state scored interventions (not keyword if/else replies) |
| Scientific reasoning | IMPLEMENTED | `scientific_reasoning` + reasoning summary |
| Impacted metrics | IMPLEMENTED | recommendation schema |
| Time horizon | IMPLEMENTED | short\|medium\|long |
| Confidence | IMPLEMENTED | 0–1 confidence with validator adjustment |
| Evidence / reference | IMPLEMENTED | evidence items with title/org/year/URL/snippet |
| Multi-metric reasoning | IMPLEMENTED | reasoning engine (≥3 vars when available) |
| ≥3 environmental variables | IMPLEMENTED | enforced for full recommendation path |
| Geographic context | PARTIALLY IMPLEMENTED | lat/lon/region parsed & stored; no map UI |
| Tests | IMPLEMENTED | backend pytest + frontend vitest |
| Docker | IMPLEMENTED | `docker-compose.yml`, Dockerfiles |
| CI/CD | IMPLEMENTED | `.github/workflows/ci.yml` |
| README | IMPLEMENTED | `README.md` |
| Deployment documentation | IMPLEMENTED | `deploy/render.md`, `deploy/vercel.md` |

## Notes

- Auth is intentionally minimal (not core to the challenge).
- PostGIS is not enabled; optional geo is attribute-based only.
- Content in `knowledge/sources` are retrieval summaries attributed to real
  institutional publications — not fabricated peer-reviewed paper citations.
