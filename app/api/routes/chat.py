from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from app.services.crew_manager import CrewManager
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
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
    agents_used: Optional[list] = None

class ChatHistoryResponse(BaseModel):
    success: bool
    messages: list
    total_count: int

# Initialize crew manager (in production, this would be dependency injected)
crew_manager = CrewManager()

@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message to the AI assistant system
    This endpoint matches the iOS NetworkService.sendMessage() function
    """
    try:
        logger.info(f"Received chat message from user {request.user_id}: {request.message[:100]}...")
        
        # Process message through CrewAI system
        result = await crew_manager.process_message(
            message=request.message,
            user_id=request.user_id,
            context=request.context
        )
        
        if result.get("success"):
            return ChatResponse(
                success=True,
                message=result["message"],
                agent_id=result.get("agents_used", ["general"])[0],  # Primary agent used
                conversation_id=result.get("conversation_id"),
                agents_used=result.get("agents_used")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error occurred")
            )
            
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}", response_model=ChatHistoryResponse)
async def get_chat_history(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """
    Get chat history for a user
    This endpoint matches the iOS NetworkService.fetchChatHistory() function
    """
    try:
        # Get conversation history from crew manager
        conversations = crew_manager.get_conversation_history(user_id)
        
        # Format for response (limit results)
        messages = []
        for conv in conversations[-limit:]:
            messages.append({
                "content": conv.get("message", ""),
                "timestamp": conv.get("started_at", datetime.now()).isoformat(),
                "is_sender_user": True,  # Original message
                "agent_id": None
            })
            
            if conv.get("response"):
                messages.append({
                    "content": conv["response"],
                    "timestamp": conv.get("started_at", datetime.now()).isoformat(),
                    "is_sender_user": False,  # AI response
                    "agent_id": "assistant"
                })
        
        return ChatHistoryResponse(
            success=True,
            messages=messages,
            total_count=len(messages)
        )
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_system_status():
    """
    Get the current status of the AI assistant system
    """
    try:
        agent_count = await crew_manager.get_active_agents_count()
        
        return {
            "success": True,
            "status": "active",
            "active_agents": agent_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/feedback")
async def submit_feedback(
    conversation_id: str,
    rating: int,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Submit feedback for a conversation
    """
    try:
        # In a production system, you'd store this feedback in the database
        # For now, just log it
        logger.info(f"Feedback received for conversation {conversation_id}: Rating {rating}, Feedback: {feedback}")
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{user_id}")
async def clear_chat_history(user_id: str, db: Session = Depends(get_db)):
    """
    Clear chat history for a user
    """
    try:
        # Clear from crew manager
        if user_id in crew_manager.active_conversations:
            # Remove user's conversations
            conversations_to_remove = [
                conv_id for conv_id, conv in crew_manager.active_conversations.items()
                if conv.get("user_id") == user_id
            ]
            
            for conv_id in conversations_to_remove:
                del crew_manager.active_conversations[conv_id]
        
        return {
            "success": True,
            "message": "Chat history cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 