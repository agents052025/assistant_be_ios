#!/usr/bin/env python3
"""
🚀 CrashCurse AI Backend 2025 - Simplified Version
Використовує CrewAI 0.121.0 з базовою функціональністю
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# CrewAI 2025 imports
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA MODELS
# =============================================================================

class ChatMessage(BaseModel):
    type: str = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")

# =============================================================================
# SIMPLE CREWAI TOOLS
# =============================================================================

@tool("simple_responder")
def simple_response_tool(message: str) -> str:
    """Простий інструмент для відповідей користувачу"""
    # Basic response logic
    if "привіт" in message.lower() or "hello" in message.lower():
        return "Привіт! Я AI асистент CrashCurse. Як можу допомогти?"
    elif "план" in message.lower() or "planning" in message.lower():
        return "Допоможу з плануванням! Опишіть, що потрібно організувати."
    elif "контент" in message.lower() or "content" in message.lower():
        return "Створюю контент! Скажіть, який тип контенту вам потрібен."
    else:
        return f"Розумію ваш запит: '{message}'. Обробляю інформацію та готую відповідь..."

# =============================================================================
# SIMPLE CREWAI AGENT
# =============================================================================

def create_simple_agent():
    """Створює простого AI агента"""
    return Agent(
        role="AI Assistant",
        goal="Допомагати користувачам з різними завданнями",
        backstory="""Ти корисний AI асистент для iOS додатку CrashCurse. 
        Твоя мета - надавати якісну допомогу користувачам.""",
        verbose=True,
        tools=[simple_response_tool],
        max_iter=2,
        memory=False  # Простіша конфігурація
    )

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="CrashCurse AI Backend 2025 - Simple",
    description="Simplified CrewAI backend for iOS app",
    version="2025.1.0-simple"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "CrashCurse AI Backend 2025 - Simple",
        "version": "2025.1.0-simple",
        "framework": "CrewAI 0.121.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "crewai_version": "0.121.0",
        "features": ["basic_chat", "simple_agents"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Simple chat endpoint with CrewAI"""
    try:
        logger.info(f"Processing chat request: {request.message}")
        
        # Create agent and task
        agent = create_simple_agent()
        
        task = Task(
            description=f"Відповідь на повідомлення користувача: {request.message}",
            expected_output="Корисна та дружня відповідь українською мовою",
            agent=agent
        )
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute
        result = crew.kickoff()
        
        # Prepare response
        response = ChatMessage(
            type="assistant",
            content=str(result),
            metadata={
                "conversation_id": request.conversation_id,
                "processing_time": "< 1s",
                "agent_used": "simple_agent"
            }
        )
        
        logger.info(f"Chat response prepared successfully")
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        # Fallback response
        return ChatMessage(
            type="assistant",
            content=f"Вибачте, сталася помилка: {str(e)}. Спробуйте ще раз.",
            metadata={"error": True}
        )

@app.post("/planning")
async def planning_endpoint(request: ChatRequest):
    """Simple planning endpoint"""
    return await chat_endpoint(ChatRequest(
        message=f"Створи план для: {request.message}",
        conversation_id=request.conversation_id
    ))

@app.post("/content")
async def content_endpoint(request: ChatRequest):
    """Simple content creation endpoint"""
    return await chat_endpoint(ChatRequest(
        message=f"Створи контент: {request.message}",
        conversation_id=request.conversation_id
    ))

# =============================================================================
# STARTUP
# =============================================================================

if __name__ == "__main__":
    logger.info("🚀 Starting CrashCurse AI Backend 2025 - Simple Version")
    logger.info("Framework: CrewAI 0.121.0")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 