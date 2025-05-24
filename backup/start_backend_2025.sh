#!/bin/bash

# 🚀 CrashCurse AI Backend 2025 Startup Script
# Modern CrewAI 0.121.0 with Flows + Crews architecture

echo "🚀 Starting CrashCurse AI Backend 2025..."
echo "Framework: CrewAI 0.121.0 (Standalone, no LangChain dependency)"
echo "Features: Flows + Crews, iOS optimized, WebSocket support"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating basic .env file..."
    cat > .env << EOF
# OpenAI API Key (required for AI functionality)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Serper API for web search
SERPER_API_KEY=your_serper_api_key_here

# CrewAI Settings
CREWAI_TELEMETRY_OPT_OUT=true
OTEL_SDK_DISABLED=true
EOF
    echo "✏️  Please edit .env file and add your API keys"
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required dependencies
echo "🔍 Checking dependencies..."
python -c "import crewai; print(f'CrewAI version: {crewai.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ CrewAI not installed!"
    echo "Installing CrewAI 2025..."
    pip install crewai==0.121.0 crewai-tools==0.45.0
fi

# Check API key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "⚠️  OPENAI_API_KEY not configured!"
    echo "The backend will start but AI features may not work"
    echo "Please set your OpenAI API key in .env file"
    echo ""
fi

# Show system info
echo "📊 System Information:"
echo "Python: $(python --version)"
echo "FastAPI: $(python -c 'import fastapi; print(fastapi.__version__)' 2>/dev/null || echo 'Not installed')"
echo "CrewAI: $(python -c 'import crewai; print(crewai.__version__)' 2>/dev/null || echo 'Not installed')"
echo "Uvicorn: $(python -c 'import uvicorn; print(uvicorn.__version__)' 2>/dev/null || echo 'Not installed')"
echo ""

# Show network info
echo "🌐 Network Configuration:"
echo "Server: http://localhost:8000"
echo "WebSocket: ws://localhost:8000/ws"
echo "iOS App should connect to these endpoints"
echo ""

# Start the backend
echo "🚀 Starting CrashCurse AI Backend 2025..."
echo "Press Ctrl+C to stop"
echo "=================================="

python main_crewai_2025.py 