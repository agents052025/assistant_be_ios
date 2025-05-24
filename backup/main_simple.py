from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    success: bool
    message: str
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: str = datetime.now().isoformat()

class EventRequest(BaseModel):
    title: str
    start_date: str
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    user_id: str = "anonymous"

class EventResponse(BaseModel):
    success: bool
    event_id: Optional[str] = None
    message: str

# Add ReminderRequest model after EventResponse
class ReminderRequest(BaseModel):
    title: str
    due_date: Optional[str] = None
    notes: Optional[str] = None
    user_id: str = "anonymous"

class ReminderResponse(BaseModel):
    success: bool
    reminder_id: Optional[str] = None
    message: str

# Simple in-memory storage
conversations = {}
active_connections: Dict[str, WebSocket] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CrashCurse Backend (Simple Mode)...")
    logger.info("Backend initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down CrashCurse Backend...")

# Create FastAPI app
app = FastAPI(
    title="CrashCurse AI Assistant Backend",
    description="Multi-agent AI system backend for iOS CrashCurse app (Simple Mode)",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "CrashCurse AI Assistant Backend (Simple Mode)",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents_active": 2,  # Mock data
        "websocket_connections": len(active_connections),
        "mode": "simple"
    }

# Chat endpoints
@app.post("/api/v1/chat/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI assistant system (Mock implementation)
    """
    try:
        logger.info(f"Received message from {request.user_id}: {request.message[:100]}...")
        
        # Simple mock response
        conversation_id = f"{request.user_id}_{datetime.now().timestamp()}"
        
        # Store conversation
        conversations[conversation_id] = {
            "user_id": request.user_id,
            "message": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate mock response based on keywords
        mock_response = generate_mock_response(request.message)
        
        return ChatResponse(
            success=True,
            message=mock_response,
            agent_id="mock_agent",
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50):
    """Get chat history for a user"""
    try:
        user_conversations = [
            conv for conv in conversations.values()
            if conv.get("user_id") == user_id
        ]
        
        return {
            "success": True,
            "messages": user_conversations[-limit:],
            "total_count": len(user_conversations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Planning endpoints
@app.post("/api/v1/planning/events", response_model=EventResponse)
async def create_event(request: EventRequest):
    """Create a new event (Mock implementation)"""
    try:
        logger.info(f"Creating event for {request.user_id}: {request.title}")
        
        event_id = f"event_{datetime.now().timestamp()}"
        
        return EventResponse(
            success=True,
            event_id=event_id,
            message=f"Event '{request.title}' created successfully for {request.start_date}"
        )
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/planning/reminders", response_model=ReminderResponse)
async def create_reminder(request: ReminderRequest):
    """Create a reminder (Mock implementation)"""
    try:
        logger.info(f"Creating reminder for {request.user_id}: {request.title}")
        
        reminder_id = f"reminder_{datetime.now().timestamp()}"
        
        return ReminderResponse(
            success=True,
            reminder_id=reminder_id,
            message=f"Reminder '{request.title}' created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent endpoints
@app.get("/api/v1/agents/status")
async def get_agents_status():
    """Get status of all agents (Mock implementation)"""
    return {
        "success": True,
        "agents": {
            "coordinator": {"status": "active", "health": "good"},
            "planning": {"status": "active", "health": "good"},
            "content": {"status": "simulated", "health": "mock"},
            "integration": {"status": "simulated", "health": "mock"},
            "voice": {"status": "simulated", "health": "mock"}
        }
    }

@app.get("/api/v1/agents/list")
async def list_agents():
    """List all available agents (Mock implementation)"""
    return {
        "success": True,
        "agents": [
            {
                "id": "coordinator",
                "name": "Mock Coordinator Agent",
                "description": "Simulated central orchestrator",
                "status": "active"
            },
            {
                "id": "planning", 
                "name": "Mock Planning Agent",
                "description": "Simulated scheduling and task management",
                "status": "active"
            }
        ]
    }

# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    logger.info(f"Client {client_id} connected via WebSocket")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message from {client_id}: {data}")
            
            # Echo back with mock AI response
            response = {
                "type": "message",
                "content": f"Mock AI response to: {data}",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        if client_id in active_connections:
            del active_connections[client_id]
        logger.info(f"Client {client_id} disconnected")

def generate_mock_response(message: str) -> str:
    """Generate a mock response based on message keywords"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! I'm your AI assistant. How can I help you today?"
    
    elif any(word in message_lower for word in ['plan', 'schedule', 'event', 'meeting']):
        return "I'd be happy to help you with planning! I can assist with scheduling events, organizing tasks, and optimizing your calendar. What would you like to plan?"
    
    elif any(word in message_lower for word in ['task', 'todo', 'remind']):
        return "I can help you manage your tasks and set reminders. What task would you like me to help you organize?"
    
    elif any(word in message_lower for word in ['weather', 'temperature']):
        return "I can help you check the weather! However, weather integration is coming soon. For now, I'd recommend checking your favorite weather app."
    
    elif any(word in message_lower for word in ['help', 'what can you do']):
        return "I'm your AI assistant! I can help with:\n• Planning and scheduling\n• Task management\n• Setting reminders\n• General conversation\n• More features coming soon!"
    
    else:
        return f"I understand you said: '{message}'. I'm currently in simple mode, but I'm here to help! Try asking me about planning, tasks, or reminders."

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main_simple:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    ) 