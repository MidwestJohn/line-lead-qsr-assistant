#!/usr/bin/env python3
"""
Safe Enhanced Chat Endpoints
============================

Low-risk chat endpoints that enhance the existing clean PydanticAI orchestration
with optional Ragie knowledge while maintaining simplicity and reliability.

Features:
- Uses existing proven QSR orchestrator
- Adds Ragie enhancement as optional pre-processing
- Maintains <3s response time targets
- 100% reliability with graceful fallbacks
- Easy to disable Ragie without affecting core functionality

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

# Import existing proven components
from agents.qsr_orchestrator import get_qsr_orchestrator  # Use existing clean orchestrator
from services.safe_ragie_enhancement import safe_ragie_enhancement, enhance_query_for_orchestrator

# Configure logging
logger = logging.getLogger(__name__)

# Simple API models (avoid over-engineering)
class SafeEnhancedChatRequest(BaseModel):
    """Simple request model for safe enhanced chat"""
    message: str = Field(..., description="User message")
    conversation_id: str = Field(default="default", description="Conversation identifier")
    enable_ragie: bool = Field(default=True, description="Enable Ragie enhancement (can disable)")
    include_citations: bool = Field(default=True, description="Include visual citations")

class SafeEnhancedChatResponse(BaseModel):
    """Simple response model with optional enhancements"""
    response: str = Field(description="Assistant response text")
    agent_used: str = Field(description="Agent that handled the query")
    conversation_id: str = Field(description="Conversation identifier")
    
    # Enhancement data (optional)
    ragie_enhanced: bool = Field(default=False, description="Whether Ragie enhancement was used")
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list, description="Visual citations if available")
    equipment_context: Optional[str] = Field(default=None, description="Detected equipment context")
    procedure_context: Optional[str] = Field(default=None, description="Detected procedure context")
    
    # Performance data
    total_processing_time: float = Field(description="Total processing time")
    ragie_processing_time: float = Field(default=0.0, description="Time spent on Ragie enhancement")
    orchestrator_processing_time: float = Field(description="Time spent on orchestration")

def setup_safe_enhanced_chat_endpoints(app: FastAPI):
    """Setup safe enhanced chat endpoints with existing orchestrator"""
    
    @app.post("/chat/safe-enhanced", response_model=SafeEnhancedChatResponse)
    async def safe_enhanced_chat(
        request: SafeEnhancedChatRequest,
        http_request: Request
    ):
        """
        Safe enhanced chat endpoint
        
        Enhances existing clean PydanticAI orchestration with optional Ragie knowledge.
        Maintains reliability and performance while adding value when possible.
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Safe enhanced chat: {request.message[:100]}...")
            
            # Step 1: Optional Ragie enhancement (with timeout protection)
            ragie_result = None
            if request.enable_ragie:
                try:
                    ragie_result = await enhance_query_for_orchestrator(
                        request.message, 
                        request.conversation_id
                    )
                    logger.info(f"✅ Ragie enhancement: {ragie_result['ragie_enhanced']} in {ragie_result['processing_time']:.2f}s")
                except Exception as e:
                    logger.warning(f"⚠️ Ragie enhancement failed, continuing without: {e}")
                    ragie_result = None
            
            # Step 2: Use existing proven orchestrator
            orchestrator = await get_qsr_orchestrator()
            orchestrator_start = datetime.now()
            
            # Use enhanced query if available, otherwise use original
            query_to_process = ragie_result["query"] if ragie_result else request.message
            
            orchestrator_response = await orchestrator.handle_query(
                query=query_to_process,
                conversation_id=request.conversation_id
            )
            
            orchestrator_time = (datetime.now() - orchestrator_start).total_seconds()
            total_time = (datetime.now() - start_time).total_seconds()
            
            # Step 3: Combine results
            response = SafeEnhancedChatResponse(
                response=orchestrator_response.response,
                agent_used=orchestrator_response.agent_used.value,
                conversation_id=request.conversation_id,
                total_processing_time=total_time,
                orchestrator_processing_time=orchestrator_time
            )
            
            # Add Ragie enhancements if available
            if ragie_result:
                response.ragie_enhanced = ragie_result["ragie_enhanced"]
                response.ragie_processing_time = ragie_result["processing_time"]
                
                if request.include_citations:
                    response.visual_citations = ragie_result["visual_citations"]
                
                response.equipment_context = ragie_result["equipment_context"]
                response.procedure_context = ragie_result["procedure_context"]
            
            # Performance logging
            if total_time > 3.0:
                logger.warning(f"⏱️ Response time {total_time:.2f}s exceeds 3s target")
            else:
                logger.info(f"✅ Response completed in {total_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Safe enhanced chat error: {e}")
            total_time = (datetime.now() - start_time).total_seconds()
            
            # Simple error response
            return SafeEnhancedChatResponse(
                response="I encountered an issue processing your request. Please try again.",
                agent_used="error_handler",
                conversation_id=request.conversation_id,
                total_processing_time=total_time,
                orchestrator_processing_time=0.0
            )
    
    @app.post("/chat/safe-enhanced/stream")
    async def safe_enhanced_chat_stream(
        request: SafeEnhancedChatRequest,
        http_request: Request
    ):
        """
        Safe enhanced streaming chat
        
        Simple streaming approach:
        1. Do Ragie enhancement (if enabled)
        2. Process with orchestrator
        3. Stream the complete response
        
        No complex coordination - keep it simple and reliable.
        """
        
        async def generate_safe_stream():
            try:
                start_time = datetime.now()
                
                # Send processing status
                yield json.dumps({
                    "type": "status",
                    "content": "Processing your request...",
                    "complete": False
                }) + "\n"
                
                # Step 1: Optional Ragie enhancement
                ragie_result = None
                if request.enable_ragie:
                    yield json.dumps({
                        "type": "status", 
                        "content": "Searching knowledge base...",
                        "complete": False
                    }) + "\n"
                    
                    try:
                        ragie_result = await enhance_query_for_orchestrator(
                            request.message, 
                            request.conversation_id
                        )
                    except Exception as e:
                        logger.warning(f"Ragie enhancement failed in streaming: {e}")
                
                # Step 2: Process with orchestrator
                yield json.dumps({
                    "type": "status",
                    "content": "Generating response...", 
                    "complete": False
                }) + "\n"
                
                orchestrator = await get_qsr_orchestrator()
                query_to_process = ragie_result["query"] if ragie_result else request.message
                
                orchestrator_response = await orchestrator.handle_query(
                    query=query_to_process,
                    conversation_id=request.conversation_id
                )
                
                # Step 3: Stream the response text
                response_text = orchestrator_response.response
                chunk_size = 50
                
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    yield json.dumps({
                        "type": "text",
                        "content": chunk,
                        "complete": False
                    }) + "\n"
                    await asyncio.sleep(0.03)  # Smooth streaming
                
                # Step 4: Send visual citations if available
                if ragie_result and ragie_result["visual_citations"] and request.include_citations:
                    yield json.dumps({
                        "type": "citations",
                        "content": "",
                        "visual_citations": ragie_result["visual_citations"],
                        "complete": False
                    }) + "\n"
                
                # Step 5: Final completion
                total_time = (datetime.now() - start_time).total_seconds()
                yield json.dumps({
                    "type": "complete",
                    "content": "",
                    "metadata": {
                        "agent_used": orchestrator_response.agent_used.value,
                        "total_time": total_time,
                        "ragie_enhanced": ragie_result["ragie_enhanced"] if ragie_result else False
                    },
                    "complete": True
                }) + "\n"
                
            except Exception as e:
                logger.error(f"Safe streaming error: {e}")
                yield json.dumps({
                    "type": "error",
                    "content": "An error occurred while processing your request.",
                    "complete": True
                }) + "\n"
        
        return StreamingResponse(
            generate_safe_stream(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache"}
        )
    
    @app.get("/chat/safe-enhanced/status")
    async def safe_enhanced_status():
        """Get safe enhanced chat system status"""
        try:
            # Check orchestrator
            orchestrator = await get_qsr_orchestrator()
            orchestrator_metrics = orchestrator.get_performance_metrics()
            
            # Check Ragie enhancement
            ragie_stats = safe_ragie_enhancement.get_enhancement_stats()
            
            return JSONResponse(content={
                "status": "healthy",
                "architecture": "safe_enhanced",
                "orchestrator": {
                    "available": True,
                    "metrics": orchestrator_metrics
                },
                "ragie_enhancement": ragie_stats,
                "performance_targets": {
                    "total_response_time": "<3 seconds",
                    "ragie_timeout": "2 seconds",
                    "reliability": "100% (works without Ragie)"
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return JSONResponse(
                content={"status": "error", "error": str(e)},
                status_code=503
            )
    
    logger.info("✅ Safe enhanced chat endpoints configured")