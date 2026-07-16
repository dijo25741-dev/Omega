import logging
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("omega.websocket")

class ConnectionManager:
    """
    Manages active WebSocket connections for real-time telemetry broadcasts.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts and stores a new client WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Removes a client WebSocket connection from active pool."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Sends a JSON payload to all connected clients."""
        if not self.active_connections:
            return
            
        disconnected_clients = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client. Adding to disconnect list: {e}")
                disconnected_clients.append(connection)
                
        # Clean up any broken connections discovered during broadcast
        for client in disconnected_clients:
            self.disconnect(client)

# Global singleton connection manager
manager = ConnectionManager()
