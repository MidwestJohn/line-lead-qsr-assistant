#!/usr/bin/env python3
"""
Orchestrated Chat Endpoints - Phase 2 Implementation
===================================================

FastAPI endpoints that use the QSR Agent Orchestrator for intelligent
multi-agent chat interactions. Provides both standard and streaming
chat with automatic agent selection and routing.

Features:
- Intelligent agent routing based on query content
- Streaming responses with orchestration metadata
- Context preservation across agent handoffs
- Performance monitoring and analytics
- Enhanced Ragie integration per agent

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

# Import orchestrator and database
from ..agents.qsr_orchestrator import QSROrchestrator
from ..agents.types import AgentType, QueryClassification, OrchestratorResponse
from ..production_system import ProductionTranslationLayer, get_production_layer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router for orchestrated chat endpoints
router = APIRouter(prefix="/chat/orchestrated", tags=["Orchestrated Chat"])

# Global orchestrator instance (initialized on first use)
_orchestrator: Optional[QSROrchestrator] = None
_production_layer: Optional[ProductionTranslationLayer] = None


async def get_orchestrator() -> QSROrchestrator:
    """Get or initialize the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        logger.info("Initializing QSR Orchestrator...")
        _orchestrator = await QSROrchestrator.create(
            model=os.getenv("OPENAI_MODEL", "openai:gpt-4o"),
            enable_fallback=True,
            enable_handoffs=True,
            performance_tracking=True
        )
        logger.info("QSR Orchestrator initialized successfully")
    return _orchestrator


async def get_production_layer_instance() -> ProductionTranslationLayer:
    """Get or initialize the global production layer instance"""
    global _production_layer
    if _production_layer is None:
        logger.info("Initializing Production Translation Layer...")
        _production_layer = await get_production_layer()
        logger.info("Production Translation Layer initialized successfully")
    
    return _production_layer


# Request/Response Models

class OrchestratedChatRequest(BaseModel):
    """Request model for orchestrated chat"""
    message: str = Field(description="User's message")
    conversation_id: str = Field(default="default", description="Conversation identifier")
    include_citations: bool = Field(default=True, description="Include document citations")
    search_documents: bool = Field(default=True, description="Search uploaded documents")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    preferred_agent: Optional[AgentType] = Field(default=None, description="Preferred agent type (optional)")
    enable_handoffs: bool = Field(default=True, description="Allow agent handoffs")


class OrchestratedChatResponse(BaseModel):
    """Response model for orchestrated chat"""
    response: str = Field(description="AI response content")
    conversation_id: str = Field(description="Conversation identifier")
    agent_used: AgentType = Field(description="Which agent handled the query")
    classification: QueryClassification = Field(description="How the query was classified")
    performance_metrics: Dict[str, Any] = Field(description="Performance data")
    context_preserved: bool = Field(description="Whether context was preserved")
    handoff_occurred: bool = Field(description="Whether agent handoff occurred")
    message_id: int = Field(description="Database message ID")
    timestamp: str = Field(description="Response timestamp")


class AgentHealthResponse(BaseModel):
    """Response model for agent health status"""
    status: str = Field(description="Overall health status")
    orchestrator: Dict[str, Any] = Field(description="Orchestrator health data")
    agents: Dict[str, Any] = Field(description="Individual agent health data")
    timestamp: str = Field(description="Health check timestamp")


class QueryClassificationResponse(BaseModel):
    """Response model for query classification"""
    classification: QueryClassification = Field(description="Classification results")
    reasoning: str = Field(description="Detailed reasoning")
    timestamp: str = Field(description="Classification timestamp")


# Chat Endpoints

