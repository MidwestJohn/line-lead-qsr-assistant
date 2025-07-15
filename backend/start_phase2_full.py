#!/usr/bin/env python3
"""
Phase 2 Full Startup Script
==========================

Start the backend server with both Phase 1 PydanticAI endpoints 
AND Phase 2 orchestrated multi-agent endpoints.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import sys

# Load environment FIRST before any other imports
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Now safe to import other modules
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

# Add backend to path
sys.path.append('.')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up environment
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'test-key')

# Create FastAPI app
app = FastAPI(
    title="Line Lead QSR MVP - Phase 2 Full",
    description="QSR Assistant with Full Multi-Agent Orchestration",
    version="2.0.0-phase2"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check
@app.get("/health")
async def health_check():
    """Basic health check"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0-phase2",
        "phase": "Phase 2 - Full Multi-Agent Orchestration"
    })

# Legacy chat endpoint (minimal)
class LegacyChatMessage(BaseModel):
    message: str
    conversation_id: str = "default"

@app.post("/chat")
async def legacy_chat(request: LegacyChatMessage):
    """Legacy chat endpoint - minimal implementation"""
    return JSONResponse(content={
        "response": f"Legacy response to: {request.message}",
        "timestamp": datetime.now().isoformat(),
        "conversation_id": request.conversation_id,
        "note": "This is a legacy endpoint. Use /chat/orchestrated for Phase 2 features."
    })

# Setup Phase 1 endpoints
phase1_loaded = False
try:
    from endpoints.pydantic_chat_endpoints import setup_pydantic_chat_endpoints
    
    # Setup PydanticAI endpoints
    pydantic_endpoints = setup_pydantic_chat_endpoints(app)
    logger.info("✅ Phase 1 PydanticAI endpoints loaded successfully")
    phase1_loaded = True
    
except Exception as e:
    logger.error(f"❌ Failed to load Phase 1 endpoints: {e}")

# Setup Phase 2 orchestrated endpoints
phase2_loaded = False
try:
    import sys
    import os
    
    # Add the backend directory to Python path for absolute imports
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    from endpoints.orchestrated_chat_endpoints import router as orchestrated_router
    
    # Include the orchestrated chat router
    app.include_router(orchestrated_router)
    logger.info("✅ Phase 2 Orchestrated endpoints loaded successfully")
    phase2_loaded = True
    
except Exception as e:
    logger.error(f"❌ Failed to load Phase 2 orchestrated endpoints: {e}")
    
    # Add placeholder endpoint
    @app.post("/chat/orchestrated")
    async def orchestrated_chat_placeholder(request: LegacyChatMessage):
        return JSONResponse(content={
            "error": "Phase 2 orchestrated endpoints not available",
            "message": f"Orchestrated endpoints failed to load: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, status_code=503)

# Enhanced test endpoint
@app.get("/test")
async def test_endpoint():
    """Test endpoint with Phase 2 status"""
    endpoints = [
        "/health - Health check",
        "/chat - Legacy chat",
    ]
    
    if phase1_loaded:
        endpoints.extend([
            "/chat/pydantic - Phase 1 PydanticAI chat",
            "/chat/pydantic/stream - Phase 1 streaming chat",
            "/chat/pydantic/health - Phase 1 agent health"
        ])
    
    if phase2_loaded:
        endpoints.extend([
            "/chat/orchestrated - Phase 2 orchestrated chat",
            "/chat/orchestrated/stream - Phase 2 streaming chat",
            "/chat/orchestrated/classify - Query classification",
            "/chat/orchestrated/health - Agent orchestrator health",
            "/chat/orchestrated/analytics/{conversation_id} - Analytics",
            "/chat/orchestrated/history/{conversation_id} - Chat history"
        ])
    
    return JSONResponse(content={
        "message": "Phase 2 Full backend is running",
        "timestamp": datetime.now().isoformat(),
        "phase1_loaded": phase1_loaded,
        "phase2_loaded": phase2_loaded,
        "endpoints": endpoints
    })

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Phase 2 Full Backend Server")
    print("=" * 60)
    print("Available endpoints:")
    print("  - GET  /health - Health check")
    print("  - GET  /test - Test endpoint with status")
    print("  - POST /chat - Legacy chat")
    
    if phase1_loaded:
        print("\n📊 Phase 1 - PydanticAI Integration:")
        print("  - POST /chat/pydantic - PydanticAI chat")
        print("  - POST /chat/pydantic/stream - Streaming chat")
        print("  - GET  /chat/pydantic/health - Agent health")
    
    if phase2_loaded:
        print("\n🎯 Phase 2 - Multi-Agent Orchestration:")
        print("  - POST /chat/orchestrated - Orchestrated chat")
        print("  - POST /chat/orchestrated/stream - Streaming orchestrated chat")
        print("  - POST /chat/orchestrated/classify - Query classification")
        print("  - GET  /chat/orchestrated/health - Orchestrator health")
        print("  - GET  /chat/orchestrated/analytics/{id} - Analytics")
        print("  - GET  /chat/orchestrated/history/{id} - Chat history")
    
    print("=" * 60)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)