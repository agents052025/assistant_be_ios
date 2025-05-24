from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

# Import our CrewAI agents
from app.agents.coordinator_agent import CoordinatorService
from app.agents.planning_agent import PlanningService
from app.agents.content_agent import ContentService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    success: bool
    message: str
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: str = datetime.now().isoformat()
    metadata: Optional[Dict[str, Any]] = None

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
    details: Optional[Dict[str, Any]] = None

class ReminderRequest(BaseModel):
    title: str
    due_date: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = "normal"
    user_id: str = "anonymous"

class ReminderResponse(BaseModel):
    success: bool
    reminder_id: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None

class ContentRequest(BaseModel):
    type: str  # "email", "text", "brainstorm"
    prompt: str
    tone: Optional[str] = "professional"
    length: Optional[str] = "medium"
    context: Optional[Dict[str, Any]] = None
    user_id: str = "anonymous"

class ContentResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    content_type: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

# Global services
coordinator_service: CoordinatorService = None
planning_service: PlanningService = None
content_service: ContentService = None

# Storage
conversations = {}
active_connections: Dict[str, WebSocket] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global coordinator_service, planning_service, content_service
    
    logger.info("🚀 Starting CrashCurse CrewAI Backend...")
    
    try:
        # Initialize CrewAI services
        logger.info("Initializing CrewAI agents...")
        coordinator_service = CoordinatorService()
        planning_service = PlanningService()
        content_service = ContentService()
        
        logger.info("✅ All CrewAI agents initialized successfully")
        logger.info("🎯 Backend ready for multi-agent AI assistance!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize CrewAI agents: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down CrashCurse CrewAI Backend...")

# Create FastAPI app
app = FastAPI(
    title="CrashCurse AI Assistant Backend - CrewAI Edition",
    description="Multi-agent CrewAI system backend for iOS CrashCurse app",
    version="2.0.0",
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
        "message": "CrashCurse AI Assistant Backend - CrewAI Edition",
        "version": "2.0.0",
        "status": "active",
        "agents": ["coordinator", "planning", "content", "integration", "voice"],
        "capabilities": [
            "Intelligent task routing",
            "Multi-agent coordination", 
            "Calendar and reminder management",
            "Content generation and brainstorming",
            "System integrations"
        ]
    }

@app.get("/health")
async def health_check():
    agent_statuses = {}
    
    try:
        # Check agent health
        agent_statuses["coordinator"] = "healthy" if coordinator_service else "not_initialized"
        agent_statuses["planning"] = "healthy" if planning_service else "not_initialized"
        agent_statuses["content"] = "healthy" if content_service else "not_initialized"
        agent_statuses["integration"] = "simulated"  # Not yet implemented
        agent_statuses["voice"] = "simulated"  # Not yet implemented
        
        overall_health = "healthy" if all(
            status in ["healthy", "simulated"] for status in agent_statuses.values()
        ) else "degraded"
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        overall_health = "unhealthy"
    
    return {
        "status": overall_health,
        "agents": agent_statuses,
        "websocket_connections": len(active_connections),
        "mode": "crewai_enabled",
        "timestamp": datetime.now().isoformat()
    }

