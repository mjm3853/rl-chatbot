"""Agent CRUD endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.agent import AgentCreate, AgentRead, AgentUpdate
from ..services.agent_service import AgentService

router = APIRouter()


async def get_agent_service(session: AsyncSession = Depends(get_session)) -> AgentService:
    """Dependency to get agent service."""
    return AgentService(session)


@router.post("/", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    service: AgentService = Depends(get_agent_service),
):
    """Create a new agent."""
    agent = await service.create(agent_data)
    return agent


@router.get("/", response_model=List[AgentRead])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    service: AgentService = Depends(get_agent_service),
):
    """List all agents."""
    agents = await service.list(skip=skip, limit=limit, active_only=active_only)
    return agents


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
):
    """Get an agent by ID."""
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    service: AgentService = Depends(get_agent_service),
):
    """Update an agent."""
    agent = await service.update(agent_id, agent_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
):
    """Delete an agent (soft delete)."""
    success = await service.delete(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None


@router.post("/{agent_id}/reset", response_model=AgentRead)
async def reset_agent(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
):
    """Reset an agent's state (clears conversations)."""
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # For now, just return the agent. Full reset will involve
    # clearing conversations when chat functionality is added.
    return agent
