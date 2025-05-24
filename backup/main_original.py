from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager

# Import our modules
from app.core.config import settings
from app.api.routes import chat, planning, voice, agents, auth
from app.core.database import init_db
from app.services.crew_manager import CrewManager
from app.services.websocket_manager import WebSocketManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
crew_manager = CrewManager()
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CrashCurse Backend...")
    await init_db()
    await crew_manager.initialize()
    logger.info("Backend initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down CrashCurse Backend...")
    await crew_manager.cleanup()

# Create FastAPI app
app = FastAPI(
    title="CrashCurse AI Assistant Backend",
    description="Multi-agent AI system backend for iOS CrashCurse app",
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

# Include API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(planning.router, prefix="/api/v1/planning", tags=["planning"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])

@app.get("/")
async def root():
    return {
        "message": "CrashCurse AI Assistant Backend",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents_active": await crew_manager.get_active_agents_count(),
        "websocket_connections": websocket_manager.get_connection_count()
    }

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Process real-time messages
            response = await crew_manager.process_realtime_message(data, client_id)
            await websocket_manager.send_personal_message(response, client_id)
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 