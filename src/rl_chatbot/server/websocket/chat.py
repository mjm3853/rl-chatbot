"""WebSocket chat handler."""

import json
from typing import Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.chat import ChatRequest
from ..services.chat_service import ChatService
from .manager import manager


class ChatWebSocketHandler:
    """Handles WebSocket chat connections."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.service = ChatService(session)

    async def handle(
        self,
        websocket: WebSocket,
        agent_id: UUID,
        conversation_id: Optional[UUID] = None,
    ):
        """Handle a WebSocket chat session."""
        await manager.connect_agent(websocket, agent_id)
        current_conversation_id = conversation_id

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()

                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    message_data = {"message": data}

                # Extract message content
                message_content = message_data.get("message", data)

                # Send acknowledgment
                await websocket.send_json({
                    "type": "ack",
                    "status": "processing",
                })

                try:
                    # Process chat request
                    request = ChatRequest(
                        agent_id=agent_id,
                        message=message_content,
                        conversation_id=current_conversation_id,
                    )

                    response = await self.service.chat(request)

                    # Update conversation ID for subsequent messages
                    current_conversation_id = response.conversation_id

                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "conversation_id": str(response.conversation_id),
                        "message_id": str(response.message_id),
                        "response": response.response,
                        "tool_calls": [
                            {
                                "id": str(tc.id),
                                "tool_name": tc.tool_name,
                                "arguments": tc.arguments_json,
                                "result": tc.result,
                            }
                            for tc in response.tool_calls
                        ],
                        "sequence_num": response.sequence_num,
                    })

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                    })

        except WebSocketDisconnect:
            manager.disconnect_agent(websocket, agent_id)
        except Exception as e:
            manager.disconnect_agent(websocket, agent_id)
            raise
