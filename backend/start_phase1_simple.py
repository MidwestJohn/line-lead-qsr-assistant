#!/usr/bin/env python3
"""
Simple Phase 1 Startup Script
=============================

Start the backend server with Phase 1 PydanticAI endpoints only,
bypassing complex startup dependencies.

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
    title="Line Lead QSR MVP - Phase 1",
    description="QSR Assistant with PydanticAI Integration",
    version="2.0.0-phase1"
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
        "version": "2.0.0-phase1",
        "phase": "Phase 1 - PydanticAI Integration"
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
        "note": "This is a legacy endpoint. Use /chat/pydantic for Phase 1 features."
    })

# Setup Phase 1 endpoints
try:
    from endpoints.pydantic_chat_endpoints import setup_pydantic_chat_endpoints
    
    # Setup PydanticAI endpoints
    pydantic_endpoints = setup_pydantic_chat_endpoints(app)
    logger.info("✅ Phase 1 PydanticAI endpoints loaded successfully")
    
except Exception as e:
    logger.error(f"❌ Failed to load Phase 1 endpoints: {e}")
    
    # Add placeholder endpoints
    @app.post("/chat/pydantic")
    async def pydantic_chat_placeholder(request: LegacyChatMessage):
        return JSONResponse(content={
            "error": "Phase 1 endpoints not available",
            "message": f"PydanticAI endpoints failed to load: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, status_code=503)

# Test endpoint
@app.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return JSONResponse(content={
        "message": "Phase 1 backend is running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/health - Health check",
            "/chat - Legacy chat",
            "/chat/pydantic - Phase 1 PydanticAI chat",
            "/chat/pydantic/stream - Phase 1 streaming chat",
            "/chat/pydantic/health - Phase 1 agent health"
        ]
    })

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Phase 1 Simple Backend Server")
    print("=" * 50)
    print("Available endpoints:")
    print("  - GET  /health - Health check")
    print("  - GET  /test - Test endpoint")
    print("  - POST /chat - Legacy chat")
    print("  - POST /chat/pydantic - Phase 1 PydanticAI chat")
    print("  - POST /chat/pydantic/stream - Phase 1 streaming chat")
    print("  - GET  /chat/pydantic/health - Phase 1 agent health")
    print("=" * 50)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)