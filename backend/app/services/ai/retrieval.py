"""pgvector retrieval service with metadata filtering and ranking."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.services.ai.embedding_provider import EmbeddingProvider, get_embedding_provider

logger = get_logger("retrieval")


class RetrievalService:
    def __init__(
        self,
        db: Session,
        embedder: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.db = db
        self.embedder = embedder or get_embedding_provider()
        self.settings = get_settings()

    async def search(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        topic: Optional[str] = None,
        min_similarity: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        top_k = top_k or self.settings.retrieval_top_k
        min_sim = (
            min_similarity
            if min_similarity is not None
            else self.settings.retrieval_min_similarity
        )

        query_embedding = await self.embedder.embed_one(query)
        embedding_literal = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"

        # Cosine distance via pgvector: 1 - cosine_distance = similarity
        # Using <=> operator (cosine distance)
        # Build SQL with optional topic filter to avoid NULL param type issues
        if topic:
            sql = text(
                """
                SELECT
                    kc.id AS chunk_id,
                    kc.content,
                    kc.chunk_index,
                    kc.metadata AS chunk_metadata,
                    kd.id AS document_id,
                    kd.title AS document_title,
                    ks.id AS source_id,
                    ks.title AS source_title,
                    ks.organization,
                    ks.authors,
                    ks.publication_year,
                    ks.source_type,
                    ks.url,
                    ks.topic,
                    ks.geographic_scope,
                    1 - (kc.embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM knowledge_chunks kc
                JOIN knowledge_documents kd ON kd.id = kc.document_id
                JOIN knowledge_sources ks ON ks.id = kd.source_id
                WHERE kc.embedding IS NOT NULL
                  AND (
                    ks.topic ILIKE :topic_pattern
                    OR COALESCE(kc.metadata->>'topics', '') ILIKE :topic_pattern
                  )
                ORDER BY kc.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            )
            params = {
                "embedding": embedding_literal,
                "topic_pattern": f"%{topic}%",
                "limit": top_k * 2,
            }
        else:
            sql = text(
                """
                SELECT
                    kc.id AS chunk_id,
                    kc.content,
                    kc.chunk_index,
                    kc.metadata AS chunk_metadata,
                    kd.id AS document_id,
                    kd.title AS document_title,
                    ks.id AS source_id,
                    ks.title AS source_title,
                    ks.organization,
                    ks.authors,
                    ks.publication_year,
                    ks.source_type,
                    ks.url,
                    ks.topic,
                    ks.geographic_scope,
                    1 - (kc.embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM knowledge_chunks kc
                JOIN knowledge_documents kd ON kd.id = kc.document_id
                JOIN knowledge_sources ks ON ks.id = kd.source_id
                WHERE kc.embedding IS NOT NULL
                ORDER BY kc.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            )
            params = {
                "embedding": embedding_literal,
                "limit": top_k * 2,
            }

        rows = self.db.execute(sql, params).mappings().all()

        results: list[dict[str, Any]] = []
        for row in rows:
            sim = float(row["similarity"] or 0.0)
            if sim < min_sim:
                continue
            results.append(
                {
                    "chunk_id": row["chunk_id"],
                    "content": row["content"],
                    "similarity": round(sim, 4),
                    "topic": row["topic"],
                    "metadata": row["chunk_metadata"] or {},
                    "source": {
                        "id": str(row["source_id"]),
                        "title": row["source_title"],
                        "organization": row["organization"],
                        "authors": row["authors"],
                        "publication_year": row["publication_year"],
                        "source_type": row["source_type"],
                        "url": row["url"],
                        "topic": row["topic"],
                        "geographic_scope": row["geographic_scope"],
                        "document_title": row["document_title"],
                    },
                }
            )
            if len(results) >= top_k:
                break

        # Fallback: if no embeddings match (empty DB or SQL fails), try ORM lexical
        if not results:
            results = await self._lexical_fallback(query, top_k=top_k, topic=topic)

        logger.info(
            "retrieval_complete",
            query=query[:120],
            count=len(results),
            source_ids=[r["source"]["id"] for r in results],
        )
        return results

    async def _lexical_fallback(
        self,
        query: str,
        *,
        top_k: int,
        topic: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Keyword overlap fallback when vector search returns nothing."""
        tokens = {t.lower() for t in query.replace("-", " ").split() if len(t) > 2}
        stmt = (
            select(KnowledgeChunk)
            .options(
                joinedload(KnowledgeChunk.document).joinedload(KnowledgeDocument.source)
            )
            .limit(200)
        )
        chunks = self.db.scalars(stmt).unique().all()
        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk in chunks:
            content_tokens = set(chunk.content.lower().replace("-", " ").split())
            if not tokens:
                continue
            overlap = len(tokens & content_tokens) / len(tokens)
            src = chunk.document.source
            if topic and src.topic and topic.lower() not in (src.topic or "").lower():
                overlap *= 0.5
            if overlap > 0:
                scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, chunk in scored[:top_k]:
            src = chunk.document.source
            results.append(
                {
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "similarity": round(float(sim), 4),
                    "topic": src.topic,
                    "metadata": chunk.metadata_ or {},
                    "source": {
                        "id": str(src.id),
                        "title": src.title,
                        "organization": src.organization,
                        "authors": src.authors,
                        "publication_year": src.publication_year,
                        "source_type": src.source_type,
                        "url": src.url,
                        "topic": src.topic,
                        "geographic_scope": src.geographic_scope,
                        "document_title": chunk.document.title,
                    },
                }
            )
        return results

    def build_retrieval_query(self, analysis: dict[str, Any]) -> str:
        """Generate a retrieval-focused query from analyzed variables."""
        parts: list[str] = []
        known = analysis.get("known_variables", {})
        problem = analysis.get("problem")
        if problem:
            parts.append(problem.replace("_", " "))
        mapping = {
            "soil_organic_carbon": "soil organic carbon biodiversity soil function",
            "rainfall": "rainfall water availability ecological recovery",
            "land_use": "land use monoculture habitat diversity agroforestry",
            "habitat_diversity": "habitat diversity species richness",
            "species_richness": "species richness biodiversity indicators",
            "pollution": "pollution biodiversity decline habitat quality",
            "deforestation": "deforestation habitat fragmentation ecological connectivity",
            "habitat_fragmentation": "habitat fragmentation connectivity corridors",
            "temperature": "temperature stress water soil biodiversity",
            "soil_moisture": "soil moisture drought water stress",
            "crop": "cropping systems diversification cover crops",
        }
        for key, phrase in mapping.items():
            if key in known:
                parts.append(phrase)
                val = known[key]
                parts.append(f"{key.replace('_', ' ')} {val}")
        if not parts:
            parts.append(
                "soil health biodiversity land use climate environmental management"
            )
        return " ".join(parts)
