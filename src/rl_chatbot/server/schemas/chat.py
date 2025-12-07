"""Chat API schemas."""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel


class ToolCallRead(BaseModel):
    """Schema for reading a tool call."""

    id: UUID
    tool_name: str
    arguments_json: Optional[dict[str, Any]]
    result: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """Schema for a chat request."""

    agent_id: UUID
    message: str
    conversation_id: Optional[UUID] = None  # If None, creates new conversation


class ChatResponse(BaseModel):
    """Schema for a chat response."""

    conversation_id: UUID
    agent_id: UUID
    message_id: UUID
    response: str
    tool_calls: List[ToolCallRead] = []
    sequence_num: int


class MessageRead(BaseModel):
    """Schema for reading a message."""

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    sequence_num: int
    created_at: datetime
    tool_calls: List[ToolCallRead] = []

    model_config = {"from_attributes": True}


class ConversationRead(BaseModel):
    """Schema for reading a conversation."""

    id: UUID
    agent_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    metadata_json: Optional[dict[str, Any]]
    messages: List[MessageRead] = []

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    """Schema for conversation list item (without messages)."""

    id: UUID
    agent_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    message_count: int = 0

    model_config = {"from_attributes": True}
