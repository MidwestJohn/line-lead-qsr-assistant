#!/bin/bash
# Phase 1 Staging Startup Script

echo "🚀 Starting Phase 1 Staging Environment"
echo "======================================"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✅ Virtual environment found"
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found"
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check for required packages
echo "📦 Checking requirements..."
python3 -c "import pydantic_ai; print('✅ PydanticAI available')" 2>/dev/null || {
    echo "❌ PydanticAI not available - installing..."
    pip install pydantic-ai[openai]
}

# Set environment variables
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export QSR_MODEL="${QSR_MODEL:-openai:gpt-4o}"
export DATABASE_PATH="${DATABASE_PATH:-staging_qsr_conversations.sqlite}"

# Start backend
echo "🔧 Starting backend server..."
python3 main.py &
BACKEND_PID=$!

echo "✅ Phase 1 staging environment started"
echo "Backend PID: $BACKEND_PID"
echo "Available endpoints:"
echo "  - /chat/pydantic (Phase 1 standard chat)"
echo "  - /chat/pydantic/stream (Phase 1 streaming chat)"
echo "  - /chat/pydantic/health (Phase 1 health check)"
echo "  - /chat (Legacy chat endpoint)"
echo "  - /chat/stream (Legacy streaming endpoint)"

# Wait for backend to start
sleep 3

# Test Phase 1 endpoints
echo "🧪 Testing Phase 1 endpoints..."
curl -s http://localhost:8000/chat/pydantic/health | jq . || echo "❌ Health check failed"

echo "======================================"
echo "Phase 1 staging environment ready!"
echo "Press Ctrl+C to stop"

# Wait for interrupt
wait $BACKEND_PID
