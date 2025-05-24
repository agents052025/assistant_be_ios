from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.core.database import Base

class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)
    configuration = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    user_id = Column(String(100), nullable=True)  # For user-specific configurations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "configuration": self.configuration,
            "is_active": self.is_active,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 