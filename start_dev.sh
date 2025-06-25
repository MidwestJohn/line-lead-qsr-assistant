#!/bin/bash

# Start both React frontend and FastAPI backend

echo "Starting Line Lead QSR MVP Development Servers..."

# Start FastAPI backend in background
echo "Starting FastAPI backend on port 8000..."
cd "$(dirname "$0")"
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start React frontend in background
echo "Starting React frontend on port 3000..."
npm start > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "✅ Services started:"
echo "   - FastAPI Backend: http://localhost:8000"
echo "   - React Frontend: http://localhost:3000"
echo "   - Network Access: http://$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}'):3000"
echo ""
echo "📱 iPhone Access: http://$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}'):3000"
echo ""
echo "🛑 To stop all services: kill $BACKEND_PID $FRONTEND_PID"
echo "📝 Logs:"
echo "   - Backend: tail -f backend.log"
echo "   - Frontend: tail -f frontend.log"

# Keep script running
wait