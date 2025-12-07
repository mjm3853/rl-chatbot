"""WebSocket connection manager."""

from typing import Dict, List, Set
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        # Map of agent_id to set of connected WebSockets
        self._agent_connections: Dict[UUID, Set[WebSocket]] = {}
        # Map of run_id to set of connected WebSockets (for progress updates)
        self._progress_connections: Dict[UUID, Set[WebSocket]] = {}

    async def connect_agent(self, websocket: WebSocket, agent_id: UUID):
        """Connect a WebSocket for agent chat."""
        await websocket.accept()
        if agent_id not in self._agent_connections:
            self._agent_connections[agent_id] = set()
        self._agent_connections[agent_id].add(websocket)

    def disconnect_agent(self, websocket: WebSocket, agent_id: UUID):
        """Disconnect a WebSocket from agent chat."""
        if agent_id in self._agent_connections:
            self._agent_connections[agent_id].discard(websocket)
            if not self._agent_connections[agent_id]:
                del self._agent_connections[agent_id]

    async def connect_progress(self, websocket: WebSocket, run_id: UUID):
        """Connect a WebSocket for progress updates."""
        await websocket.accept()
        if run_id not in self._progress_connections:
            self._progress_connections[run_id] = set()
        self._progress_connections[run_id].add(websocket)

    def disconnect_progress(self, websocket: WebSocket, run_id: UUID):
        """Disconnect a WebSocket from progress updates."""
        if run_id in self._progress_connections:
            self._progress_connections[run_id].discard(websocket)
            if not self._progress_connections[run_id]:
                del self._progress_connections[run_id]

    async def send_to_agent(self, agent_id: UUID, message: dict):
        """Send a message to all connections for an agent."""
        if agent_id in self._agent_connections:
            disconnected = []
            for connection in self._agent_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            # Clean up disconnected connections
            for conn in disconnected:
                self._agent_connections[agent_id].discard(conn)

    async def send_progress(self, run_id: UUID, message: dict):
        """Send a progress update to all connections for a run."""
        if run_id in self._progress_connections:
            disconnected = []
            for connection in self._progress_connections[run_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            # Clean up disconnected connections
            for conn in disconnected:
                self._progress_connections[run_id].discard(conn)

    def get_agent_connection_count(self, agent_id: UUID) -> int:
        """Get number of connections for an agent."""
        return len(self._agent_connections.get(agent_id, set()))

    def get_progress_connection_count(self, run_id: UUID) -> int:
        """Get number of connections for a run."""
        return len(self._progress_connections.get(run_id, set()))


# Global connection manager singleton
manager = ConnectionManager()
