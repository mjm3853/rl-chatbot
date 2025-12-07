"""Agent API schemas."""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel


class AgentCreate(BaseModel):
    """Schema for creating an agent."""

    name: Optional[str] = None
    agent_type: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 1.0
    system_prompt: Optional[str] = None
    config_json: Optional[dict[str, Any]] = None


class AgentRead(BaseModel):
    """Schema for reading an agent."""

    id: UUID
    name: Optional[str]
    agent_type: str
    model: str
    temperature: float
    system_prompt: Optional[str]
    config_json: Optional[dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""

    name: Optional[str] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    config_json: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
