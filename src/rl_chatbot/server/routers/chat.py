"""Chat endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session, async_session
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.chat_service import ChatService, get_chat_service
from ..websocket.chat import ChatWebSocketHandler

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    """Send a message to an agent and get a response."""
    service = get_chat_service(session)
    try:
        response = await service.chat(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.websocket("/ws/{agent_id}")
async def websocket_chat(
    websocket: WebSocket,
    agent_id: UUID,
    conversation_id: Optional[UUID] = Query(None),
):
    """WebSocket endpoint for real-time chat with an agent.

    Connect to ws://host/api/v1/chat/ws/{agent_id}?conversation_id={optional}

    Send messages as JSON: {"message": "your message"}
    Or just send plain text.

    Receive responses as JSON:
    - {"type": "ack", "status": "processing"} - Message received
    - {"type": "response", "conversation_id": "...", "response": "...", ...} - Agent response
    - {"type": "error", "error": "..."} - Error occurred
    """
    async with async_session() as session:
        handler = ChatWebSocketHandler(session)
        await handler.handle(websocket, agent_id, conversation_id)
