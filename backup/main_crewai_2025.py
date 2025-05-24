#!/usr/bin/env python3
"""
🚀 CrashCurse AI Backend 2025 - Modern CrewAI Implementation
Використовує найновіші можливості CrewAI 0.121.0:
- Standalone framework (без LangChain)
- Flows + Crews архітектура
- Сучасні інструменти та інтеграції
- Підтримка iOS додатку
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# CrewAI 2025 imports - standalone framework
from crewai import Agent, Task, Crew, Process, Flow
from crewai.flow.flow import listen, start, router
from crewai.tools import tool  # Fixed import path for tool decorator
from crewai_tools import (
    FileReadTool, 
    FileWriterTool,  # Fixed: FileWriterTool not FileWriteTool
    SerperDevTool,  # For web search
    WebsiteSearchTool,
    TXTSearchTool, PDFSearchTool, CSVSearchTool, 
    DirectoryReadTool, JsonTool,
    BaseTool
)
from langchain.tools import tool
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA MODELS (iOS COMPATIBILITY)
# =============================================================================

class ChatMessage(BaseModel):
    type: str = Field(..., description="Message type: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PlanningRequest(BaseModel):
    task: str = Field(..., description="Planning task")
    deadline: Optional[str] = Field(None, description="Task deadline")
    priority: str = Field(default="medium", description="Task priority")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ContentRequest(BaseModel):
    content_type: str = Field(..., description="Type of content to generate")
    prompt: str = Field(..., description="Content generation prompt")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentStatus(BaseModel):
    agent_id: str
    name: str
    status: str  # active, idle, busy, error
    current_task: Optional[str] = None
    last_activity: datetime = Field(default_factory=datetime.now)

# =============================================================================
# MODERN CREWAI TOOLS (2025)
# =============================================================================

@tool("task_analyzer")
def analyze_task_complexity(task_description: str) -> str:
    """Аналізує складність завдання та рекомендує підходящих агентів"""
    # Smart task analysis logic
    keywords = task_description.lower()
    
    if any(word in keywords for word in ['plan', 'schedule', 'organize', 'calendar']):
        return "planning_required"
    elif any(word in keywords for word in ['write', 'content', 'article', 'email']):
        return "content_creation"
    elif any(word in keywords for word in ['research', 'search', 'find', 'analyze']):
        return "research_needed"
    else:
        return "general_assistance"

@tool("context_memory")
def store_conversation_context(conversation_id: str, context: dict) -> str:
    """Зберігає контекст розмови для подальшого використання"""
    # In production, this would store to a database
    context_store = getattr(store_conversation_context, '_store', {})
    context_store[conversation_id] = context
    store_conversation_context._store = context_store
    return f"Context stored for conversation {conversation_id}"

@tool("ios_formatter")
def format_for_ios(content: str, format_type: str = "markdown") -> str:
    """Форматує контент для оптимального відображення в iOS додатку"""
    if format_type == "markdown":
        # Clean and optimize markdown for iOS
        content = content.replace("```", "\n```\n")
        content = content.replace("**", "**")  # Ensure bold formatting
        return content
    elif format_type == "json":
        # Structure content as JSON for iOS parsing
        return f'{{"formatted_content": "{content.replace(chr(34), chr(92)+chr(34))}", "type": "response"}}'
    else:
        return content

# =============================================================================
# MODERN CREWAI AGENTS (2025)
# =============================================================================

class ModernCrashCurseAgents:
    """Сучасні AI агенти для CrashCurse iOS додатку"""
    
    @staticmethod
    def create_coordinator_agent() -> Agent:
        """Координатор - керує розподілом завдань між агентами"""
        return Agent(
            role="AI Task Coordinator",
            goal="Ефективно розподіляти завдання між спеціалізованими агентами та координувати їх роботу",
            backstory="""Ти досвідчений координатор AI асистентів, який спеціалізується на 
            аналізі запитів користувачів та призначенні найкращих агентів для кожного завдання. 
            Ти розумієш специфіку роботи з iOS додатками та можеш адаптувати відповіді для 
            оптимального користувацького досвіду.""",
            verbose=True,
            tools=[analyze_task_complexity, context_memory, ios_formatter],
            max_iter=3,
            memory=True
        )
    
    @staticmethod
    def create_planning_agent() -> Agent:
        """Агент планування - спеціалізується на організації та плануванні"""
        return Agent(
            role="Strategic Planning Specialist",
            goal="Створювати детальні плани, організовувати завдання та допомагати з time management",
            backstory="""Ти експерт з планування та організації часу. Твоя спеціальність - 
            створення структурованих планів, розбиття великих завдань на менші кроки, 
            встановлення пріоритетів та оптимізація продуктивності. Ти особливо добре 
            розумієш потреби користувачів мобільних додатків.""",
            verbose=True,
            tools=[ios_formatter],
            max_iter=3,
            memory=True
        )
    
    @staticmethod
    def create_content_agent() -> Agent:
        """Агент контенту - спеціалізується на створенні різних типів контенту"""
        return Agent(
            role="Creative Content Specialist",
            goal="Створювати високоякісний контент: тексти, статті, емейли та креативні матеріали",
            backstory="""Ти талановитий письменник та контент-креатор з великим досвідом у 
            створенні різноманітного контенту. Ти можеш писати у різних стилях - від 
            професійних емейлів до креативних статей. Особливо добре адаптуєш контент 
            для мобільних платформ та iOS додатків.""",
            verbose=True,
            tools=[FileWriterTool(), ios_formatter],
            max_iter=3,
            memory=True
        )
    
    @staticmethod
    def create_research_agent() -> Agent:
        """Агент дослідження - спеціалізується на пошуку та аналізі інформації"""
        return Agent(
            role="Research & Analysis Expert",
            goal="Проводити глибокі дослідження, аналізувати інформацію та надавати точні факти",
            backstory="""Ти досвідчений дослідник з відмінними навичками аналізу інформації. 
            Ти можеш швидко знайти релевантну інформацію, проаналізувати її достовірність 
            та представити результати у зрозумілому форматі. Ти особливо добре працюєш 
            з сучасними джерелами та технологіями.""",
            verbose=True,
            tools=[SerperDevTool(), WebsiteSearchTool(), ios_formatter],
            max_iter=3,
            memory=True
        )

# =============================================================================
# MODERN CREWAI FLOWS (2025) - Precision Control
# =============================================================================

class CrashCurseState(BaseModel):
    """State for CrewAI Flow management"""
    user_request: str = ""
    task_type: str = ""
    assigned_agent: str = ""
    result: str = ""
    confidence: float = 0.0
    conversation_id: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)

class CrashCurseFlow(Flow[CrashCurseState]):
    """Сучасний Flow для обробки запитів з точним контролем"""
    
    def __init__(self):
        super().__init__()
        self.agents = ModernCrashCurseAgents()
        
    @start()
    def analyze_request(self):
        """Початковий аналіз запиту користувача"""
        logger.info(f"Analyzing request: {self.state.user_request}")
        
        # Аналіз типу завдання
        task_analysis = analyze_task_complexity(self.state.user_request)
        self.state.task_type = task_analysis
        
        logger.info(f"Task type determined: {task_analysis}")
        return {"analysis": task_analysis, "request": self.state.user_request}
    
    @router(analyze_request)
    def route_to_specialist(self):
        """Маршрутизація до відповідного агента"""
        if self.state.task_type == "planning_required":
            return "planning_flow"
        elif self.state.task_type == "content_creation":
            return "content_flow"
        elif self.state.task_type == "research_needed":
            return "research_flow"
        else:
            return "general_flow"
    
    @listen("planning_flow")
    def handle_planning(self):
        """Обробка планувальних завдань"""
        agent = self.agents.create_planning_agent()
        
        task = Task(
            description=f"Створи детальний план для: {self.state.user_request}",
            expected_output="Структурований план з конкретними кроками та рекомендаціями",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        formatted_result = ios_formatter(str(result), "markdown")
        self.state.result = formatted_result
        self.state.confidence = 0.9
        return formatted_result
    
    @listen("content_flow")
    def handle_content(self):
        """Обробка створення контенту"""
        agent = self.agents.create_content_agent()
        
        task = Task(
            description=f"Створи якісний контент для: {self.state.user_request}",
            expected_output="Професійно написаний контент, адаптований для мобільного використання",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        formatted_result = ios_formatter(str(result), "markdown")
        self.state.result = formatted_result
        self.state.confidence = 0.9
        return formatted_result
    
    @listen("research_flow")
    def handle_research(self):
        """Обробка дослідницьких завдань"""
        agent = self.agents.create_research_agent()
        
        task = Task(
            description=f"Проведи дослідження та проаналізуй: {self.state.user_request}",
            expected_output="Детальний аналіз з фактами, джерелами та висновками",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        formatted_result = ios_formatter(str(result), "markdown")
        self.state.result = formatted_result
        self.state.confidence = 0.8
        return formatted_result
    
    @listen("general_flow")
    def handle_general(self):
        """Обробка загальних запитів"""
        coordinator = self.agents.create_coordinator_agent()
        
        task = Task(
            description=f"Допоможи користувачу з: {self.state.user_request}",
            expected_output="Корисна та зрозуміла відповідь на запит користувача",
            agent=coordinator
        )
        
        crew = Crew(
            agents=[coordinator],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        formatted_result = ios_formatter(str(result), "markdown")
        self.state.result = formatted_result
        self.state.confidence = 0.7
        return formatted_result

# =============================================================================
# FASTAPI APPLICATION WITH WEBSOCKET SUPPORT
# =============================================================================

# Global state
active_flows: Dict[str, CrashCurseFlow] = {}
agent_statuses: Dict[str, AgentStatus] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 CrashCurse AI Backend 2025 starting...")
    
    # Initialize agent statuses
    agent_statuses.update({
        "coordinator": AgentStatus(agent_id="coordinator", name="AI Coordinator", status="idle"),
        "planning": AgentStatus(agent_id="planning", name="Planning Specialist", status="idle"),
        "content": AgentStatus(agent_id="content", name="Content Creator", status="idle"),
        "research": AgentStatus(agent_id="research", name="Research Expert", status="idle")
    })
    
    yield
    
    logger.info("🛑 CrashCurse AI Backend 2025 shutting down...")

# Create FastAPI app with modern configuration
app = FastAPI(
    title="CrashCurse AI Backend 2025",
    description="Modern CrewAI-powered backend for iOS CrashCurse app",
    version="2025.1.0",
    lifespan=lifespan
)

# Configure CORS for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify iOS app origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "CrashCurse AI Backend 2025",
        "version": "2025.1.0",
        "framework": "CrewAI 0.121.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/agents/status")
async def get_agent_status():
    """Get status of all AI agents"""
    return {
        "agents": list(agent_statuses.values()),
        "active_flows": len(active_flows),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Modern chat endpoint using CrewAI Flows"""
    try:
        conversation_id = request.conversation_id or f"conv_{datetime.now().timestamp()}"
        
        # Create new Flow instance
        flow = CrashCurseFlow()
        flow.state.user_request = request.message
        flow.state.conversation_id = conversation_id
        flow.state.context = request.context or {}
        
        # Store active flow
        active_flows[conversation_id] = flow
        
        # Execute the flow
        result = flow.kickoff()
        
        # Prepare response
        response = ChatMessage(
            type="assistant",
            content=flow.state.result,
            metadata={
                "conversation_id": conversation_id,
                "task_type": flow.state.task_type,
                "confidence": flow.state.confidence,
                "processing_time": "< 1s"  # In production, calculate actual time
            }
        )
        
        # Cleanup
        if conversation_id in active_flows:
            del active_flows[conversation_id]
        
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@app.post("/planning")
async def planning_endpoint(request: PlanningRequest):
    """Specialized planning endpoint"""
    try:
        flow = CrashCurseFlow()
        flow.state.user_request = f"Planning task: {request.task}. Deadline: {request.deadline}. Priority: {request.priority}"
        flow.state.task_type = "planning_required"
        flow.state.context = request.context or {}
        
        result = flow.kickoff()
        
        return {
            "plan": flow.state.result,
            "confidence": flow.state.confidence,
            "task": request.task,
            "deadline": request.deadline,
            "priority": request.priority,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Planning endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Planning error: {str(e)}")

@app.post("/content")
async def content_endpoint(request: ContentRequest):
    """Specialized content creation endpoint"""
    try:
        flow = CrashCurseFlow()
        flow.state.user_request = f"Create {request.content_type}: {request.prompt}"
        flow.state.task_type = "content_creation"
        flow.state.context = request.parameters or {}
        
        result = flow.kickoff()
        
        return {
            "content": flow.state.result,
            "confidence": flow.state.confidence,
            "content_type": request.content_type,
            "parameters": request.parameters,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Content endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content creation error: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time communication with iOS app"""
    await websocket.accept()
    client_id = f"client_{datetime.now().timestamp()}"
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        while True:
            # Receive message from iOS app
            data = await websocket.receive_json()
            message_type = data.get("type", "chat")
            content = data.get("content", "")
            
            logger.info(f"WebSocket message from {client_id}: {message_type}")
            
            if message_type == "chat":
                # Process chat message through Flow
                flow = CrashCurseFlow()
                flow.state.user_request = content
                flow.state.conversation_id = client_id
                
                result = flow.kickoff()
                
                # Send response back to iOS app
                await websocket.send_json({
                    "type": "response",
                    "content": flow.state.result,
                    "metadata": {
                        "task_type": flow.state.task_type,
                        "confidence": flow.state.confidence,
                        "timestamp": datetime.now().isoformat()
                    }
                })
            
            elif message_type == "status":
                # Send agent status
                await websocket.send_json({
                    "type": "status",
                    "agents": [agent.dict() for agent in agent_statuses.values()],
                    "active_flows": len(active_flows)
                })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {str(e)}")
        await websocket.close()

# =============================================================================
# MAIN APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Check for required environment variables
    required_env_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.info("App will start but some features may not work correctly")
    
    logger.info("🚀 Starting CrashCurse AI Backend 2025...")
    logger.info("Features: CrewAI 0.121.0, Flows + Crews, iOS optimized, WebSocket support")
    
    uvicorn.run(
        "main_crewai_2025:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disabled reload to prevent issues with venv file changes
        log_level="info"
    ) 