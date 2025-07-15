#!/usr/bin/env python3
"""
Production System Integration - Phase 3
======================================

Production-ready enhancement layer that integrates with existing main.py patterns
while adding PydanticAI compatibility and production features.

This preserves the existing Ragie translation layer and conversation patterns
while adding enterprise-grade capabilities.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from contextlib import asynccontextmanager

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from .database.pydantic_ai_database import PydanticAIDatabase, create_pydantic_ai_database

logger = logging.getLogger(__name__)

class ProductionTranslationLayer:
    """
    Translation layer that bridges existing main.py patterns with PydanticAI.
    
    This maintains compatibility with:
    - Existing Ragie integration (clean_ragie_service)
    - Voice orchestrator patterns
    - Simple conversation_id handling
    
    While adding:
    - Proper PydanticAI message storage
    - Production database management
    - Enhanced monitoring and analytics
    """
    
    def __init__(self):
        self.db: Optional[PydanticAIDatabase] = None
        self.db_context_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the production translation layer"""
        if self._initialized:
            return
            
        try:
            logger.info("🔧 Initializing Production Translation Layer...")
            
            # Initialize PydanticAI database
            db_path = Path(os.getenv("DATABASE_PATH", "qsr_production.sqlite"))
            self.db_context_manager = create_pydantic_ai_database(db_path)
            self.db = await self.db_context_manager.__aenter__()
            
            self._initialized = True
            logger.info("✅ Production Translation Layer initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Production Translation Layer: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.db_context_manager:
            await self.db_context_manager.__aexit__(None, None, None)
    
    def translate_conversation_to_pydantic(
        self, 
        conversation_id: str, 
        message: str, 
        role: str = "user",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Translate main.py conversation patterns to PydanticAI format.
        
        This maintains compatibility with existing ChatMessage patterns
        while preparing for PydanticAI storage.
        """
        return {
            "conversation_id": conversation_id,
            "message": message,
            "role": role,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
    
    async def save_conversation_exchange(
        self,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        agent_type: str = "qsr_assistant",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Save a complete conversation exchange (user + assistant) using PydanticAI patterns.
        
        This is compatible with existing main.py chat endpoint patterns.
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create PydanticAI-compatible messages
            from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
            
            # Create request (user message)
            user_request = ModelRequest(
                parts=[UserPromptPart(content=user_message)]
            )
            
            # Create response (assistant message)  
            assistant_response = ModelResponse(
                parts=[TextPart(content=assistant_response)],
                model_name="qsr-assistant"
            )
            
            # Serialize messages using PydanticAI's official method
            messages = [user_request, assistant_response]
            serialized_messages = ModelMessagesTypeAdapter.dump_json(messages)
            
            # Save to database
            success = await self.db.add_messages(
                conversation_id=conversation_id,
                messages=serialized_messages,
                agent_id=agent_type
            )
            
            # Save analytics if provided
            if metadata and success:
                await self.db.save_qsr_analytics(
                    conversation_id=conversation_id,
                    agent_type=agent_type,
                    metadata=metadata
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save conversation exchange: {e}")
            return False
    
    async def get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[ModelMessage]:
        """
        Get conversation history in PydanticAI format.
        
        Compatible with existing conversation_id patterns.
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.db.get_messages(
                conversation_id=conversation_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def translate_ragie_results_to_context(
        self, 
        ragie_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Translate Ragie search results to PydanticAI context format.
        
        Maintains compatibility with existing clean_ragie_service patterns.
        """
        try:
            translated_context = {
                "ragie_results": ragie_results,
                "document_count": len(ragie_results),
                "search_method": "ragie_enhanced",
                "relevant_content": []
            }
            
            # Extract content for PydanticAI context
            for result in ragie_results:
                content_item = {
                    "text": result.get("text", ""),
                    "source": result.get("metadata", {}).get("file_name", "Unknown"),
                    "score": result.get("score", 0.0),
                    "chunk_id": result.get("chunk_id", "")
                }
                translated_context["relevant_content"].append(content_item)
            
            return translated_context
            
        except Exception as e:
            logger.error(f"Failed to translate Ragie results: {e}")
            return {"error": str(e), "ragie_results": ragie_results}
    
    async def get_production_metrics(self) -> Dict[str, Any]:
        """Get production system metrics"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        try:
            db_health = await self.db.health_check()
            
            return {
                "status": "healthy",
                "database": db_health,
                "translation_layer": {
                    "initialized": self._initialized,
                    "pydantic_ai_compatible": True,
                    "ragie_compatible": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global production translation layer
_production_layer: Optional[ProductionTranslationLayer] = None

async def get_production_layer() -> ProductionTranslationLayer:
    """Get the global production translation layer"""
    global _production_layer
    
    if _production_layer is None:
        _production_layer = ProductionTranslationLayer()
        await _production_layer.initialize()
    
    return _production_layer


class ProductionChatWrapper:
    """
    Wrapper for existing chat endpoints that adds production features
    while maintaining compatibility with main.py patterns.
    """
    
    def __init__(self):
        self.translation_layer: Optional[ProductionTranslationLayer] = None
    
    async def enhanced_chat_endpoint(
        self,
        user_message: str,
        conversation_id: str = "default",
        enable_analytics: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced version of main.py chat endpoint with production features.
        
        This wraps the existing chat logic while adding:
        - PydanticAI message storage
        - Production analytics
        - Enhanced error handling
        """
        start_time = datetime.now()
        
        try:
            # Get production layer
            if not self.translation_layer:
                self.translation_layer = await get_production_layer()
            
            # Get conversation history for context
            message_history = await self.translation_layer.get_conversation_history(
                conversation_id=conversation_id,
                limit=10
            )
            
            # TODO: Integrate with existing main.py chat logic here
            # This would call the existing chat processing logic
            assistant_response = f"Enhanced response to: {user_message}"
            
            # Save the conversation exchange
            if enable_analytics:
                response_time = (datetime.now() - start_time).total_seconds()
                metadata = {
                    "response_time": response_time,
                    "message_count": len(message_history) + 2,  # +2 for current exchange
                    "enhanced_features": True
                }
                
                await self.translation_layer.save_conversation_exchange(
                    conversation_id=conversation_id,
                    user_message=user_message,
                    assistant_response=assistant_response,
                    agent_type="enhanced_qsr_assistant",
                    metadata=metadata
                )
            
            return {
                "response": assistant_response,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "production_enhanced": True,
                "message_history_count": len(message_history)
            }
            
        except Exception as e:
            logger.error(f"Enhanced chat endpoint failed: {e}")
            return {
                "error": str(e),
                "conversation_id": conversation_id,
                "production_enhanced": False
            }


# Export key components
__all__ = [
    "ProductionTranslationLayer",
    "ProductionChatWrapper", 
    "get_production_layer"
]