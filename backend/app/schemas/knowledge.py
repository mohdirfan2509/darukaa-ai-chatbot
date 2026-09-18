"""Knowledge search and ingestion schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    topic: Optional[str] = None
    min_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class RetrievedChunk(BaseModel):
    chunk_id: UUID
    content: str
    similarity: float
    topic: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: dict[str, Any]


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]
    count: int


class KnowledgeSourceOut(BaseModel):
    id: UUID
    title: str
    organization: Optional[str] = None
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    source_type: str
    url: Optional[str] = None
    topic: Optional[str] = None
    geographic_scope: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeIngestRequest(BaseModel):
    """Ingest a single document with source metadata."""

    source_title: str
    organization: Optional[str] = None
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    source_type: str = "institutional_report"
    url: Optional[str] = None
    topic: Optional[str] = None
    geographic_scope: Optional[str] = None
    document_title: str
    content: str = Field(..., min_length=20)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeIngestResponse(BaseModel):
    source_id: UUID
    document_id: UUID
    chunks_created: int
