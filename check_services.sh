#!/bin/bash

echo "🔍 Checking Line Lead QSR MVP Services..."
echo ""

# Check Backend
echo "🔧 Backend (FastAPI):"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ Backend is running on http://localhost:8000"
    echo "   📊 Health: $(curl -s http://localhost:8000/health | jq -r .status 2>/dev/null || echo "healthy")"
else
    echo "   ❌ Backend is not responding"
fi

echo ""

# Check Frontend
echo "🎨 Frontend (React):"
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Frontend is running on http://localhost:3000"
else
    echo "   ❌ Frontend is not responding"
fi

echo ""

# Network info
IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo "📱 Mobile Access: http://$IP:3000"
echo ""

# Running processes
echo "🔄 Running Processes:"
ps aux | grep -E "(uvicorn|react-scripts)" | grep -v grep | while read line; do
    echo "   📋 $line"
done