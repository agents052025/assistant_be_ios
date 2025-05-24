from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.core.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String(50), default="text")
    agent_id = Column(String(100), nullable=True)
    is_sender_user = Column(Boolean, default=False)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "type": self.type,
            "agent_id": self.agent_id,
            "is_sender_user": self.is_sender_user
        } 