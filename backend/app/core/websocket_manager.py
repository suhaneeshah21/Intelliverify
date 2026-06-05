# backend/app/core/websocket_manager.py

from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Holds all active WebSocket connections from admin clients.
    Provides connect / disconnect / broadcast interface.
    Thread safety note: FastAPI runs async, all operations here are
    single-threaded within the event loop — no locks needed.
    """

    def __init__(self):
        # List of currently connected WebSocket objects
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept the WebSocket handshake and register the connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove the connection from the registry (client closed tab / lost network)."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Send a JSON message to every connected admin.
        If a send fails (client already gone), silently remove that connection.
        """
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send to a WebSocket client, marking dead: {e}")
                dead_connections.append(connection)

        # Clean up dead connections after the loop (never mutate while iterating)
        for dead in dead_connections:
            self.disconnect(dead)


# Single shared instance — imported everywhere that needs to broadcast
manager = WebSocketManager()