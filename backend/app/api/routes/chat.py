from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.conversation import Conversation, ConversationContext
from app.schemas.chat import (
    ChatTurnResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    MessageCreate,
    MessageResponse,
)
from app.services.conversation.service import ChatPipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationSummary)
def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
) -> Conversation:
    conv = Conversation(title=body.title)
    db.add(conv)
    db.flush()
    ctx = ConversationContext(
        conversation_id=conv.id,
        known_variables={},
        missing_variables=[],
        environmental_state={},
        assumptions=[],
    )
    db.add(ctx)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(db: Session = Depends(get_db)) -> list[Conversation]:
    stmt = select(Conversation).order_by(Conversation.updated_at.desc()).limit(100)
    return list(db.scalars(stmt).all())


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
) -> ConversationDetail:
    conv = db.scalar(
        select(Conversation)
        .options(
            joinedload(Conversation.messages),
            joinedload(Conversation.context),
        )
        .where(Conversation.id == conversation_id)
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    context = None
    if conv.context:
        context = {
            "known_variables": conv.context.known_variables,
            "missing_variables": conv.context.missing_variables,
            "environmental_state": conv.context.environmental_state,
            "assumptions": conv.context.assumptions,
        }
    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageResponse.model_validate(m) for m in conv.messages],
        context=context,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatTurnResponse,
)
async def post_message(
    conversation_id: UUID,
    body: MessageCreate,
    db: Session = Depends(get_db),
) -> ChatTurnResponse:
    conv = db.scalar(
        select(Conversation)
        .options(joinedload(Conversation.context))
        .where(Conversation.id == conversation_id)
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    pipeline = ChatPipeline(db)
    payload = await pipeline.handle_message(
        conv, body.content, structured_input=body.structured_input
    )

    # Reload last assistant message
    db.refresh(conv)
    assistant = next(
        (m for m in reversed(conv.messages) if m.role == "assistant"),
        None,
    )
    if not assistant:
        raise HTTPException(
            status_code=500, detail="Failed to persist assistant message"
        )

    return ChatTurnResponse(
        conversation_id=conv.id,
        message=MessageResponse.model_validate(assistant),
        response=payload,
    )
