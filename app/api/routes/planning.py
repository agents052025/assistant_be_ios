from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from app.services.crew_manager import CrewManager
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class EventRequest(BaseModel):
    title: str
    start_date: str  # ISO format
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    user_id: str = "anonymous"

class EventResponse(BaseModel):
    success: bool
    event_id: Optional[str] = None
    message: str
    event_plan: Optional[str] = None
    suggested_optimizations: Optional[List[str]] = None

class TaskRequest(BaseModel):
    description: str
    due_date: Optional[str] = None  # ISO format
    priority: Optional[str] = "medium"
    user_id: str = "anonymous"

class TaskResponse(BaseModel):
    success: bool
    task_id: Optional[str] = None
    message: str
    task_breakdown: Optional[List[str]] = None
    estimated_time: Optional[str] = None

class ScheduleOptimizationRequest(BaseModel):
    events: List[Dict[str, Any]]
    preferences: Optional[Dict[str, Any]] = None
    user_id: str = "anonymous"

class ScheduleOptimizationResponse(BaseModel):
    success: bool
    analysis: str
    conflicts: List[str]
    suggestions: List[str]
    optimized_schedule: Optional[List[Dict]] = None

# Initialize crew manager
crew_manager = CrewManager()

@router.post("/events", response_model=EventResponse)
async def create_event(request: EventRequest, db: Session = Depends(get_db)):
    """
    Create a new event using the planning agent
    This endpoint matches the iOS NetworkService.createEvent() function
    """
    try:
        logger.info(f"Creating event for user {request.user_id}: {request.title}")
        
        # Prepare event data for the planning agent
        event_data = {
            "title": request.title,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "location": request.location,
            "description": request.description,
            "user_id": request.user_id
        }
        
        # Process through CrewAI planning agent
        result = await crew_manager.create_event(event_data)
        
        if result.get("success"):
            return EventResponse(
                success=True,
                event_id=f"event_{datetime.now().timestamp()}",
                message="Event created successfully",
                event_plan=result.get("event_plan"),
                suggested_optimizations=result.get("checklist", [])
            )
        else:
            return EventResponse(
                success=False,
                message=result.get("error", "Failed to create event"),
                event_plan=None
            )
            
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, db: Session = Depends(get_db)):
    """
    Create a new task using the planning agent
    This endpoint matches task creation functionality
    """
    try:
        logger.info(f"Creating task for user {request.user_id}: {request.description[:50]}...")
        
        # Prepare task request for the planning agent
        task_request = f"Create a task: {request.description}"
        if request.due_date:
            task_request += f" Due date: {request.due_date}"
        if request.priority:
            task_request += f" Priority: {request.priority}"
        
        # Process through CrewAI planning agent
        result = await crew_manager.manage_tasks(task_request, [])
        
        if result.get("success"):
            return TaskResponse(
                success=True,
                task_id=f"task_{datetime.now().timestamp()}",
                message="Task created successfully",
                task_breakdown=result.get("priorities", []),
                estimated_time=result.get("timeline", {}).get("estimated_time")
            )
        else:
            return TaskResponse(
                success=False,
                message=result.get("error", "Failed to create task"),
                task_breakdown=None
            )
            
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reminders", response_model=TaskResponse)
async def create_reminder(
    description: str,
    due_date: Optional[str] = None,
    user_id: str = "anonymous",
    db: Session = Depends(get_db)
):
    """
    Create a reminder using the planning agent
    This endpoint matches the iOS NetworkService.createReminder() function
    """
    try:
        logger.info(f"Creating reminder for user {user_id}: {description[:50]}...")
        
        # Format as task request for planning agent
        reminder_request = f"Create a reminder: {description}"
        if due_date:
            reminder_request += f" Remind me on: {due_date}"
        
        # Process through CrewAI planning agent
        result = await crew_manager.manage_tasks(reminder_request, [])
        
        if result.get("success"):
            return TaskResponse(
                success=True,
                task_id=f"reminder_{datetime.now().timestamp()}",
                message="Reminder created successfully",
                task_breakdown=[description],
                estimated_time=due_date
            )
        else:
            return TaskResponse(
                success=False,
                message=result.get("error", "Failed to create reminder"),
                task_breakdown=None
            )
            
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-schedule", response_model=ScheduleOptimizationResponse)
async def optimize_schedule(request: ScheduleOptimizationRequest, db: Session = Depends(get_db)):
    """
    Optimize a user's schedule using the planning agent
    """
    try:
        logger.info(f"Optimizing schedule for user {request.user_id} with {len(request.events)} events")
        
        # Prepare schedule data for the planning agent
        schedule_data = {
            "events": request.events,
            "preferences": request.preferences or {},
            "user_id": request.user_id
        }
        
        # Get planning agent and optimize
        if not crew_manager.planning_agent:
            await crew_manager.initialize()
        
        result = await crew_manager.planning_agent.optimize_schedule(schedule_data)
        
        if result.get("success"):
            return ScheduleOptimizationResponse(
                success=True,
                analysis=result.get("analysis", "Schedule analyzed"),
                conflicts=result.get("conflicts", []),
                suggestions=result.get("suggestions", []),
                optimized_schedule=None  # Could include optimized schedule here
            )
        else:
            return ScheduleOptimizationResponse(
                success=False,
                analysis=result.get("error", "Failed to optimize schedule"),
                conflicts=[],
                suggestions=[]
            )
            
    except Exception as e:
        logger.error(f"Error optimizing schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{user_id}")
async def get_user_events(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """
    Get events for a specific user
    """
    try:
        # In a production system, you'd fetch from database
        # For now, return a sample response
        return {
            "success": True,
            "events": [],
            "total_count": 0,
            "message": "No events found for user"
        }
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{user_id}")
async def get_user_tasks(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """
    Get tasks for a specific user
    """
    try:
        # In a production system, you'd fetch from database
        # For now, return a sample response
        return {
            "success": True,
            "tasks": [],
            "total_count": 0,
            "message": "No tasks found for user"
        }
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/planning-suggestions/{user_id}")
async def get_planning_suggestions(user_id: str, db: Session = Depends(get_db)):
    """
    Get AI-generated planning suggestions for a user
    """
    try:
        # Use planning agent to generate suggestions
        if not crew_manager.planning_agent:
            await crew_manager.initialize()
        
        # For demo purposes, provide general suggestions
        suggestions = [
            "Consider blocking time for deep work in the morning",
            "Add buffer time between meetings",
            "Schedule regular breaks every 2 hours",
            "Group similar tasks together",
            "Set aside time for planning and review"
        ]
        
        return {
            "success": True,
            "suggestions": suggestions,
            "generated_by": "planning_agent",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating planning suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 