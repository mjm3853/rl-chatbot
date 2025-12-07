"""Agent service for managing agent lifecycle."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models import Agent, AgentCreate, AgentUpdate


class AgentService:
    """Service for managing agents in the database."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, agent_data: AgentCreate) -> Agent:
        """Create a new agent."""
        agent = Agent(**agent_data.model_dump())
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def get(self, agent_id: UUID) -> Optional[Agent]:
        """Get an agent by ID."""
        result = await self.session.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Agent]:
        """List all agents with pagination."""
        query = select(Agent)
        if active_only:
            query = query.where(Agent.is_active == True)
        query = query.offset(skip).limit(limit).order_by(Agent.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, agent_id: UUID, agent_data: AgentUpdate) -> Optional[Agent]:
        """Update an agent."""
        agent = await self.get(agent_id)
        if not agent:
            return None

        update_data = agent_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(agent, key, value)

        agent.updated_at = datetime.utcnow()
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def delete(self, agent_id: UUID) -> bool:
        """Soft delete an agent."""
        agent = await self.get(agent_id)
        if not agent:
            return False

        agent.is_active = False
        agent.updated_at = datetime.utcnow()
        self.session.add(agent)
        await self.session.commit()
        return True

    async def hard_delete(self, agent_id: UUID) -> bool:
        """Permanently delete an agent."""
        agent = await self.get(agent_id)
        if not agent:
            return False

        await self.session.delete(agent)
        await self.session.commit()
        return True
