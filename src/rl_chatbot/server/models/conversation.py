"""Conversation, Message, and ToolCall database models."""

from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .agent import Agent


class ToolCallBase(SQLModel):
    """Base tool call model."""

    tool_name: str = Field(max_length=100)
    arguments_json: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    result: Optional[str] = None
    duration_ms: Optional[int] = None


class ToolCall(ToolCallBase, table=True):
    """Database model for tool calls."""

    __tablename__ = "tool_calls"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    message_id: UUID = Field(foreign_key="messages.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    message: "Message" = Relationship(back_populates="tool_calls")


class MessageBase(SQLModel):
    """Base message model."""

    role: str = Field(max_length=20)  # user, assistant, system
    content: str
    sequence_num: int


class Message(MessageBase, table=True):
    """Database model for messages."""

    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    conversation: "Conversation" = Relationship(back_populates="messages")
    tool_calls: List[ToolCall] = Relationship(back_populates="message")


class ConversationBase(SQLModel):
    """Base conversation model."""

    metadata_json: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class Conversation(ConversationBase, table=True):
    """Database model for conversations."""

    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(foreign_key="agents.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    # Relationships
    agent: "Agent" = Relationship(back_populates="conversations")
    messages: List[Message] = Relationship(back_populates="conversation")


class MessageRead(MessageBase):
    """Schema for reading a message."""

    id: UUID
    conversation_id: UUID
    created_at: datetime
    tool_calls: List[ToolCallBase] = []


class ConversationRead(ConversationBase):
    """Schema for reading a conversation."""

    id: UUID
    agent_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    messages: List[MessageRead] = []
