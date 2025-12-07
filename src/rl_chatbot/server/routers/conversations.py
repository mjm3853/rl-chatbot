"""Conversation endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, func

from ..database import get_session
from ..models import Conversation, Message, ToolCall
from ..schemas.chat import ConversationRead, ConversationListItem, MessageRead, ToolCallRead

router = APIRouter()


@router.get("/", response_model=List[ConversationListItem])
async def list_conversations(
    agent_id: Optional[UUID] = Query(None, description="Filter by agent ID"),
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """List all conversations with message counts."""
    # Build query
    query = select(Conversation)
    if agent_id:
        query = query.where(Conversation.agent_id == agent_id)
    query = query.offset(skip).limit(limit).order_by(Conversation.started_at.desc())

    result = await session.execute(query)
    conversations = result.scalars().all()

    # Get message counts
    items = []
    for conv in conversations:
        count_result = await session.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv.id)
        )
        message_count = count_result.scalar() or 0

        items.append(
            ConversationListItem(
                id=conv.id,
                agent_id=conv.agent_id,
                started_at=conv.started_at,
                ended_at=conv.ended_at,
                message_count=message_count,
            )
        )

    return items


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a conversation with all its messages and tool calls."""
    # Get conversation with messages eagerly loaded
    result = await session.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages).selectinload(Message.tool_calls))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Build response with messages and tool calls
    messages_read = []
    for msg in sorted(conversation.messages, key=lambda m: m.sequence_num):
        tool_calls_read = [
            ToolCallRead(
                id=tc.id,
                tool_name=tc.tool_name,
                arguments_json=tc.arguments_json,
                result=tc.result,
                duration_ms=tc.duration_ms,
                created_at=tc.created_at,
            )
            for tc in msg.tool_calls
        ]
        messages_read.append(
            MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                sequence_num=msg.sequence_num,
                created_at=msg.created_at,
                tool_calls=tool_calls_read,
            )
        )

    return ConversationRead(
        id=conversation.id,
        agent_id=conversation.agent_id,
        started_at=conversation.started_at,
        ended_at=conversation.ended_at,
        metadata_json=conversation.metadata_json,
        messages=messages_read,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a conversation and all its messages."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete associated messages and tool calls (cascade)
    await session.delete(conversation)
    await session.commit()
    return None


@router.post("/{conversation_id}/end")
async def end_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Mark a conversation as ended."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.ended_at = datetime.utcnow()
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    return {"status": "ended", "conversation_id": str(conversation.id)}
