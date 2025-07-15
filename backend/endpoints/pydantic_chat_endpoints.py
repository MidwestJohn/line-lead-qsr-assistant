#!/usr/bin/env python3
"""
PydanticAI Chat Endpoints - Phase 1 Implementation
==================================================

Updated chat endpoints using official PydanticAI patterns.
Replaces custom OpenAI integration with PydanticAI Agent while maintaining
all QSR-specific functionality.

Features:
- Official PydanticAI Agent integration
- Native streaming with debouncing
- Proper message history management
- SQLite database persistence
- QSR-specific response processing

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

# Import PydanticAI components
from agents.qsr_base_agent import QSRBaseAgent, QSRContext, QSRResponse, qsr_base_agent
from database.qsr_database import QSRDatabase
from services.ragie_service_clean import clean_ragie_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class PydanticChatRequest(BaseModel):
    """Request model for PydanticAI chat endpoint"""
    message: str = Field(..., description="User message")
    conversation_id: str = Field(default="default", description="Conversation identifier")
    include_citations: bool = Field(default=True, description="Include visual citations")
    search_documents: bool = Field(default=True, description="Search documents with Ragie")
    user_location: Optional[str] = Field(default=None, description="User location for context")
    equipment_context: Optional[Dict[str, str]] = Field(default=None, description="Equipment context")

class PydanticChatResponse(BaseModel):
    """Response model for PydanticAI chat endpoint"""
    response: str = Field(..., description="Assistant response")
    timestamp: str = Field(..., description="Response timestamp")
    conversation_id: str = Field(..., description="Conversation identifier")
    
    # QSR-specific fields
    response_type: str = Field(..., description="Type of response")
    confidence: float = Field(..., description="Confidence score")
    safety_alerts: List[str] = Field(default_factory=list, description="Safety alerts")
    equipment_references: List[str] = Field(default_factory=list, description="Equipment references")
    citations: List[str] = Field(default_factory=list, description="Document citations")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    escalation_required: bool = Field(default=False, description="Escalation required")
    
    # Performance metrics
    response_time: Optional[float] = Field(default=None, description="Response time in seconds")
    agent_id: str = Field(..., description="Agent identifier")
    
    # Ragie integration
    ragie_documents: List[Dict[str, Any]] = Field(default_factory=list, description="Ragie documents used")
    
    class Config:
        exclude_none = False

class StreamingChatChunk(BaseModel):
    """Streaming chat chunk model"""
    chunk: str = Field(..., description="Text chunk")
    timestamp: str = Field(..., description="Chunk timestamp")
    conversation_id: str = Field(..., description="Conversation identifier")
    done: bool = Field(default=False, description="Whether streaming is complete")
    
    # Optional metadata for final chunk
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")
    error: Optional[str] = Field(default=None, description="Error message if any")

class QSRChatEndpoints:
    """
    QSR Chat endpoints using PydanticAI patterns
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
        # Lazy-load the agent to ensure environment is loaded first
        self._agent = None
        self.setup_endpoints()
    
    @property
    def agent(self) -> QSRBaseAgent:
        """Lazy-load the agent to ensure environment is properly loaded"""
        if self._agent is None:
            # Ensure environment is loaded
            from dotenv import load_dotenv
            import os
            load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
            
            # Now create the agent
            self._agent = QSRBaseAgent()
        return self._agent
    
    def setup_endpoints(self):
        """Setup all chat endpoints"""
        
        # Standard chat endpoint
        self.app.post("/chat/pydantic", response_model=PydanticChatResponse)(
            self.chat_endpoint
        )
        
        # Streaming chat endpoint
        self.app.post("/chat/pydantic/stream")(
            self.chat_stream_endpoint
        )
        
        # Conversation history endpoint
        self.app.get("/chat/pydantic/history/{conversation_id}")(
            self.get_conversation_history
        )
        
        # Conversation analytics endpoint
        self.app.get("/chat/pydantic/analytics/{conversation_id}")(
            self.get_conversation_analytics
        )
        
        # Agent health check
        self.app.get("/chat/pydantic/health")(
            self.agent_health_check
        )
    
    async def get_database(self) -> QSRDatabase:
        """Get database connection"""
        # This would typically be managed by FastAPI dependency injection
        # For now, we'll create a new connection each time
        async with QSRDatabase.connect() as db:
            return db
    
    async def chat_endpoint(self, request: PydanticChatRequest) -> PydanticChatResponse:
        """
        Standard chat endpoint using PydanticAI Agent
        
        Args:
            request: Chat request
            
        Returns:
            PydanticChatResponse with complete response
        """
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate request
            if not request.message.strip():
                raise HTTPException(status_code=400, detail="Message cannot be empty")
            
            logger.info(f"Processing PydanticAI chat request: {request.message[:50]}...")
            
            # Get database connection
            async with QSRDatabase.connect() as db:
                # Get conversation history
                message_history = await db.get_messages(request.conversation_id, limit=20)
                
                # Search documents with Ragie if requested
                ragie_documents = []
                if request.search_documents:
                    ragie_documents = await self._search_ragie_documents(request.message)
                
                # Create QSR context
                context = QSRContext(
                    conversation_id=request.conversation_id,
                    user_location=request.user_location,
                    equipment_context=request.equipment_context,
                    previous_queries=[request.message]
                )
                
                # Process query with agent
                response = await self.agent.process_query(
                    query=request.message,
                    context=context,
                    message_history=message_history
                )
                
                # Calculate response time
                response_time = asyncio.get_event_loop().time() - start_time
                
                # Save conversation data
                await self._save_conversation_data(db, request, response, response_time)
                
                # Create API response
                api_response = PydanticChatResponse(
                    response=response.response,
                    timestamp=datetime.now().isoformat(),
                    conversation_id=request.conversation_id,
                    response_type=response.response_type,
                    confidence=response.confidence,
                    safety_alerts=response.safety_alerts,
                    equipment_references=response.equipment_references,
                    citations=response.citations,
                    follow_up_suggestions=response.follow_up_suggestions,
                    escalation_required=response.escalation_required,
                    response_time=response_time,
                    agent_id=self.agent.agent_id,
                    ragie_documents=ragie_documents
                )
                
                logger.info(f"PydanticAI chat response generated in {response_time:.2f}s")
                return api_response
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in PydanticAI chat endpoint: {str(e)}")
            raise HTTPException(status_code=500, detail="Chat processing failed")
    
    async def chat_stream_endpoint(self, request: PydanticChatRequest) -> StreamingResponse:
        """
        Streaming chat endpoint using PydanticAI Agent
        
        Args:
            request: Chat request
            
        Returns:
            StreamingResponse with real-time chunks
        """
        
        try:
            # Validate request
            if not request.message.strip():
                raise HTTPException(status_code=400, detail="Message cannot be empty")
            
            logger.info(f"Processing PydanticAI streaming chat request: {request.message[:50]}...")
            
            async def generate_stream():
                try:
                    # Get database connection
                    async with QSRDatabase.connect() as db:
                        # Get conversation history
                        message_history = await db.get_messages(request.conversation_id, limit=20)
                        
                        # Search documents with Ragie if requested
                        ragie_documents = []
                        if request.search_documents:
                            ragie_documents = await self._search_ragie_documents(request.message)
                        
                        # Create QSR context
                        context = QSRContext(
                            conversation_id=request.conversation_id,
                            user_location=request.user_location,
                            equipment_context=request.equipment_context,
                            previous_queries=[request.message]
                        )
                        
                        # Stream user message first
                        user_chunk = StreamingChatChunk(
                            chunk=f"User: {request.message}\n\nAssistant: ",
                            timestamp=datetime.now().isoformat(),
                            conversation_id=request.conversation_id,
                            done=False
                        )
                        yield f"data: {user_chunk.json()}\n\n"
                        
                        # Stream agent response
                        complete_response = ""
                        async for chunk_data in self.agent.process_query_stream(
                            query=request.message,
                            context=context,
                            message_history=message_history
                        ):
                            if chunk_data["done"]:
                                # Final chunk with metadata
                                final_chunk = StreamingChatChunk(
                                    chunk="",
                                    timestamp=chunk_data["timestamp"],
                                    conversation_id=request.conversation_id,
                                    done=True,
                                    metadata={
                                        **chunk_data.get("metadata", {}),
                                        "ragie_documents": ragie_documents,
                                        "agent_id": self.agent.agent_id
                                    }
                                )
                                yield f"data: {final_chunk.json()}\n\n"
                                
                                # Save conversation data
                                await self._save_streaming_conversation_data(
                                    db, request, complete_response, chunk_data.get("metadata", {})
                                )
                                
                            else:
                                # Regular chunk
                                complete_response += chunk_data["chunk"]
                                chunk = StreamingChatChunk(
                                    chunk=chunk_data["chunk"],
                                    timestamp=chunk_data["timestamp"],
                                    conversation_id=request.conversation_id,
                                    done=False
                                )
                                yield f"data: {chunk.json()}\n\n"
                
                except Exception as e:
                    logger.error(f"Error in streaming chat: {str(e)}")
                    error_chunk = StreamingChatChunk(
                        chunk="",
                        timestamp=datetime.now().isoformat(),
                        conversation_id=request.conversation_id,
                        done=True,
                        error=str(e)
                    )
                    yield f"data: {error_chunk.json()}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error setting up streaming chat: {str(e)}")
            raise HTTPException(status_code=500, detail="Streaming setup failed")
    
    async def get_conversation_history(self, conversation_id: str) -> JSONResponse:
        """
        Get conversation history
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            JSONResponse with conversation history
        """
        
        try:
            async with QSRDatabase.connect() as db:
                # Get messages
                messages = await db.get_messages(conversation_id)
                
                # Get metadata
                metadata = await db.get_conversation_metadata(conversation_id)
                
                # Format response
                response = {
                    "conversation_id": conversation_id,
                    "message_count": len(messages),
                    "messages": [
                        {
                            "role": getattr(msg, 'role', 'unknown'),
                            "content": getattr(msg, 'content', str(msg)),
                            "timestamp": getattr(msg, 'timestamp', datetime.now().isoformat())
                        }
                        for msg in messages
                    ],
                    "metadata": metadata.to_dict() if metadata else None
                }
                
                return JSONResponse(content=response)
                
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get conversation history")
    
    async def get_conversation_analytics(self, conversation_id: str) -> JSONResponse:
        """
        Get conversation analytics
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            JSONResponse with analytics data
        """
        
        try:
            async with QSRDatabase.connect() as db:
                analytics = await db.get_conversation_analytics(conversation_id)
                return JSONResponse(content=analytics)
                
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get conversation analytics")
    
    async def agent_health_check(self) -> JSONResponse:
        """
        Agent health check endpoint
        
        Returns:
            JSONResponse with health status
        """
        
        try:
            health_status = await self.agent.health_check()
            return JSONResponse(content=health_status)
            
        except Exception as e:
            logger.error(f"Error in agent health check: {str(e)}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                status_code=500
            )
    
    async def _search_ragie_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search documents using Ragie service"""
        
        documents = []
        
        if clean_ragie_service.is_available():
            try:
                logger.info("Searching Ragie documents...")
                ragie_results = await clean_ragie_service.search(query, limit=5)
                
                for result in ragie_results:
                    documents.append({
                        'content': result.text,
                        'score': result.score,
                        'source': result.metadata.get('original_filename', 'Unknown'),
                        'document_id': result.document_id,
                        'search_method': 'ragie'
                    })
                
                logger.info(f"Found {len(documents)} documents from Ragie")
                
            except Exception as e:
                logger.warning(f"Ragie search failed: {e}")
        
        return documents
    
    async def _save_conversation_data(self, db: QSRDatabase, request: PydanticChatRequest, 
                                    response: QSRResponse, response_time: float) -> None:
        """Save conversation data to database"""
        
        try:
            # This would typically save the actual PydanticAI messages
            # For now, we'll create a simple representation
            message_data = json.dumps([
                {
                    "role": "user",
                    "content": request.message,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "role": "assistant",
                    "content": response.response,
                    "timestamp": datetime.now().isoformat()
                }
            ])
            
            # Save messages
            await db.add_messages(
                conversation_id=request.conversation_id,
                messages=message_data.encode(),
                agent_id=self.agent.agent_id,
                response_time=response_time
            )
            
            # Save equipment references
            for equipment in response.equipment_references:
                await db.add_equipment_reference(
                    conversation_id=request.conversation_id,
                    equipment_name=equipment,
                    context=request.message
                )
            
            # Save safety incidents
            if response.safety_alerts:
                severity = "high" if response.escalation_required else "medium"
                await db.add_safety_incident(
                    conversation_id=request.conversation_id,
                    incident_type="safety_guidance",
                    severity_level=severity,
                    response_provided=response.response,
                    escalation_required=response.escalation_required
                )
            
            # Save analytics
            await db.add_analytics_metric(
                conversation_id=request.conversation_id,
                metric_type="response_time",
                metric_value=response_time
            )
            
            await db.add_analytics_metric(
                conversation_id=request.conversation_id,
                metric_type="confidence",
                metric_value=response.confidence
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation data: {str(e)}")
    
    async def _save_streaming_conversation_data(self, db: QSRDatabase, request: PydanticChatRequest, 
                                              complete_response: str, metadata: Dict[str, Any]) -> None:
        """Save streaming conversation data to database"""
        
        try:
            # Create simple message representation
            message_data = json.dumps([
                {
                    "role": "user",
                    "content": request.message,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "role": "assistant",
                    "content": complete_response,
                    "timestamp": datetime.now().isoformat()
                }
            ])
            
            # Save messages
            await db.add_messages(
                conversation_id=request.conversation_id,
                messages=message_data.encode(),
                agent_id=self.agent.agent_id
            )
            
            # Save metadata-based analytics
            if metadata.get("equipment_references"):
                for equipment in metadata["equipment_references"]:
                    await db.add_equipment_reference(
                        conversation_id=request.conversation_id,
                        equipment_name=equipment,
                        context=request.message
                    )
            
            if metadata.get("safety_alerts"):
                severity = "high" if metadata.get("escalation_required") else "medium"
                await db.add_safety_incident(
                    conversation_id=request.conversation_id,
                    incident_type="safety_guidance",
                    severity_level=severity,
                    response_provided=complete_response,
                    escalation_required=metadata.get("escalation_required", False)
                )
            
            # Save confidence metric
            if metadata.get("confidence"):
                await db.add_analytics_metric(
                    conversation_id=request.conversation_id,
                    metric_type="confidence",
                    metric_value=metadata["confidence"]
                )
            
        except Exception as e:
            logger.error(f"Error saving streaming conversation data: {str(e)}")

# Factory function to setup endpoints
def setup_pydantic_chat_endpoints(app: FastAPI) -> QSRChatEndpoints:
    """
    Setup PydanticAI chat endpoints on FastAPI app
    
    Args:
        app: FastAPI application instance
        
    Returns:
        QSRChatEndpoints instance
    """
    
    return QSRChatEndpoints(app)

# Test function
async def test_endpoints():
    """Test the endpoints"""
    
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI()
    endpoints = setup_pydantic_chat_endpoints(app)
    
    client = TestClient(app)
    
    # Test chat endpoint
    response = client.post("/chat/pydantic", json={
        "message": "How do I clean the Taylor ice cream machine?",
        "conversation_id": "test_conversation"
    })
    
    print(f"Chat endpoint response: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    
    # Test health check
    response = client.get("/chat/pydantic/health")
    print(f"Health check response: {response.status_code}")
    if response.status_code == 200:
        print(f"Health: {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())