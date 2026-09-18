"""Recommendation and structured AI response schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source_title: str
    organization: Optional[str] = None
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    relevant_snippet: str
    similarity: Optional[float] = None


class Recommendation(BaseModel):
    title: str
    action: str
    scientific_reasoning: str
    impacted_metrics: list[str] = Field(default_factory=list)
    expected_direction: str
    estimated_effect: Optional[str] = None
    time_horizon: str = Field(description="short|medium|long")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class EnvironmentalAssessment(BaseModel):
    summary: str
    variables_considered: list[str] = Field(default_factory=list)


class RetrievalMeta(BaseModel):
    sources_used: int = 0
    chunks_used: int = 0


class StructuredAIResponse(BaseModel):
    answer: str
    environmental_assessment: EnvironmentalAssessment
    reasoning_summary: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    retrieval: RetrievalMeta = Field(default_factory=RetrievalMeta)
    environmental_context: dict[str, Any] = Field(default_factory=dict)
    needs_clarification: bool = False
    clarification_questions: list[str] = Field(default_factory=list)
