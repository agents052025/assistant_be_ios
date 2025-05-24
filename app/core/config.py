from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./crashcurse.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # External Services
    CALENDAR_SERVICE_URL: Optional[str] = None
    EMAIL_SERVICE_URL: Optional[str] = None
    
    # Agent Configuration
    MAX_CONCURRENT_AGENTS: int = 5
    AGENT_TIMEOUT_SECONDS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 