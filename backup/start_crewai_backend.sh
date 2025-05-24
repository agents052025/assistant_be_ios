#!/bin/bash

# CrashCurse AI Assistant - CrewAI Backend Startup Script
echo "🚀 Starting CrashCurse CrewAI Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create it first:"
    echo "python -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "📦 Checking dependencies..."
python -c "import crewai, fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Some dependencies missing. Installing..."
    pip install -r requirements.txt
fi

# Set environment variables
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
export DEBUG=${DEBUG:-True}

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    if [ -f "env_example.txt" ]; then
        cp env_example.txt .env
        echo "✅ Created .env from env_example.txt"
    else
        echo "# CrashCurse Environment Variables" > .env
        echo "HOST=0.0.0.0" >> .env
        echo "PORT=8000" >> .env
        echo "DEBUG=True" >> .env
        echo "✅ Created basic .env file"
    fi
fi

# Create app directories if they don't exist
echo "📁 Ensuring directory structure..."
mkdir -p app/agents
mkdir -p app/api/routes
mkdir -p app/core
mkdir -p app/models
mkdir -p app/services

# Start the CrewAI backend
echo "🎯 Starting CrewAI multi-agent backend on http://${HOST}:${PORT}"
echo "🤖 Agents: Coordinator | Planning | Content | Integration | Voice"
echo ""
echo "📋 Available endpoints:"
echo "  - POST /api/v1/chat/send - Send message to AI agents"
echo "  - POST /api/v1/planning/events - Create calendar events"
echo "  - POST /api/v1/planning/reminders - Create reminders"
echo "  - POST /api/v1/content/generate - Generate content"
echo "  - GET /api/v1/agents/status - Check agent status"
echo "  - WebSocket /ws/{client_id} - Real-time chat"
echo ""
echo "🔗 API Documentation: http://${HOST}:${PORT}/docs"
echo ""

# Check for Python version
python_version=$(python --version 2>&1)
echo "🐍 Using: $python_version"

# Start the server
python main_crewai.py 