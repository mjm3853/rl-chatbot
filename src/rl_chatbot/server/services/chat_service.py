"""Chat service for handling conversations with agents."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models import Agent, Conversation, Message, ToolCall
from ..schemas.chat import ChatRequest, ChatResponse, ToolCallRead

from rl_chatbot.factory import AgentFactory
from rl_chatbot.agents.base import BaseAgent


class ChatService:
    """Service for handling chat interactions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._factory = AgentFactory()
        self._active_agents: Dict[UUID, BaseAgent] = {}

    async def _get_or_create_agent(self, agent_db: Agent) -> BaseAgent:
        """Get or create an in-memory agent instance."""
        if agent_db.id not in self._active_agents:
            agent = self._factory.create_agent(
                agent_type=agent_db.agent_type,
                model=agent_db.model,
                temperature=agent_db.temperature,
                conversation_id=str(agent_db.id),
            )
            self._active_agents[agent_db.id] = agent
        return self._active_agents[agent_db.id]

    async def _get_or_create_conversation(
        self,
        agent_id: UUID,
        conversation_id: Optional[UUID] = None,
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id:
            result = await self.session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation

        # Create new conversation
        conversation = Conversation(agent_id=agent_id)
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def _get_next_sequence_num(self, conversation_id: UUID) -> int:
        """Get the next sequence number for a conversation."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_num.desc())
            .limit(1)
        )
        last_message = result.scalar_one_or_none()
        return (last_message.sequence_num + 1) if last_message else 1

    async def _save_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        sequence_num: int,
    ) -> Message:
        """Save a message to the database."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sequence_num=sequence_num,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def _save_tool_calls(
        self,
        message_id: UUID,
        tool_calls: list[dict[str, Any]],
    ) -> list[ToolCall]:
        """Save tool calls to the database."""
        import json

        saved_tool_calls = []
        for tc in tool_calls:
            # Parse arguments if they're a string
            arguments = tc.get("arguments")
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {"raw": arguments}

            tool_call = ToolCall(
                message_id=message_id,
                tool_name=tc.get("name", "unknown"),
                arguments_json=arguments,
                result=tc.get("result"),
            )
            self.session.add(tool_call)
            saved_tool_calls.append(tool_call)

        await self.session.commit()
        for tc in saved_tool_calls:
            await self.session.refresh(tc)
        return saved_tool_calls

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat message and return response."""
        # Get agent from database
        result = await self.session.execute(select(Agent).where(Agent.id == request.agent_id))
        agent_db = result.scalar_one_or_none()
        if not agent_db:
            raise ValueError(f"Agent {request.agent_id} not found")

        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            agent_id=request.agent_id,
            conversation_id=request.conversation_id,
        )

        # Get in-memory agent
        agent = await self._get_or_create_agent(agent_db)

        # Get sequence numbers
        user_seq = await self._get_next_sequence_num(conversation.id)

        # Save user message
        await self._save_message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            sequence_num=user_seq,
        )

        # Get response from agent
        response_text = agent.chat(request.message)

        # Get tool calls from agent
        agent_tool_calls = agent.get_last_tool_calls()

        # Save assistant message
        assistant_seq = user_seq + 1
        assistant_message = await self._save_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            sequence_num=assistant_seq,
        )

        # Save tool calls if any
        tool_calls_read = []
        if agent_tool_calls:
            saved_tool_calls = await self._save_tool_calls(
                message_id=assistant_message.id,
                tool_calls=agent_tool_calls,
            )
            tool_calls_read = [
                ToolCallRead(
                    id=tc.id,
                    tool_name=tc.tool_name,
                    arguments_json=tc.arguments_json,
                    result=tc.result,
                    duration_ms=tc.duration_ms,
                    created_at=tc.created_at,
                )
                for tc in saved_tool_calls
            ]

        return ChatResponse(
            conversation_id=conversation.id,
            agent_id=request.agent_id,
            message_id=assistant_message.id,
            response=response_text,
            tool_calls=tool_calls_read,
            sequence_num=assistant_seq,
        )

    async def reset_agent(self, agent_id: UUID) -> bool:
        """Reset an agent's in-memory state."""
        if agent_id in self._active_agents:
            self._active_agents[agent_id].reset(clear_conversation_id=False)
            return True
        return False


# Global chat service singleton for agent state management
_chat_services: Dict[str, ChatService] = {}


def get_chat_service(session: AsyncSession) -> ChatService:
    """Get or create a chat service for the session."""
    # For simplicity, create a new service per request
    # In production, you'd want to manage agent instances more carefully
    return ChatService(session)
