from crewai import Agent, Task
from crewai.tools import BaseTool
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class CalendarTool(BaseTool):
    name: str = "calendar_tool"
    description: str = "Creates and manages calendar events"
    
    def _run(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event"""
        try:
            # This would integrate with iOS EventKit or system calendar
            # For now, return mock success
            event_id = f"event_{int(datetime.now().timestamp())}"
            
            result = {
                "event_id": event_id,
                "title": event_data.get("title", "New Event"),
                "start_date": event_data.get("start_date"),
                "end_date": event_data.get("end_date"),
                "location": event_data.get("location"),
                "created": True,
                "message": f"Event '{event_data.get('title')}' successfully created"
            }
            
            logger.info(f"Calendar event created: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"created": False, "error": str(e)}

class ReminderTool(BaseTool):
    name: str = "reminder_tool"
    description: str = "Creates and manages reminders and tasks"
    
    def _run(self, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a reminder"""
        try:
            reminder_id = f"reminder_{int(datetime.now().timestamp())}"
            
            result = {
                "reminder_id": reminder_id,
                "title": reminder_data.get("title", "New Reminder"),
                "due_date": reminder_data.get("due_date"),
                "notes": reminder_data.get("notes"),
                "priority": reminder_data.get("priority", "normal"),
                "created": True,
                "message": f"Reminder '{reminder_data.get('title')}' successfully created"
            }
            
            logger.info(f"Reminder created: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return {"created": False, "error": str(e)}

class SchedulingOptimizerTool(BaseTool):
    name: str = "scheduling_optimizer"
    description: str = "Optimizes scheduling by finding best time slots and avoiding conflicts"
    
    def _run(self, optimization_request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize scheduling for events"""
        try:
            # Mock optimization logic
            duration = optimization_request.get("duration", 60)  # minutes
            preferred_time = optimization_request.get("preferred_time")
            
            # Simple optimization: suggest next available slot
            if preferred_time:
                optimal_time = preferred_time
            else:
                # Suggest tomorrow at 2 PM by default
                tomorrow = datetime.now() + timedelta(days=1)
                optimal_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
            
            result = {
                "optimized": True,
                "suggested_time": optimal_time.isoformat(),
                "duration_minutes": duration,
                "conflicts_found": False,
                "alternative_slots": [
                    (optimal_time + timedelta(hours=1)).isoformat(),
                    (optimal_time + timedelta(hours=2)).isoformat()
                ],
                "optimization_score": 0.95
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in scheduling optimization: {e}")
            return {"optimized": False, "error": str(e)}

def create_planning_agent() -> Agent:
    """Create the Planning Agent"""
    
    calendar_tool = CalendarTool()
    reminder_tool = ReminderTool()
    scheduling_optimizer = SchedulingOptimizerTool()
    
    planning_agent = Agent(
        role="Personal Planner",
        goal="Створювати та управляти подіями, нагадуваннями та оптимізувати розклад користувача",
        backstory="""Ти експертний персональний планувальник з багаторічним досвідом 
        в організації часу та управлінні завданнями. Ти розумієш важливість балансу 
        між роботою та особистим життям, вмієш знаходити оптимальні часові слоти 
        та попереджувати конфлікти в розкладі. 
        
        Твої основні навички:
        - Створення подій у календарі
        - Встановлення нагадувань та задач
        - Оптимізація розкладу
        - Аналіз пріоритетів
        - Попередження конфліктів у часі""",
        tools=[calendar_tool, reminder_tool, scheduling_optimizer],
        verbose=True,
        memory=True,
        max_iter=3,
        max_execution_time=30
    )
    
    return planning_agent

class PlanningService:
    """Service class for managing planning agent operations"""
    
    def __init__(self):
        self.planning_agent = create_planning_agent()
        logger.info("Planning Agent initialized successfully")
    
    async def create_event(self, event_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calendar event"""
        try:
            calendar_tool = CalendarTool()
            
            # Prepare event data
            event_data = {
                "title": event_request.get("title", "New Event"),
                "start_date": event_request.get("start_date"),
                "end_date": event_request.get("end_date"),
                "location": event_request.get("location"),
                "description": event_request.get("description"),
                "user_id": event_request.get("user_id", "anonymous")
            }
            
            # Create the event
            result = calendar_tool._run(event_data)
            
            return {
                "success": result.get("created", False),
                "event_id": result.get("event_id"),
                "message": result.get("message", "Event creation failed"),
                "details": event_data
            }
            
        except Exception as e:
            logger.error(f"Error in create_event: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create event"
            }
    
    async def create_reminder(self, reminder_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new reminder"""
        try:
            reminder_tool = ReminderTool()
            
            # Prepare reminder data
            reminder_data = {
                "title": reminder_request.get("title", "New Reminder"),
                "due_date": reminder_request.get("due_date"),
                "notes": reminder_request.get("notes"),
                "priority": reminder_request.get("priority", "normal"),
                "user_id": reminder_request.get("user_id", "anonymous")
            }
            
            # Create the reminder
            result = reminder_tool._run(reminder_data)
            
            return {
                "success": result.get("created", False),
                "reminder_id": result.get("reminder_id"),
                "message": result.get("message", "Reminder creation failed"),
                "details": reminder_data
            }
            
        except Exception as e:
            logger.error(f"Error in create_reminder: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create reminder"
            }
    
    async def optimize_schedule(self, optimization_request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize scheduling for better time management"""
        try:
            optimizer = SchedulingOptimizerTool()
            
            # Get optimization suggestions
            result = optimizer._run(optimization_request)
            
            return {
                "success": result.get("optimized", False),
                "suggested_time": result.get("suggested_time"),
                "duration_minutes": result.get("duration_minutes"),
                "conflicts_found": result.get("conflicts_found", False),
                "alternative_slots": result.get("alternative_slots", []),
                "optimization_score": result.get("optimization_score", 0.0),
                "message": "Schedule optimization completed" if result.get("optimized") else "Optimization failed"
            }
            
        except Exception as e:
            logger.error(f"Error in optimize_schedule: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to optimize schedule"
            }
    
    async def process_planning_request(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process general planning requests using the agent"""
        try:
            planning_task = Task(
                description=f"""
                User planning request: "{user_message}"
                Context: {context or {}}
                
                Analyze this request and:
                1. Determine what planning action is needed
                2. Extract relevant details (dates, times, titles, etc.)
                3. Provide a structured response with recommendations
                4. If this is an event creation, provide event details
                5. If this is a reminder, provide reminder details
                6. If this is schedule optimization, provide suggestions
                
                Respond with actionable planning recommendations.
                """,
                agent=self.planning_agent,
                expected_output="Structured planning recommendations with specific actions"
            )
            
            # For now, return a structured analysis instead of running CrewAI
            # This would be replaced with actual agent execution in production
            analysis = self._analyze_planning_request(user_message)
            
            return {
                "success": True,
                "analysis": analysis,
                "recommendations": self._generate_recommendations(analysis),
                "next_actions": self._suggest_next_actions(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error processing planning request: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process planning request"
            }
    
    def _analyze_planning_request(self, user_message: str) -> Dict[str, Any]:
        """Analyze user message for planning intent"""
        message_lower = user_message.lower()
        
        analysis = {
            "intent": "general",
            "confidence": 0.5,
            "extracted_entities": {},
            "suggested_action": "ask_for_more_details"
        }
        
        # Detect intent
        if any(word in message_lower for word in ['create', 'add', 'schedule', 'book']):
            if any(word in message_lower for word in ['event', 'meeting', 'appointment']):
                analysis["intent"] = "create_event"
                analysis["confidence"] = 0.9
            elif any(word in message_lower for word in ['reminder', 'remind', 'task']):
                analysis["intent"] = "create_reminder"
                analysis["confidence"] = 0.9
        elif any(word in message_lower for word in ['optimize', 'best time', 'when should']):
            analysis["intent"] = "optimize_schedule"
            analysis["confidence"] = 0.8
        
        # Extract basic entities (this would be enhanced with NLP in production)
        if 'tomorrow' in message_lower:
            analysis["extracted_entities"]["relative_date"] = "tomorrow"
        if 'next week' in message_lower:
            analysis["extracted_entities"]["relative_date"] = "next_week"
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        intent = analysis.get("intent", "general")
        
        if intent == "create_event":
            recommendations.extend([
                "I can help you create a calendar event",
                "Please provide the event title, date, and time",
                "Optionally include location and description"
            ])
        elif intent == "create_reminder":
            recommendations.extend([
                "I can set up a reminder for you",
                "Please specify what you want to be reminded about",
                "Include the date/time when you want to be reminded"
            ])
        elif intent == "optimize_schedule":
            recommendations.extend([
                "I can help optimize your schedule",
                "Please tell me about the activity you want to schedule",
                "Include preferred times or duration if you have preferences"
            ])
        else:
            recommendations.extend([
                "I can help with calendar events, reminders, and schedule optimization",
                "Try asking me to 'create an event', 'set a reminder', or 'find the best time for...'"
            ])
        
        return recommendations
    
    def _suggest_next_actions(self, analysis: Dict[str, Any]) -> List[str]:
        """Suggest next actions based on analysis"""
        intent = analysis.get("intent", "general")
        
        if intent == "create_event":
            return ["collect_event_details", "create_calendar_event"]
        elif intent == "create_reminder":
            return ["collect_reminder_details", "create_reminder"]
        elif intent == "optimize_schedule":
            return ["collect_optimization_criteria", "run_optimization"]
        else:
            return ["clarify_intent", "provide_help"] 