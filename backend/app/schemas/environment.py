"""Environmental observation and analysis schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ObservationCreate(BaseModel):
    metric: str = Field(..., min_length=1, max_length=128)
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    source: str = "user"
    quality: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    region: Optional[str] = None
    conversation_id: Optional[UUID] = None
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObservationOut(BaseModel):
    id: UUID
    metric: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    timestamp: datetime
    source: str
    quality: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None

    model_config = {"from_attributes": True}


class EnvironmentAnalyzeRequest(BaseModel):
    text: Optional[str] = None
    variables: dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[UUID] = None


class EnvironmentAnalyzeResponse(BaseModel):
    environmental_state: dict[str, Any]
    known_variables: dict[str, Any]
    missing_variables: list[str]
    critical_variables: list[str]
    optional_variables: list[str]
    relationships: list[str]
    assessment_summary: str
