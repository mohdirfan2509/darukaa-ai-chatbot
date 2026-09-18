"""Chat and conversation schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationSummary(BaseModel):
    id: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)
    structured_input: Optional[dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    structured_payload: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []
    context: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ChatTurnResponse(BaseModel):
    conversation_id: UUID
    message: MessageResponse
    response: dict[str, Any]