# Chat endpoints with CrewAI integration
@app.post("/api/v1/chat/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the CrewAI multi-agent system
    """
    try:
        logger.info(f"📨 Received message from {request.user_id}: {request.message[:100]}...")
        
        conversation_id = f"{request.user_id}_{datetime.now().timestamp()}"
        
        # Store conversation
        conversations[conversation_id] = {
            "user_id": request.user_id,
            "message": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Route message through coordinator
        routing_result = await coordinator_service.route_task(
            request.message, 
            [conversations.get(k, {}) for k in list(conversations.keys())[-5:]]  # Last 5 conversations as context
        )
        
        recommended_agent = routing_result.get("recommended_agent", "general_chat")
        logger.info(f"🎯 Task routed to: {recommended_agent}")
        
        # Process with appropriate agent
        if recommended_agent == "planning_agent":
            response_data = await planning_service.process_planning_request(
                request.message, 
                request.context
            )
            agent_response = response_data.get("analysis", {}).get("intent", "Planning request processed")
            agent_type = "planning"
            
        elif recommended_agent == "content_agent":
            response_data = await content_service.process_content_request(
                request.message, 
                request.context
            )
            if response_data.get("content"):
                agent_response = response_data["content"]
            else:
                agent_response = response_data.get("message", "Content request processed")
            agent_type = "content"
            
        else:
            # General chat or coordinator response
            agent_response = await generate_intelligent_response(request.message, routing_result)
            agent_type = "coordinator"
        
        return ChatResponse(
            success=True,
            message=agent_response,
            agent_id=recommended_agent,
            agent_type=agent_type,
            conversation_id=conversation_id,
            metadata={
                "routing_result": routing_result,
                "task_complexity": routing_result.get("context", {}).get("message_complexity", "unknown"),
                "urgency": routing_result.get("context", {}).get("urgency_level", "normal")
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error in send_message: {e}")
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
            "total_count": len(user_conversations),
            "agent_routing_enabled": True
        }
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Planning endpoints with CrewAI
@app.post("/api/v1/planning/events", response_model=EventResponse)
async def create_event(request: EventRequest):
    """Create a new event using Planning Agent"""
    try:
        logger.info(f"📅 Creating event for {request.user_id}: {request.title}")
        
        result = await planning_service.create_event({
            "title": request.title,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "location": request.location,
            "description": request.description,
            "user_id": request.user_id
        })
        
        return EventResponse(
            success=result["success"],
            event_id=result.get("event_id"),
            message=result["message"],
            details=result.get("details")
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/planning/reminders", response_model=ReminderResponse)
async def create_reminder(request: ReminderRequest):
    """Create a reminder using Planning Agent"""
    try:
        logger.info(f"⏰ Creating reminder for {request.user_id}: {request.title}")
        
        result = await planning_service.create_reminder({
            "title": request.title,
            "due_date": request.due_date,
            "notes": request.notes,
            "priority": request.priority,
            "user_id": request.user_id
        })
        
        return ReminderResponse(
            success=result["success"],
            reminder_id=result.get("reminder_id"),
            message=result["message"],
            details=result.get("details")
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Content generation endpoints
@app.post("/api/v1/content/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """Generate content using Content Agent"""
    try:
        logger.info(f"✍️ Generating {request.type} content for {request.user_id}")
        
        if request.type == "email":
            result = await content_service.compose_email({
                "recipient": request.context.get("recipient", "Recipient") if request.context else "Recipient",
                "subject": request.context.get("subject", "Email Subject") if request.context else "Email Subject",
                "purpose": request.prompt,
                "tone": request.tone,
                "include_attachment": request.context.get("include_attachment", False) if request.context else False
            })
            content = result.get("email_content", "")
            
        elif request.type == "brainstorm":
            result = await content_service.brainstorm_ideas({
                "topic": request.prompt,
                "quantity": request.context.get("quantity", 5) if request.context else 5,
                "focus_area": request.context.get("focus_area", "general") if request.context else "general"
            })
            content = json.dumps(result.get("ideas", []), indent=2)
            
        else:  # text generation
            result = await content_service.generate_text({
                "type": request.type,
                "prompt": request.prompt,
                "tone": request.tone,
                "length": request.length
            })
            content = result.get("content", "")
        
        return ContentResponse(
            success=result["success"],
            content=content,
            content_type=request.type,
            message=result["message"],
            metadata={
                "word_count": result.get("word_count"),
                "character_count": result.get("character_count"),
                "tone": request.tone
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent management endpoints
@app.get("/api/v1/agents/status")
async def get_agents_status():
    """Get detailed status of all CrewAI agents"""
    return {
        "success": True,
        "agents": {
            "coordinator": {
                "status": "active" if coordinator_service else "inactive",
                "health": "good",
                "description": "Task routing and coordination",
                "tools": ["task_router", "user_context_analyzer"]
            },
            "planning": {
                "status": "active" if planning_service else "inactive", 
                "health": "good",
                "description": "Calendar events and reminders",
                "tools": ["calendar_tool", "reminder_tool", "scheduling_optimizer"]
            },
            "content": {
                "status": "active" if content_service else "inactive",
                "health": "good", 
                "description": "Text generation and brainstorming",
                "tools": ["text_generator", "email_composer", "idea_brainstormer"]
            },
            "integration": {
                "status": "planned",
                "health": "not_implemented",
                "description": "System integrations (calendar, mail, etc.)",
                "tools": ["apple_calendar_api", "mail_api", "safari_bookmarks"]
            },
            "voice": {
                "status": "planned", 
                "health": "not_implemented",
                "description": "Voice processing and synthesis",
                "tools": ["speech_to_text", "text_to_speech", "voice_synthesizer"]
            }
        },
        "coordination_enabled": True,
        "multi_agent_tasks": True
    }

@app.get("/api/v1/agents/list")
async def list_agents():
    """List all available CrewAI agents with capabilities"""
    return {
        "success": True,
        "agents": [
            {
                "id": "coordinator",
                "name": "Task Coordinator Agent",
                "description": "Routes and coordinates tasks between specialized agents",
                "status": "active",
                "capabilities": ["task_routing", "context_analysis", "multi_agent_coordination"]
            },
            {
                "id": "planning",
                "name": "Personal Planning Agent", 
                "description": "Manages calendar events, reminders, and schedule optimization",
                "status": "active",
                "capabilities": ["event_creation", "reminder_management", "schedule_optimization"]
            },
            {
                "id": "content",
                "name": "Content Generation Agent",
                "description": "Creates text content, emails, and brainstorms ideas",
                "status": "active", 
                "capabilities": ["text_generation", "email_composition", "idea_brainstorming"]
            },
            {
                "id": "integration",
                "name": "System Integration Agent",
                "description": "Integrates with external services and APIs",
                "status": "planned",
                "capabilities": ["calendar_integration", "email_integration", "web_services"]
            },
            {
                "id": "voice",
                "name": "Voice Processing Agent",
                "description": "Handles speech recognition and voice synthesis",
                "status": "planned",
                "capabilities": ["speech_to_text", "text_to_speech", "voice_commands"]
            }
        ]
    }

# WebSocket endpoint with agent routing
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    logger.info(f"🔌 Client {client_id} connected via WebSocket")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"📡 WebSocket message from {client_id}: {data}")
            
            try:
                # Route through coordinator for WebSocket messages too
                routing_result = await coordinator_service.route_task(data, [])
                recommended_agent = routing_result.get("recommended_agent", "general_chat")
                
                # Generate intelligent response
                ai_response = await generate_intelligent_response(data, routing_result)
                
                response = {
                    "type": "message",
                    "content": ai_response,
                    "agent_id": recommended_agent,
                    "routing_info": routing_result,
                    "timestamp": datetime.now().isoformat(),
                    "client_id": client_id
                }
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                error_response = {
                    "type": "error",
                    "content": "Sorry, I encountered an error processing your message.",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(error_response))
            
    except WebSocketDisconnect:
        if client_id in active_connections:
            del active_connections[client_id]
        logger.info(f"🔌 Client {client_id} disconnected")

async def generate_intelligent_response(message: str, routing_result: Dict[str, Any]) -> str:
    """Generate intelligent response based on routing results"""
    recommended_agent = routing_result.get("recommended_agent", "general_chat")
    context = routing_result.get("context", {})
    
    if recommended_agent == "planning_agent":
        return f"I can help you with planning! I've detected you want to work with scheduling or tasks. I can create events, set reminders, and optimize your schedule. What would you like me to help you plan?"
    
    elif recommended_agent == "content_agent":
        return f"I'm ready to help with content creation! I can write emails, generate text content, or brainstorm ideas for you. What type of content would you like me to create?"
    
    elif recommended_agent == "voice_agent":
        return "Voice processing capabilities are coming soon! For now, I can help you with text-based planning and content creation."
    
    elif recommended_agent == "integration_agent":
        return "System integration features are in development! I can currently help with planning and content generation."
    
    else:
        # General chat response
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return f"Hello! I'm your AI assistant powered by multiple specialized agents. I can help with planning, content creation, and more. What can I do for you today?"
        
        elif any(word in message_lower for word in ['help', 'what can you do']):
            return """I'm your multi-agent AI assistant! Here's what I can help you with:

🗓️ **Planning**: Create events, set reminders, optimize schedules
✍️ **Content**: Write emails, generate text, brainstorm ideas  
🤖 **Coordination**: Route tasks to the best specialist agent
📱 **Integration**: Connect with your iOS apps (coming soon)
🎤 **Voice**: Speech processing (coming soon)

Just tell me what you need help with, and I'll route your request to the most suitable agent!"""
        
        else:
            complexity = context.get("message_complexity", "simple")
            urgency = context.get("urgency_level", "normal")
            
            response = f"I understand you said: '{message}'. "
            
            if complexity == "high":
                response += "This seems like a complex request. Let me analyze how I can best help you with my specialized agents. "
            
            if urgency == "high":
                response += "I notice this seems urgent - I'll prioritize this request. "
            
            response += "I can help with planning, content creation, or general assistance. Could you tell me more about what you'd like to accomplish?"
            
            return response

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    logger.info(f"🚀 Starting CrewAI Backend on {host}:{port}")
    
    uvicorn.run(
        "main_crewai:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    ) 