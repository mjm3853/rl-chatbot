"""Agent database models."""

from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .conversation import Conversation
    from .evaluation import EvaluationRun
    from .training import TrainingRun


class AgentBase(SQLModel):
    """Base agent model with common fields."""

    name: Optional[str] = Field(default=None, max_length=255)
    agent_type: str = Field(default="openai", max_length=50)
    model: str = Field(default="gpt-4o", max_length=100)
    temperature: float = Field(default=1.0)
    system_prompt: Optional[str] = Field(default=None)
    config_json: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    is_active: bool = Field(default=True)


class Agent(AgentBase, table=True):
    """Database model for agents."""

    __tablename__ = "agents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    conversations: List["Conversation"] = Relationship(back_populates="agent")
    evaluation_runs: List["EvaluationRun"] = Relationship(back_populates="agent")
    training_runs: List["TrainingRun"] = Relationship(back_populates="agent")


class AgentCreate(AgentBase):
    """Schema for creating an agent."""

    pass


class AgentRead(AgentBase):
    """Schema for reading an agent."""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]


class AgentUpdate(SQLModel):
    """Schema for updating an agent."""

    name: Optional[str] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    config_json: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
