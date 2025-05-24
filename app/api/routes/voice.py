from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/process")
async def process_voice():
    """
    Process voice input - placeholder for voice processing agent
    """
    return {
        "success": True,
        "message": "Voice processing not implemented yet",
        "transcription": "",
        "response": ""
    }

@router.get("/status")
async def get_voice_status():
    """
    Get voice service status
    """
    return {
        "success": True,
        "status": "voice_service_ready"
    } 