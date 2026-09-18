"""Integration tests requiring PostgreSQL + pgvector. Skip if unavailable."""

import os

import pytest
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://darukaa:darukaa@localhost:5433/darukaa_ai",
)


def _db_available() -> bool:
    try:
        eng = create_engine(DATABASE_URL)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
            row = conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            ).fetchone()
            return row is not None
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _db_available(), reason="PostgreSQL + pgvector not available"
)


@pytest.mark.asyncio
async def test_ingest_and_retrieve():
    from app.core.database import SessionLocal
    from app.services.ai.retrieval import RetrievalService
    from app.services.knowledge.ingestion import KnowledgeIngestionService

    db = SessionLocal()
    try:
        ingestion = KnowledgeIngestionService(db)
        result = await ingestion.ingest_document(
            source_title="Test FAO Soil Note",
            document_title="Test document",
            content=(
                "Soil organic carbon supports soil ecological function and biodiversity. "
                "Low rainfall creates water stress. Monoculture reduces habitat diversity. "
                "Cover crops and diversification are discussed in institutional guidance."
            ),
            organization="FAO",
            publication_year=2017,
            source_type="institutional_report",
            url="https://www.fao.org/",
            topic="soil_health",
        )
        assert result["chunks_created"] >= 1

        retrieval = RetrievalService(db)
        hits = await retrieval.search(
            "soil organic carbon biodiversity low rainfall monoculture",
            top_k=5,
            min_similarity=0.0,
        )
        assert len(hits) >= 1
        assert "source" in hits[0]
        assert hits[0]["source"]["title"]
        assert "similarity" in hits[0]
    finally:
        db.close()


@pytest.mark.asyncio
async def test_chat_pipeline_end_to_end():
    from app.core.database import SessionLocal
    from app.models.conversation import Conversation, ConversationContext
    from app.services.conversation.service import ChatPipeline

    db = SessionLocal()
    try:
        conv = Conversation(title="eval")
        db.add(conv)
        db.flush()
        db.add(
            ConversationContext(
                conversation_id=conv.id,
                known_variables={},
                missing_variables=[],
                environmental_state={},
                assumptions=[],
            )
        )
        db.commit()
        db.refresh(conv)

        pipeline = ChatPipeline(db)

        # Clarification path
        r1 = await pipeline.handle_message(
            conv, "Biodiversity is declining on my land."
        )
        assert r1["needs_clarification"] is True
        assert r1["missing_information"]

        # Multi-turn memory
        r2 = await pipeline.handle_message(
            conv,
            "Organic carbon is 0.3%, rainfall is low, and I grow wheat continuously "
            "in a semi-arid region with low habitat diversity.",
        )
        assert r2["needs_clarification"] is False
        assert len(r2["environmental_assessment"]["variables_considered"]) >= 3
        assert r2["recommendations"]
        for rec in r2["recommendations"]:
            assert rec["evidence"]
    finally:
        db.close()
