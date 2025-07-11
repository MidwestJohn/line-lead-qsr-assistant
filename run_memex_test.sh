#!/bin/bash

# Memex Complete System Test Runner
# This script runs the complete test sequence with enhanced logging

echo "🧪 MEMEX COMPLETE SYSTEM TEST RUNNER"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "backend/run_complete_test.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'python -m venv .venv' first"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if required packages are installed
echo "🔍 Checking required packages..."
python -c "import asyncio, logging, json, time, requests; print('✅ Core packages available')" 2>/dev/null || {
    echo "❌ Required packages not installed. Please install requirements."
    exit 1
}

# Check environment variables
echo "🔍 Checking environment variables..."
if [ ! -f "backend/.env.rag" ]; then
    echo "❌ Environment file .env.rag not found"
    exit 1
fi

# Start backend in background if not running
echo "🚀 Starting backend services..."
cd backend

# Check if backend is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend already running"
else
    echo "🔄 Starting FastAPI backend..."
    nohup python main.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Backend is ready"
            break
        fi
        sleep 1
    done
    
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "❌ Backend failed to start"
        exit 1
    fi
fi

# Run the complete test
echo ""
echo "🧪 STARTING COMPLETE SYSTEM TEST"
echo "================================"
echo ""

python run_complete_test.py

TEST_EXIT_CODE=$?

# Show results
echo ""
echo "📊 TEST RESULTS"
echo "==============="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "🎉 COMPLETE SYSTEM TEST PASSED!"
    echo "✅ System is ready for production"
    echo ""
    echo "📋 Generated Files:"
    echo "- Pipeline diagnostic logs"
    echo "- Test metrics and results"
    echo "- Comprehensive test report"
    echo ""
    echo "🌐 You can now:"
    echo "- View Neo4j data at http://localhost:7474"
    echo "- Access API at http://localhost:8000"
    echo "- Upload documents via API or frontend"
else
    echo "❌ COMPLETE SYSTEM TEST FAILED"
    echo "⚠️  Check logs for detailed error information"
    echo ""
    echo "📋 Debug Files:"
    echo "- backend/pipeline_diagnostic.log"
    echo "- backend/backend.log"
    echo "- Test reports in backend/"
fi

# Clean up
echo ""
echo "🧹 Cleaning up..."
cd ..

echo "Test completed. Exit code: $TEST_EXIT_CODE"
exit $TEST_EXIT_CODE