from typing import Dict, List, Any, Optional
import asyncio
import logging
from datetime import datetime

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.planning_agent import PlanningAgent
from app.core.config import settings

logger = logging.getLogger(__name__)

class CrewManager:
    """
    Central manager for all AI agents and their coordination
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.active_conversations: Dict[str, Dict] = {}
        self.coordinator: Optional[CoordinatorAgent] = None
        self.planning_agent: Optional[PlanningAgent] = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all agents"""
        try:
            logger.info("Initializing CrewManager and agents...")
            
            # Initialize coordinator
            self.coordinator = CoordinatorAgent()
            self.agents['coordinator'] = self.coordinator
            
            # Initialize specialized agents
            self.planning_agent = PlanningAgent()
            self.agents['planning'] = self.planning_agent
            
            # TODO: Initialize other agents (content, integration, voice)
            # self.content_agent = ContentGenerationAgent()
            # self.integration_agent = IntegrationAgent()
            # self.voice_agent = VoiceProcessingAgent()
            
            self.initialized = True
            logger.info(f"Successfully initialized {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Error initializing CrewManager: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up CrewManager...")
        self.active_conversations.clear()
        self.agents.clear()
        self.initialized = False
    
    async def process_message(self, message: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user message through the agent system
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            conversation_id = f"{user_id}_{datetime.now().isoformat()}"
            
            # Store conversation context
            self.active_conversations[conversation_id] = {
                "user_id": user_id,
                "message": message,
                "context": context or {},
                "started_at": datetime.now(),
                "status": "processing"
            }
            
            # Step 1: Coordinator analyzes the request
            logger.info(f"Processing message from user {user_id}: {message[:100]}...")
            analysis = await self.coordinator.analyze_request(message, context)
            
            if not analysis.get("success"):
                return {
                    "success": False,
                    "error": analysis.get("error", "Unknown error in analysis"),
                    "conversation_id": conversation_id
                }
            
            # Step 2: Route to appropriate agents
            agents_needed = analysis.get("agents_needed", ["general"])
            agent_responses = {}
            
            for agent_name in agents_needed:
                if agent_name in self.agents:
                    response = await self._route_to_agent(agent_name, message, context)
                    agent_responses[agent_name] = response
                else:
                    logger.warning(f"Agent {agent_name} not available, using fallback")
                    agent_responses[agent_name] = self._get_fallback_response(agent_name, message)
            
            # Step 3: Coordinator synthesizes responses
            final_response = await self.coordinator.coordinate_response(message, agent_responses)
            
            # Update conversation status
            self.active_conversations[conversation_id]["status"] = "completed"
            self.active_conversations[conversation_id]["response"] = final_response
            
            return {
                "success": True,
                "message": final_response,
                "agent_responses": agent_responses,
                "conversation_id": conversation_id,
                "agents_used": agents_needed
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": f"An error occurred while processing your request: {str(e)}",
                "conversation_id": conversation_id if 'conversation_id' in locals() else None
            }
    
    async def _route_to_agent(self, agent_name: str, message: str, context: Dict[str, Any]) -> str:
        """Route request to specific agent"""
        try:
            if agent_name == "planning" and self.planning_agent:
                # Determine if it's an event, task, or schedule optimization
                if any(keyword in message.lower() for keyword in ['event', 'meeting', 'appointment']):
                    result = await self.planning_agent.create_event({
                        "title": self._extract_event_title(message),
                        "description": message,
                        "context": context
                    })
                    return result.get("event_plan", "Event planned successfully")
                
                elif any(keyword in message.lower() for keyword in ['task', 'todo', 'remind']):
                    result = await self.planning_agent.manage_tasks(message, context.get("existing_tasks"))
                    return result.get("task_plan", "Task organized successfully")
                
                else:
                    result = await self.planning_agent.optimize_schedule(context.get("schedule_data", {}))
                    return result.get("analysis", "Schedule analyzed successfully")
            
            # TODO: Add routing for other agents
            # elif agent_name == "content" and self.content_agent:
            #     return await self.content_agent.generate_content(message, context)
            # elif agent_name == "integration" and self.integration_agent:
            #     return await self.integration_agent.handle_integration(message, context)
            # elif agent_name == "voice" and self.voice_agent:
            #     return await self.voice_agent.process_voice(message, context)
            
            else:
                return self._get_fallback_response(agent_name, message)
                
        except Exception as e:
            logger.error(f"Error routing to {agent_name}: {e}")
            return f"I encountered an error while processing your {agent_name} request. Please try again."
    
    def _extract_event_title(self, message: str) -> str:
        """Extract event title from message"""
        # Simple extraction - in production, use more sophisticated NLP
        words = message.split()
        if "meeting" in message.lower():
            return "Meeting"
        elif "appointment" in message.lower():
            return "Appointment"
        elif len(words) > 3:
            return " ".join(words[:3]).title()
        else:
            return "New Event"
    
    def _get_fallback_response(self, agent_name: str, message: str) -> str:
        """Provide fallback response when agent is not available"""
        fallbacks = {
            "planning": "I can help you with planning. Please provide more details about what you'd like to schedule or organize.",
            "content": "I can help with content creation. What would you like me to write or generate?",
            "integration": "I can help with integrations. What service would you like to connect with?",
            "voice": "I can help with voice processing. Please speak your request clearly.",
            "general": "I'm here to help! Could you please provide more details about what you need?"
        }
        return fallbacks.get(agent_name, fallbacks["general"])
    
    async def process_realtime_message(self, message: str, client_id: str) -> str:
        """Process real-time WebSocket messages"""
        try:
            result = await self.process_message(message, client_id)
            return result.get("message", "Sorry, I couldn't process that request.")
        except Exception as e:
            logger.error(f"Error in real-time processing: {e}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    async def get_active_agents_count(self) -> int:
        """Get count of active agents"""
        return len(self.agents) if self.initialized else 0
    
    def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        user_conversations = [
            conv for conv in self.active_conversations.values()
            if conv.get("user_id") == user_id
        ]
        return sorted(user_conversations, key=lambda x: x.get("started_at", datetime.min))
    
    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an event using the planning agent"""
        if not self.planning_agent:
            return {"success": False, "error": "Planning agent not available"}
        
        return await self.planning_agent.create_event(event_data)
    
    async def manage_tasks(self, task_request: str, existing_tasks: List[Dict] = None) -> Dict[str, Any]:
        """Manage tasks using the planning agent"""
        if not self.planning_agent:
            return {"success": False, "error": "Planning agent not available"}
        
        return await self.planning_agent.manage_tasks(task_request, existing_tasks) 