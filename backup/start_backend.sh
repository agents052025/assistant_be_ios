#!/bin/bash

echo "🚀 Starting CrashCurse Backend..."

# Check if we're in the right directory
if [ ! -f "main_simple.py" ]; then
    echo "❌ Error: main_simple.py not found. Please run this script from the project root."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created."
fi

# Activate virtual environment with proper path handling
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated."
elif [ -f "venv/Scripts/activate" ]; then
    # Windows path
    source venv/Scripts/activate
    echo "✅ Virtual environment activated (Windows)."
else
    echo "❌ Error: Could not find activation script in virtual environment."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    if [ -f "env_example.txt" ]; then
        cp env_example.txt .env
        echo "✅ .env file created. You can edit it to add your API keys."
    else
        echo "⚠️  Warning: env_example.txt not found. Creating basic .env file."
        echo "# Add your environment variables here" > .env
        echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
    fi
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python -c "import fastapi, uvicorn, pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing required packages..."
    pip install --upgrade pip
    pip install fastapi 'uvicorn[standard]' pydantic sqlalchemy python-dotenv httpx websockets python-multipart aiofiles requests
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install required packages."
        exit 1
    fi
    echo "✅ Dependencies installed successfully."
else
    echo "✅ Dependencies already installed."
fi

# Start the backend
echo ""
echo "🔥 Starting backend in simple mode..."
echo "📡 Backend will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "❤️  Health Check: http://localhost:8000/health"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run the server
python main_simple.py 