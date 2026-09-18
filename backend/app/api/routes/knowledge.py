from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge import KnowledgeSource
from app.schemas.knowledge import (
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceOut,
    RetrievedChunk,
)
from app.services.ai.retrieval import RetrievalService
from app.services.knowledge.ingestion import KnowledgeIngestionService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    body: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
) -> KnowledgeSearchResponse:
    service = RetrievalService(db)
    results = await service.search(
        body.query,
        top_k=body.top_k,
        topic=body.topic,
        min_similarity=body.min_similarity,
    )
    retrieved = [
        RetrievedChunk(
            chunk_id=r["chunk_id"],
            content=r["content"],
            similarity=r["similarity"],
            topic=r.get("topic"),
            metadata=r.get("metadata") or {},
            source=r.get("source") or {},
        )
        for r in results
    ]
    return KnowledgeSearchResponse(
        query=body.query, results=retrieved, count=len(retrieved)
    )


@router.post("/ingest", response_model=KnowledgeIngestResponse)
async def ingest_knowledge(
    body: KnowledgeIngestRequest,
    db: Session = Depends(get_db),
) -> KnowledgeIngestResponse:
    service = KnowledgeIngestionService(db)
    try:
        result = await service.ingest_document(
            source_title=body.source_title,
            document_title=body.document_title,
            content=body.content,
            organization=body.organization,
            authors=body.authors,
            publication_year=body.publication_year,
            source_type=body.source_type,
            url=body.url,
            topic=body.topic,
            geographic_scope=body.geographic_scope,
            metadata=body.metadata,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KnowledgeIngestResponse(**result)


@router.get("/sources", response_model=List[KnowledgeSourceOut])
def list_sources(db: Session = Depends(get_db)) -> list[KnowledgeSource]:
    stmt = (
        select(KnowledgeSource).order_by(KnowledgeSource.created_at.desc()).limit(200)
    )
    return list(db.scalars(stmt).all())
