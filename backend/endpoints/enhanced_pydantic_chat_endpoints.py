#!/usr/bin/env python3
"""
Enhanced PydanticAI Chat Endpoints with Ragie Integration
========================================================

Updated chat endpoints using the enhanced PydanticAI + Ragie orchestration.
Replaces basic endpoints with Ragie-powered knowledge retrieval and visual citations.

Features:
- Enhanced PydanticAI orchestration with Ragie knowledge
- Native streaming with visual citation coordination
- Multi-modal response handling (text + images + videos)
- QSR-optimized context management
- Production-ready error handling and fallbacks

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

# Import enhanced orchestration components
from agents.enhanced_qsr_orchestrator import get_enhanced_qsr_orchestrator
from services.enhanced_ragie_service import enhanced_ragie_service
from database.qsr_database import QSRDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced API models
class EnhancedChatRequest(BaseModel):
    """Enhanced request model for PydanticAI + Ragie chat endpoint"""
    message: str = Field(..., description="User message")
    conversation_id: str = Field(default="default", description="Conversation identifier")
    include_citations: bool = Field(default=True, description="Include visual citations")
    search_documents: bool = Field(default=True, description="Search documents with Ragie")
    user_location: Optional[str] = Field(default=None, description="User location for context")
    equipment_context: Optional[str] = Field(default=None, description="Current equipment context")
    max_citations: int = Field(default=5, description="Maximum visual citations to include")

class EnhancedChatResponse(BaseModel):
    """Enhanced response model with Ragie integration"""
    response: str = Field(description="Assistant response text")
    agent_used: str = Field(description="Agent that handled the query")
    confidence: float = Field(description="Response confidence score")
    processing_time: float = Field(description="Processing time in seconds")
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list, description="Visual citations from Ragie")
    equipment_mentioned: List[str] = Field(default_factory=list, description="Equipment mentioned")
    safety_warnings: List[str] = Field(default_factory=list, description="Safety warnings")
    conversation_id: str = Field(description="Conversation identifier")
    ragie_enhanced: bool = Field(default=False, description="Whether response was enhanced with Ragie")
    context_updates: Dict[str, Any] = Field(default_factory=dict, description="Context updates")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class StreamingChatChunk(BaseModel):
    """Model for streaming chat chunks"""
    type: str = Field(description="Chunk type: 'text', 'citation', 'metadata'")
    content: str = Field(default="", description="Chunk content")
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list, description="Visual citations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    complete: bool = Field(default=False, description="Whether this is the final chunk")

def setup_enhanced_pydantic_chat_endpoints(app: FastAPI):
    """Setup enhanced PydanticAI + Ragie chat endpoints"""
    
    @app.post("/chat/enhanced", response_model=EnhancedChatResponse)
    async def enhanced_chat(
        request: EnhancedChatRequest,
        http_request: Request
    ):
        """
        Enhanced chat endpoint with PydanticAI orchestration and Ragie knowledge
        
        Features:
        - Intelligent agent routing based on query classification
        - Ragie-powered knowledge retrieval with visual citations
        - Context-aware conversation management
        - Multi-modal response coordination
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Enhanced chat request: {request.message[:100]}...")
            
            # Get enhanced orchestrator
            orchestrator = await get_enhanced_qsr_orchestrator()
            
            # Process query with enhanced orchestration
            orchestrator_response = await orchestrator.handle_query(
                query=request.message,
                conversation_id=request.conversation_id,
                context={
                    "equipment_context": request.equipment_context,
                    "user_location": request.user_location,
                    "include_citations": request.include_citations
                }
            )
            
            # Create enhanced response
            response = EnhancedChatResponse(
                response=orchestrator_response.response,
                agent_used=orchestrator_response.agent_used,
                confidence=orchestrator_response.confidence,
                processing_time=orchestrator_response.processing_time,
                visual_citations=orchestrator_response.visual_citations[:request.max_citations],
                conversation_id=request.conversation_id,
                ragie_enhanced=len(orchestrator_response.visual_citations) > 0,
                context_updates=orchestrator_response.context_updates,
                metadata=orchestrator_response.metadata
            )
            
            # Extract additional response data
            if "equipment_mentioned" in orchestrator_response.metadata:
                response.equipment_mentioned = orchestrator_response.metadata["equipment_mentioned"]
            if "safety_warnings" in orchestrator_response.metadata:
                response.safety_warnings = orchestrator_response.metadata["safety_warnings"]
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Enhanced chat completed in {processing_time:.2f}s with {len(response.visual_citations)} citations")
            
            return response
            
        except Exception as e:
            logger.error(f"Enhanced chat error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Return error response
            return EnhancedChatResponse(
                response="I encountered an issue processing your request. Please try again.",
                agent_used="error_handler",
                confidence=0.1,
                processing_time=processing_time,
                conversation_id=request.conversation_id,
                ragie_enhanced=False,
                metadata={"error": str(e)}
            )
    
    @app.post("/chat/enhanced/stream")
    async def enhanced_chat_stream(
        request: EnhancedChatRequest,
        http_request: Request
    ):
        """
        Enhanced streaming chat endpoint with coordinated visual citations
        
        Streams response text while coordinating visual citations timing
        for optimal user experience.
        """
        
        async def generate_enhanced_stream():
            try:
                logger.info(f"🌊 Enhanced streaming chat: {request.message[:100]}...")
                
                # Get enhanced orchestrator
                orchestrator = await get_enhanced_qsr_orchestrator()
                
                # Start processing
                yield json.dumps({
                    "type": "metadata",
                    "content": "",
                    "metadata": {"status": "processing", "agent": "routing"},
                    "complete": False
                }) + "\n"
                
                # Process with orchestrator
                orchestrator_response = await orchestrator.handle_query(
                    query=request.message,
                    conversation_id=request.conversation_id,
                    context={
                        "equipment_context": request.equipment_context,
                        "user_location": request.user_location,
                        "include_citations": request.include_citations
                    }
                )
                
                # Stream response text with visual citation coordination
                response_text = orchestrator_response.response
                visual_citations = orchestrator_response.visual_citations
                
                # Send agent info
                yield json.dumps({
                    "type": "metadata",
                    "content": "",
                    "metadata": {
                        "agent_used": orchestrator_response.agent_used,
                        "confidence": orchestrator_response.confidence,
                        "ragie_enhanced": len(visual_citations) > 0
                    },
                    "complete": False
                }) + "\n"
                
                # Stream text in chunks with debouncing
                chunk_size = 50
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    
                    yield json.dumps({
                        "type": "text",
                        "content": chunk,
                        "metadata": {"chunk_index": i // chunk_size},
                        "complete": False
                    }) + "\n"
                    
                    # Small delay for smooth streaming
                    await asyncio.sleep(0.05)
                
                # Send visual citations after text completion
                if visual_citations and request.include_citations:
                    yield json.dumps({
                        "type": "citation",
                        "content": "",
                        "visual_citations": visual_citations[:request.max_citations],
                        "metadata": {"citation_count": len(visual_citations)},
                        "complete": False
                    }) + "\n"
                
                # Final completion chunk
                yield json.dumps({
                    "type": "metadata",
                    "content": "",
                    "metadata": {
                        "status": "complete",
                        "processing_time": orchestrator_response.processing_time,
                        "context_updates": orchestrator_response.context_updates
                    },
                    "complete": True
                }) + "\n"
                
                logger.info(f"✅ Enhanced streaming completed with {len(visual_citations)} citations")
                
            except Exception as e:
                logger.error(f"Enhanced streaming error: {e}")
                yield json.dumps({
                    "type": "error",
                    "content": "An error occurred during processing.",
                    "metadata": {"error": str(e)},
                    "complete": True
                }) + "\n"
        
        return StreamingResponse(
            generate_enhanced_stream(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    @app.get("/chat/enhanced/status")
    async def enhanced_chat_status():
        """Get enhanced chat system status"""
        try:
            # Check orchestrator status
            orchestrator = await get_enhanced_qsr_orchestrator()
            performance_metrics = orchestrator.get_performance_metrics()
            
            # Check Ragie service status
            ragie_status = {
                "available": enhanced_ragie_service.is_available(),
                "partition": enhanced_ragie_service.partition if enhanced_ragie_service.is_available() else None
            }
            
            return JSONResponse(content={
                "status": "healthy",
                "enhanced_orchestrator": "active",
                "ragie_integration": ragie_status,
                "performance_metrics": performance_metrics,
                "features": {
                    "agent_routing": True,
                    "visual_citations": True,
                    "context_awareness": True,
                    "streaming_support": True
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Enhanced status check failed: {e}")
            return JSONResponse(
                content={
                    "status": "degraded",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                status_code=503
            )
    
    @app.post("/chat/enhanced/upload")
    async def enhanced_upload_document(
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Upload document to enhanced Ragie service"""
        try:
            result = await enhanced_ragie_service.upload_document(file_path, metadata)
            
            if result.success:
                return JSONResponse(content={
                    "success": True,
                    "document_id": result.document_id,
                    "filename": result.filename,
                    "chunk_count": result.chunk_count,
                    "page_count": result.page_count,
                    "qsr_metadata": result.qsr_metadata
                })
            else:
                return JSONResponse(
                    content={"success": False, "error": result.error},
                    status_code=400
                )
                
        except Exception as e:
            logger.error(f"Enhanced upload failed: {e}")
            return JSONResponse(
                content={"success": False, "error": str(e)},
                status_code=500
            )

    logger.info("✅ Enhanced PydanticAI + Ragie chat endpoints configured")