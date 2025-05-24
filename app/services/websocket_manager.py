from fastapi import WebSocket
from typing import Dict, List
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manager for WebSocket connections and real-time communication
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_info[client_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0
        }
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_info:
            del self.connection_info[client_id]
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                
                # Format message
                response = {
                    "type": "message",
                    "content": message,
                    "timestamp": datetime.now().isoformat(),
                    "client_id": client_id
                }
                
                await websocket.send_text(json.dumps(response))
                
                # Update connection info
                if client_id in self.connection_info:
                    self.connection_info[client_id]["last_activity"] = datetime.now()
                    self.connection_info[client_id]["message_count"] += 1
                
                logger.debug(f"Message sent to client {client_id}")
                
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                # Remove invalid connection
                self.disconnect(client_id)
    
    async def broadcast_message(self, message: str):
        """Send a message to all connected clients"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                response = {
                    "type": "broadcast",
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(response))
                
                # Update connection info
                if client_id in self.connection_info:
                    self.connection_info[client_id]["last_activity"] = datetime.now()
                    self.connection_info[client_id]["message_count"] += 1
                
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        logger.info(f"Broadcast message sent to {len(self.active_connections)} clients")
    
    async def send_typing_indicator(self, client_id: str, is_typing: bool = True):
        """Send typing indicator to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                
                response = {
                    "type": "typing_indicator",
                    "is_typing": is_typing,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                logger.error(f"Error sending typing indicator to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def send_agent_status(self, client_id: str, agent_name: str, status: str):
        """Send agent status update to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                
                response = {
                    "type": "agent_status",
                    "agent_name": agent_name,
                    "status": status,  # "thinking", "processing", "completed", "error"
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                logger.error(f"Error sending agent status to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def send_error(self, client_id: str, error_message: str, error_code: str = None):
        """Send error message to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                
                response = {
                    "type": "error",
                    "message": error_message,
                    "code": error_code,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                logger.error(f"Error sending error to {client_id}: {e}")
                self.disconnect(client_id)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_client_info(self, client_id: str) -> Dict:
        """Get information about a specific client"""
        return self.connection_info.get(client_id, {})
    
    def get_all_clients(self) -> List[str]:
        """Get list of all connected client IDs"""
        return list(self.active_connections.keys())
    
    def is_client_connected(self, client_id: str) -> bool:
        """Check if a specific client is connected"""
        return client_id in self.active_connections
    
    async def send_system_notification(self, message: str, notification_type: str = "info"):
        """Send system notification to all connected clients"""
        response = {
            "type": "system_notification",
            "notification_type": notification_type,  # "info", "warning", "error"
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_message(json.dumps(response))
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        total_messages = sum(
            info.get("message_count", 0) 
            for info in self.connection_info.values()
        )
        
        return {
            "total_connections": len(self.active_connections),
            "total_messages_sent": total_messages,
            "connections_info": self.connection_info
        } 