@router.post("/", response_model=OrchestratedChatResponse)
async def orchestrated_chat(
    request: OrchestratedChatRequest,
    background_tasks: BackgroundTasks
) -> OrchestratedChatResponse:
    """
    Handle chat using the intelligent agent orchestrator.
    
    Routes queries to appropriate specialist agents based on content analysis.
    """
    try:
        # Get orchestrator and database
        orchestrator = await get_orchestrator()
        database = await get_database()
        
        # Get conversation history
        conversation_history = await database.get_conversation_history(
            request.conversation_id,
            limit=10
        )
        
        # Convert to ModelMessage format
        message_history = []
        for msg in conversation_history:
            if msg.get("role") == "user":
                message_history.append(ModelMessage(role="user", content=msg["content"]))
            elif msg.get("role") == "assistant":
                message_history.append(ModelMessage(role="assistant", content=msg["content"]))
        
        # Handle query with orchestrator
        orchestrator_response = await orchestrator.handle_query(
            query=request.message,
            conversation_id=request.conversation_id,
            context=request.context,
            message_history=message_history
        )
        
        # Save user message to database
        user_message_id = await database.save_message(
            conversation_id=request.conversation_id,
            role="user",
            content=request.message,
            metadata={"context": request.context or {}}
        )
        
        # Save assistant response to database
        assistant_message_id = await database.save_message(
            conversation_id=request.conversation_id,
            role="assistant",
            content=orchestrator_response.response,
            metadata={
                "agent_used": orchestrator_response.agent_used.value,
                "classification": orchestrator_response.classification.dict(),
                "performance_metrics": orchestrator_response.performance_metrics,
                "context_preserved": orchestrator_response.context_preserved,
                "handoff_occurred": orchestrator_response.handoff_occurred
            }
        )
        
        # Update analytics in background
        background_tasks.add_task(
            _update_analytics,
            database,
            request.conversation_id,
            orchestrator_response
        )
        
        return OrchestratedChatResponse(
            response=orchestrator_response.response,
            conversation_id=request.conversation_id,
            agent_used=orchestrator_response.agent_used,
            classification=orchestrator_response.classification,
            performance_metrics=orchestrator_response.performance_metrics,
            context_preserved=orchestrator_response.context_preserved,
            handoff_occurred=orchestrator_response.handoff_occurred,
            message_id=assistant_message_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in orchestrated chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def orchestrated_chat_stream(
    request: OrchestratedChatRequest
) -> StreamingResponse:
    """
    Handle streaming chat using the intelligent agent orchestrator.
    
    Provides real-time streaming responses with orchestration metadata.
    """
    try:
        # Get orchestrator and database
        orchestrator = await get_orchestrator()
        database = await get_database()
        
        # Get conversation history
        conversation_history = await database.get_conversation_history(
            request.conversation_id,
            limit=10
        )
        
        # Convert to ModelMessage format
        message_history = []
        for msg in conversation_history:
            if msg.get("role") == "user":
                message_history.append(ModelMessage(role="user", content=msg["content"]))
            elif msg.get("role") == "assistant":
                message_history.append(ModelMessage(role="assistant", content=msg["content"]))
        
        async def generate_stream():
            """Generate streaming response"""
            try:
                # Save user message
                user_message_id = await database.save_message(
                    conversation_id=request.conversation_id,
                    role="user",
                    content=request.message,
                    metadata={"context": request.context or {}}
                )
                
                # Stream response from orchestrator
                full_response = ""
                orchestration_metadata = None
                
                async for chunk in orchestrator.handle_query_stream(
                    query=request.message,
                    conversation_id=request.conversation_id,
                    context=request.context,
                    message_history=message_history
                ):
                    # Forward chunk to client
                    chunk_data = {
                        "chunk": chunk.get("chunk", ""),
                        "done": chunk.get("done", False),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Include metadata in final chunk
                    if chunk.get("done") and chunk.get("metadata"):
                        orchestration_metadata = chunk["metadata"]
                        chunk_data["metadata"] = orchestration_metadata
                    
                    # Accumulate response content
                    if chunk.get("chunk"):
                        full_response += chunk["chunk"]
                    
                    yield f"data: {chunk_data}\n\n"
                
                # Save complete response to database
                if full_response and orchestration_metadata:
                    await database.save_message(
                        conversation_id=request.conversation_id,
                        role="assistant",
                        content=full_response,
                        metadata=orchestration_metadata
                    )
                    
                    # Update analytics
                    await _update_analytics_from_metadata(
                        database,
                        request.conversation_id,
                        orchestration_metadata
                    )
                
            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                error_chunk = {
                    "chunk": f"Error: {str(e)}",
                    "done": True,
                    "error": True,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {error_chunk}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
        
    except Exception as e:
        logger.error(f"Error setting up streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Classification and Analysis Endpoints

@router.post("/classify", response_model=QueryClassificationResponse)
async def classify_query(
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> QueryClassificationResponse:
    """
    Classify a query to see which agent would handle it.
    
    Useful for understanding the orchestrator's decision-making process.
    """
    try:
        orchestrator = await get_orchestrator()
        
        classification = await orchestrator.classify_query(message, context)
        
        return QueryClassificationResponse(
            classification=classification,
            reasoning=f"Query classified as {classification.primary_agent.value} "
                     f"with {classification.confidence:.2f} confidence. "
                     f"Keywords: {', '.join(classification.keywords)}. "
                     f"Reasoning: {classification.reasoning}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error classifying query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and Status Endpoints

@router.get("/health", response_model=AgentHealthResponse)
async def get_orchestrator_health() -> AgentHealthResponse:
    """
    Get health status of the orchestrator and all specialist agents.
    """
    try:
        orchestrator = await get_orchestrator()
        health_data = await orchestrator.get_health_status()
        
        return AgentHealthResponse(
            status="healthy" if health_data.get("orchestrator", {}).get("status") == "healthy" else "degraded",
            orchestrator=health_data.get("orchestrator", {}),
            agents=health_data.get("agents", {}),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{conversation_id}")
async def get_orchestration_analytics(conversation_id: str) -> Dict[str, Any]:
    """
    Get orchestration analytics for a specific conversation.
    """
    try:
        database = await get_database()
        
        # Get conversation analytics
        analytics = await database.get_conversation_analytics(conversation_id)
        
        # Get agent usage for this conversation
        messages = await database.get_conversation_history(conversation_id)
        agent_usage = {}
        
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("metadata"):
                agent_used = msg["metadata"].get("agent_used", "unknown")
                agent_usage[agent_used] = agent_usage.get(agent_used, 0) + 1
        
        return {
            "conversation_id": conversation_id,
            "analytics": analytics,
            "agent_usage": agent_usage,
            "message_count": len(messages),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# History Endpoints

@router.get("/history/{conversation_id}")
async def get_orchestrated_conversation_history(
    conversation_id: str,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get conversation history with orchestration metadata.
    """
    try:
        database = await get_database()
        history = await database.get_conversation_history(conversation_id, limit)
        
        # Enhance with orchestration data
        enhanced_history = []
        for msg in history:
            enhanced_msg = {
                "id": msg["id"],
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"]
            }
            
            # Add orchestration metadata for assistant messages
            if msg.get("role") == "assistant" and msg.get("metadata"):
                enhanced_msg["orchestration"] = {
                    "agent_used": msg["metadata"].get("agent_used"),
                    "classification": msg["metadata"].get("classification"),
                    "performance_metrics": msg["metadata"].get("performance_metrics"),
                    "handoff_occurred": msg["metadata"].get("handoff_occurred", False)
                }
            
            enhanced_history.append(enhanced_msg)
        
        return {
            "conversation_id": conversation_id,
            "messages": enhanced_history,
            "message_count": len(enhanced_history),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Functions

async def _update_analytics(
    database: QSRDatabase,
    conversation_id: str,
    orchestrator_response: OrchestratorResponse
) -> None:
    """Update analytics based on orchestrator response"""
    try:
        await database.update_conversation_analytics(
            conversation_id,
            {
                "agent_used": orchestrator_response.agent_used.value,
                "classification_confidence": orchestrator_response.classification.confidence,
                "response_time": orchestrator_response.performance_metrics.get("response_time", 0),
                "handoff_occurred": orchestrator_response.handoff_occurred,
                "keywords": orchestrator_response.classification.keywords,
                "urgency": orchestrator_response.classification.urgency
            }
        )
    except Exception as e:
        logger.error(f"Error updating analytics: {e}")


async def _update_analytics_from_metadata(
    database: QSRDatabase,
    conversation_id: str,
    metadata: Dict[str, Any]
) -> None:
    """Update analytics from streaming metadata"""
    try:
        classification = metadata.get("classification", {})
        performance = metadata.get("performance_metrics", {})
        
        await database.update_conversation_analytics(
            conversation_id,
            {
                "agent_used": metadata.get("agent_used", "unknown"),
                "classification_confidence": classification.get("confidence", 0),
                "response_time": performance.get("response_time", 0),
                "handoff_occurred": metadata.get("handoff_occurred", False),
                "keywords": classification.get("keywords", []),
                "urgency": classification.get("urgency", "normal")
            }
        )
    except Exception as e:
        logger.error(f"Error updating analytics from metadata: {e}")


# Export router
__all__ = ["router"]