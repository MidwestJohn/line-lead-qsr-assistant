#!/usr/bin/env python3
"""
Enhanced Text Chat Endpoint with PydanticAI + Ragie Intelligence
===============================================================

Transforms the basic text chat endpoint to use the full PydanticAI + Ragie
intelligence system. Provides the same sophisticated responses for text chat
as voice chat, with multi-agent routing and visual citations.

Key Features:
- PydanticAI multi-agent routing for text chat
- Ragie knowledge integration for all responses
- Visual citations from Ragie in text responses
- Equipment context preservation
- Safety analysis and warnings
- Performance monitoring

Author: Generated with Memex (https://memex.tech)
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import datetime
import json
import asyncio
import time
import os
import uuid
from pathlib import Path

# Import our enhanced intelligence services
try:
    from services.enhanced_clean_intelligence_service import (
        create_enhanced_clean_intelligence_service,
        EnhancedCleanIntelligenceService
    )
    from models.universal_response_models import (
        TextChatResponse, InteractionMode, AgentType, SafetyLevel
    )
    from services.ragie_service_clean import clean_ragie_service
    from services.multimodal_citation_service import MultiModalCitationService
    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Intelligence services not available: {e}")
    INTELLIGENCE_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===============================================================================
# ENHANCED TEXT CHAT MODELS
# ===============================================================================

class EnhancedChatMessage(BaseModel):
    """Enhanced chat message model with additional context"""
    message: str = Field(..., description="The user's message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    equipment_context: Optional[List[str]] = Field(None, description="Equipment mentioned")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="Previous conversation")
    user_expertise: Optional[str] = Field("beginner", description="User expertise level")

class EnhancedChatResponse(BaseModel):
    """Enhanced chat response with intelligence features"""
    
    # Core response
    response: str = Field(..., description="The main response text")
    formatted_response: str = Field(..., description="UI-formatted response")
    timestamp: str = Field(..., description="Response timestamp")
    
    # Intelligence features
    agent_type: str = Field(..., description="Primary agent that handled the query")
    confidence_score: float = Field(..., description="Response confidence")
    
    # Ragie integration
    ragie_sources: List[Dict[str, Any]] = Field(default_factory=list, description="Ragie knowledge sources")
    ragie_confidence: float = Field(0.8, description="Ragie knowledge confidence")
    
    # Visual citations
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list, description="Visual citations")
    citation_count: int = Field(0, description="Number of visual citations")
    
    # Safety and context
    safety_priority: bool = Field(False, description="Safety priority flag")
    safety_warnings: List[str] = Field(default_factory=list, description="Safety warnings")
    equipment_context: Optional[Dict[str, Any]] = Field(None, description="Equipment context")
    
    # User experience
    suggested_follow_ups: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    
    # Performance metrics
    generation_time_ms: float = Field(0.0, description="Response generation time")
    intelligence_used: bool = Field(False, description="Whether intelligence was used")
    
    # Legacy compatibility
    parsed_steps: Optional[Dict[str, Any]] = Field(None, description="Parsed steps if procedure")
    manual_references: List[Dict[str, Any]] = Field(default_factory=list, description="Manual references")
    document_context: Optional[Dict[str, Any]] = Field(None, description="Document context")
    retrieval_method: str = Field("enhanced_intelligence", description="Retrieval method used")

# ===============================================================================
# ENHANCED TEXT CHAT SERVICE
# ===============================================================================

class EnhancedTextChatService:
    """Enhanced text chat service using PydanticAI + Ragie intelligence"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.EnhancedTextChatService")
        self.intelligence_service = None
        self.citation_service = None
        self.initialized = False
        
        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.avg_response_time = 0.0
        
    async def initialize(self):
        """Initialize the enhanced text chat service"""
        
        if not INTELLIGENCE_AVAILABLE:
            self.logger.warning("Intelligence services not available, using fallback")
            return False
        
        try:
            # Create enhanced intelligence service
            self.intelligence_service = await create_enhanced_clean_intelligence_service(
                ragie_service=clean_ragie_service,
                citation_service=MultiModalCitationService()
            )
            
            # Create citation service
            self.citation_service = MultiModalCitationService()
            
            self.initialized = True
            self.logger.info("✅ Enhanced text chat service initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced text chat service: {e}")
            return False
    
    async def process_chat_message(self, chat_message: EnhancedChatMessage) -> EnhancedChatResponse:
        """Process chat message with enhanced intelligence"""
        
        start_time = time.time()
        
        try:
            if not self.initialized:
                # Try to initialize on first request
                await self.initialize()
            
            if self.initialized and self.intelligence_service:
                # Use enhanced intelligence
                response = await self._process_with_intelligence(chat_message)
            else:
                # Fallback to basic processing
                response = await self._process_with_fallback(chat_message)
            
            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            self._update_metrics(processing_time, True)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Chat message processing failed: {e}")
            
            # Update metrics for failure
            processing_time = (time.time() - start_time) * 1000
            self._update_metrics(processing_time, False)
            
            # Return error response
            return self._create_error_response(chat_message, str(e))
    
    async def _process_with_intelligence(self, chat_message: EnhancedChatMessage) -> EnhancedChatResponse:
        """Process with enhanced intelligence service"""
        
        # Process with enhanced intelligence
        text_response = await self.intelligence_service.process_text_query(
            query=chat_message.message,
            session_id=chat_message.session_id,
            equipment_mentioned=chat_message.equipment_context,
            conversation_history=chat_message.conversation_history
        )
        
        # Convert to enhanced chat response
        return await self._convert_to_chat_response(text_response, chat_message)
    
    async def _process_with_fallback(self, chat_message: EnhancedChatMessage) -> EnhancedChatResponse:
        """Process with fallback when intelligence is unavailable"""
        
        self.logger.info("Using fallback processing for chat message")
        
        # Try Ragie if available
        ragie_response = None
        if clean_ragie_service.is_available():
            try:
                ragie_results = await clean_ragie_service.search(chat_message.message, limit=5)
                if ragie_results:
                    ragie_response = ragie_results[0]
            except Exception as e:
                self.logger.error(f"Ragie fallback failed: {e}")
        
        # Generate basic response
        if ragie_response:
            response_text = ragie_response.get('content', 'I can help with QSR questions.')
            confidence = ragie_response.get('confidence', 0.7)
            sources = [ragie_response.get('metadata', {})]
        else:
            response_text = f"I received your message: {chat_message.message}. I can help with QSR questions."
            confidence = 0.5
            sources = []
        
        return EnhancedChatResponse(
            response=response_text,
            formatted_response=response_text,
            timestamp=datetime.datetime.now().isoformat(),
            agent_type="general",
            confidence_score=confidence,
            ragie_sources=sources,
            intelligence_used=False,
            retrieval_method="fallback"
        )
    
    async def _convert_to_chat_response(self, text_response: TextChatResponse, chat_message: EnhancedChatMessage) -> EnhancedChatResponse:
        """Convert universal text response to enhanced chat response"""
        
        # Get equipment context
        equipment_context = None
        if text_response.get_equipment_context():
            equipment_context = {
                'equipment_name': text_response.get_equipment_context().equipment_name,
                'equipment_type': text_response.get_equipment_context().equipment_type,
                'safety_warnings': text_response.get_equipment_context().safety_warnings
            }
        
        # Get parsed steps if available
        parsed_steps = None
        if text_response.get_procedure_context():
            parsed_steps = {
                'procedure_name': text_response.get_procedure_context().procedure_name,
                'steps': text_response.get_procedure_context().steps,
                'step_count': text_response.get_procedure_context().get_step_count()
            }
        
        # Convert visual citations
        visual_citations = []
        for citation in text_response.visual_citations:
            visual_citations.append({
                'citation_id': citation.citation_id,
                'type': citation.citation_type,
                'source': citation.source_document,
                'title': citation.title,
                'description': citation.description,
                'confidence': citation.ragie_confidence,
                'agent_type': citation.agent_type.value,
                'ragie_source': citation.ragie_source
            })
        
        # Convert knowledge sources
        ragie_sources = []
        for knowledge in text_response.knowledge_sources:
            ragie_sources.append({
                'content': knowledge.content,
                'confidence': knowledge.confidence,
                'source_title': knowledge.source_title,
                'source_page': knowledge.source_page,
                'knowledge_type': knowledge.knowledge_type
            })
        
        return EnhancedChatResponse(
            response=text_response.text_response,
            formatted_response=text_response.formatted_text or text_response.text_response,
            timestamp=datetime.datetime.now().isoformat(),
            agent_type=text_response.primary_agent.value,
            confidence_score=text_response.confidence_score,
            ragie_sources=ragie_sources,
            ragie_confidence=text_response.ragie_context.avg_ragie_confidence,
            visual_citations=visual_citations,
            citation_count=len(visual_citations),
            safety_priority=text_response.safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL],
            safety_warnings=text_response.safety_warnings,
            equipment_context=equipment_context,
            suggested_follow_ups=text_response.suggested_follow_ups,
            generation_time_ms=text_response.total_processing_time_ms,
            intelligence_used=True,
            parsed_steps=parsed_steps,
            manual_references=ragie_sources,  # Map to legacy field
            document_context=equipment_context,  # Map to legacy field
            retrieval_method="enhanced_intelligence"
        )
    
    def _create_error_response(self, chat_message: EnhancedChatMessage, error_msg: str) -> EnhancedChatResponse:
        """Create error response"""
        
        return EnhancedChatResponse(
            response=f"I apologize, but I'm experiencing technical difficulties: {error_msg}. Please try again.",
            formatted_response=f"I apologize, but I'm experiencing technical difficulties: {error_msg}. Please try again.",
            timestamp=datetime.datetime.now().isoformat(),
            agent_type="general",
            confidence_score=0.3,
            safety_priority=True,
            safety_warnings=["System experiencing technical difficulties"],
            intelligence_used=False,
            retrieval_method="error"
        )
    
    def _update_metrics(self, processing_time: float, success: bool):
        """Update performance metrics"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        
        # Update average response time
        self.avg_response_time = (
            (self.avg_response_time * (self.total_requests - 1) + processing_time) / self.total_requests
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'success_rate': self.successful_requests / max(self.total_requests, 1),
            'avg_response_time_ms': self.avg_response_time,
            'intelligence_available': self.initialized
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        return {
            'status': 'healthy' if self.initialized else 'degraded',
            'initialized': self.initialized,
            'intelligence_available': INTELLIGENCE_AVAILABLE,
            'metrics': self.get_metrics()
        }

# ===============================================================================
# GLOBAL SERVICE INSTANCE
# ===============================================================================

# Global enhanced text chat service
enhanced_text_chat_service = EnhancedTextChatService()

# ===============================================================================
# ENHANCED ENDPOINT FUNCTIONS
# ===============================================================================

async def enhanced_chat_endpoint(chat_message: EnhancedChatMessage) -> EnhancedChatResponse:
    """Enhanced chat endpoint with PydanticAI + Ragie intelligence"""
    
    logger.info(f"Enhanced chat request: {chat_message.message[:100]}...")
    
    # Process with enhanced service
    response = await enhanced_text_chat_service.process_chat_message(chat_message)
    
    logger.info(f"Enhanced chat response: agent={response.agent_type}, confidence={response.confidence_score}")
    
    return response

async def enhanced_chat_stream_endpoint(chat_message: EnhancedChatMessage) -> Dict[str, Any]:
    """Enhanced streaming chat endpoint"""
    
    try:
        # Get enhanced response
        response = await enhanced_chat_endpoint(chat_message)
        
        # Convert to streaming format (for now, just return the response)
        # In the future, this could be enhanced to stream the response generation
        return response.dict()
        
    except Exception as e:
        logger.error(f"Enhanced streaming chat endpoint error: {e}")
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again.",
            "timestamp": datetime.datetime.now().isoformat(),
            "agent_type": "general",
            "confidence_score": 0.3,
            "intelligence_used": False,
            "retrieval_method": "error",
            "error": str(e)
        }

async def get_enhanced_chat_metrics() -> Dict[str, Any]:
    """Get enhanced chat service metrics"""
    return await enhanced_text_chat_service.health_check()

# ===============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# ===============================================================================

class ChatMessage(BaseModel):
    """Legacy chat message model for backward compatibility"""
    message: str

class ChatResponse(BaseModel):
    """Legacy chat response model for backward compatibility"""
    response: str
    timestamp: str
    parsed_steps: Optional[Dict[str, Any]] = None
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list)
    manual_references: List[Dict[str, Any]] = Field(default_factory=list)
    document_context: Optional[Dict[str, Any]] = None
    hierarchical_path: Optional[List[str]] = None
    contextual_recommendations: List[str] = Field(default_factory=list)
    retrieval_method: str = "enhanced"

async def backward_compatible_chat_endpoint(chat_message: ChatMessage) -> ChatResponse:
    """Backward compatible chat endpoint that uses enhanced intelligence"""
    
    # Convert to enhanced message
    enhanced_message = EnhancedChatMessage(
        message=chat_message.message,
        session_id=str(uuid.uuid4()),
        user_expertise="beginner"
    )
    
    # Process with enhanced service
    enhanced_response = await enhanced_chat_endpoint(enhanced_message)
    
    # Convert to legacy format
    return ChatResponse(
        response=enhanced_response.response,
        timestamp=enhanced_response.timestamp,
        parsed_steps=enhanced_response.parsed_steps,
        visual_citations=enhanced_response.visual_citations,
        manual_references=enhanced_response.manual_references,
        document_context=enhanced_response.document_context,
        hierarchical_path=None,
        contextual_recommendations=enhanced_response.suggested_follow_ups,
        retrieval_method=enhanced_response.retrieval_method
    )

# ===============================================================================
# INITIALIZATION FUNCTION
# ===============================================================================

async def initialize_enhanced_text_chat():
    """Initialize enhanced text chat service"""
    
    logger.info("Initializing enhanced text chat service...")
    
    success = await enhanced_text_chat_service.initialize()
    
    if success:
        logger.info("✅ Enhanced text chat service initialized successfully")
    else:
        logger.warning("⚠️ Enhanced text chat service initialization failed, using fallback")
    
    return success

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Enhanced models
    "EnhancedChatMessage",
    "EnhancedChatResponse",
    
    # Enhanced endpoints
    "enhanced_chat_endpoint",
    "enhanced_chat_stream_endpoint",
    "get_enhanced_chat_metrics",
    
    # Backward compatibility
    "ChatMessage",
    "ChatResponse",
    "backward_compatible_chat_endpoint",
    
    # Service and initialization
    "enhanced_text_chat_service",
    "initialize_enhanced_text_chat"
]