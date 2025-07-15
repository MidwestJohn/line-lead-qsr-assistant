"""
Intelligence Integration Layer
============================

Integrates the Core Intelligence Service with existing endpoints and services.
Provides seamless upgrade from basic text processing to intelligent PydanticAI responses.

This layer:
- Connects CoreIntelligenceService to existing /chat/stream endpoint
- Enhances voice processing with intelligent responses
- Maintains backward compatibility with existing VoiceResponse
- Provides performance monitoring and fallback mechanisms

Author: Generated with Memex (https://memex.tech)
"""

import logging
import asyncio
import time
from typing import Optional, Dict, Any, Union
from datetime import datetime
import json

# Import existing services and models
try:
    from services.core_intelligence_service import (
        CoreIntelligenceService, create_core_intelligence_service,
        IntelligentResponse, InteractionMode, AgentType
    )
    from services.ragie_service_clean import RagieService
    from services.multimodal_citation_service import MultiModalCitationService
    from voice_agent import VoiceResponse, ConversationContext, VoiceState, ConversationIntent
    from step_parser import parse_ai_response_steps
    
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    INTEGRATION_AVAILABLE = False
    logging.warning(f"Intelligence integration not available: {e}")

logger = logging.getLogger(__name__)

# ===============================================================================
# INTEGRATION MODELS
# ===============================================================================

class IntelligenceUpgradeStatus:
    """Status of intelligence upgrade for the system"""
    
    def __init__(self):
        self.enabled = False
        self.core_service = None
        self.fallback_count = 0
        self.success_count = 0
        self.total_requests = 0
        self.average_response_time = 0.0
        self.last_upgrade_time = None
    
    def update_stats(self, success: bool, response_time: float):
        """Update integration statistics"""
        self.total_requests += 1
        if success:
            self.success_count += 1
        else:
            self.fallback_count += 1
        
        # Update average response time
        self.average_response_time = (
            (self.average_response_time * (self.total_requests - 1) + response_time) / self.total_requests
        )
    
    def get_success_rate(self) -> float:
        """Get success rate of intelligence upgrade"""
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests
    
    def get_status_dict(self) -> Dict[str, Any]:
        """Get status as dictionary"""
        return {
            'enabled': self.enabled,
            'total_requests': self.total_requests,
            'success_count': self.success_count,
            'fallback_count': self.fallback_count,
            'success_rate': self.get_success_rate(),
            'average_response_time_ms': self.average_response_time,
            'last_upgrade_time': self.last_upgrade_time
        }

# ===============================================================================
# INTELLIGENCE INTEGRATION SERVICE
# ===============================================================================

class IntelligenceIntegration:
    """
    Integration service that upgrades existing endpoints with intelligent responses.
    Provides seamless transition from basic text processing to PydanticAI + Ragie.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.IntelligenceIntegration")
        self.upgrade_status = IntelligenceUpgradeStatus()
        self.core_service = None
        self.initialized = False
        
        # Fallback services
        self.fallback_services = {
            'ragie_service': None,
            'citation_service': None
        }
    
    async def initialize(self, 
                        ragie_service: Any = None,
                        citation_service: Any = None,
                        conversation_context: Any = None):
        """Initialize the intelligence integration"""
        
        if not INTEGRATION_AVAILABLE:
            self.logger.warning("Intelligence integration dependencies not available")
            return False
        
        try:
            # Store fallback services
            self.fallback_services['ragie_service'] = ragie_service
            self.fallback_services['citation_service'] = citation_service
            
            # Create core intelligence service
            self.core_service = await create_core_intelligence_service(
                ragie_service=ragie_service,
                citation_service=citation_service,
                conversation_context=conversation_context
            )
            
            # Mark as initialized
            self.initialized = True
            self.upgrade_status.enabled = True
            self.upgrade_status.core_service = self.core_service
            self.upgrade_status.last_upgrade_time = datetime.now()
            
            self.logger.info("✅ Intelligence integration initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Intelligence integration initialization failed: {e}")
            return False
    
    async def process_chat_message(self,
                                 message: str,
                                 session_id: str = None,
                                 conversation_context: Optional[Dict[str, Any]] = None,
                                 use_intelligence: bool = True) -> Union[IntelligentResponse, Dict[str, Any]]:
        """
        Process chat message with intelligence upgrade.
        Falls back to basic processing if intelligence is unavailable.
        """
        
        start_time = time.time()
        
        try:
            # Use intelligence if available and enabled
            if use_intelligence and self.initialized and self.core_service:
                
                # Process with core intelligence service
                intelligent_response = await self.core_service.process_text_chat(
                    query=message,
                    session_id=session_id,
                    conversation_context=conversation_context
                )
                
                # Update success stats
                processing_time = (time.time() - start_time) * 1000
                self.upgrade_status.update_stats(True, processing_time)
                
                self.logger.info(f"Processed chat message with intelligence in {processing_time:.2f}ms")
                return intelligent_response
            
            else:
                # Fallback to basic processing
                return await self._fallback_chat_processing(message, session_id, conversation_context)
                
        except Exception as e:
            self.logger.error(f"Intelligence chat processing failed: {e}")
            
            # Update failure stats
            processing_time = (time.time() - start_time) * 1000
            self.upgrade_status.update_stats(False, processing_time)
            
            # Fallback to basic processing
            return await self._fallback_chat_processing(message, session_id, conversation_context)
    
    async def process_voice_message(self,
                                  message: str,
                                  session_id: str = None,
                                  conversation_context: Optional[Dict[str, Any]] = None,
                                  audio_metadata: Optional[Dict[str, Any]] = None,
                                  use_intelligence: bool = True) -> Union[IntelligentResponse, VoiceResponse]:
        """
        Process voice message with intelligence upgrade.
        Falls back to existing voice processing if intelligence is unavailable.
        """
        
        start_time = time.time()
        
        try:
            # Use intelligence if available and enabled
            if use_intelligence and self.initialized and self.core_service:
                
                # Process with core intelligence service
                intelligent_response = await self.core_service.process_voice_chat(
                    query=message,
                    session_id=session_id,
                    conversation_context=conversation_context,
                    audio_metadata=audio_metadata
                )
                
                # Update success stats
                processing_time = (time.time() - start_time) * 1000
                self.upgrade_status.update_stats(True, processing_time)
                
                self.logger.info(f"Processed voice message with intelligence in {processing_time:.2f}ms")
                return intelligent_response
            
            else:
                # Fallback to existing voice processing
                return await self._fallback_voice_processing(message, session_id, conversation_context, audio_metadata)
                
        except Exception as e:
            self.logger.error(f"Intelligence voice processing failed: {e}")
            
            # Update failure stats
            processing_time = (time.time() - start_time) * 1000
            self.upgrade_status.update_stats(False, processing_time)
            
            # Fallback to existing voice processing
            return await self._fallback_voice_processing(message, session_id, conversation_context, audio_metadata)
    
    async def convert_to_voice_response(self, intelligent_response: IntelligentResponse) -> VoiceResponse:
        """Convert IntelligentResponse to VoiceResponse for backward compatibility"""
        
        try:
            # Convert visual citations to legacy format
            legacy_citations = []
            for citation in intelligent_response.visual_citations:
                legacy_citations.append({
                    'citation_id': citation.get('citation_id', ''),
                    'type': citation.get('type', 'general'),
                    'source': citation.get('source', ''),
                    'page': citation.get('page', 1),
                    'description': citation.get('description', ''),
                    'confidence': citation.get('confidence', 0.8)
                })
            
            # Create VoiceResponse
            voice_response = VoiceResponse(
                text_response=intelligent_response.text_response,
                audio_data=None,  # Will be filled by TTS
                should_continue_listening=True,
                next_voice_state=VoiceState.LISTENING,
                detected_intent=intelligent_response.detected_intent,
                context_updates=intelligent_response.conversation_context,
                conversation_complete=False,
                confidence_score=intelligent_response.confidence_score,
                suggested_follow_ups=intelligent_response.suggested_follow_ups,
                
                # Enhanced fields
                equipment_mentioned=self._extract_equipment_from_context(intelligent_response.conversation_context),
                safety_priority=intelligent_response.safety_priority,
                response_type=self._determine_response_type(intelligent_response.primary_agent),
                primary_agent=intelligent_response.primary_agent,
                contributing_agents=intelligent_response.contributing_agents,
                
                # Legacy visual citations
                visual_citations=legacy_citations
            )
            
            return voice_response
            
        except Exception as e:
            self.logger.error(f"Voice response conversion failed: {e}")
            
            # Create minimal voice response
            return VoiceResponse(
                text_response=intelligent_response.text_response,
                detected_intent=ConversationIntent.NEW_TOPIC,
                confidence_score=intelligent_response.confidence_score,
                should_continue_listening=True,
                next_voice_state=VoiceState.LISTENING,
                context_updates={},
                conversation_complete=False,
                suggested_follow_ups=[]
            )
    
    async def _fallback_chat_processing(self, 
                                      message: str,
                                      session_id: str,
                                      conversation_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback to basic chat processing"""
        
        self.logger.info("Using fallback chat processing")
        
        # Use Ragie if available
        if self.fallback_services['ragie_service']:
            try:
                ragie_service = self.fallback_services['ragie_service']
                ragie_result = await ragie_service.search_documents(
                    query=message,
                    limit=5,
                    hybrid_search=True
                )
                
                return {
                    'response': ragie_result.get('content', 'I can help with general QSR questions.'),
                    'sources': ragie_result.get('sources', []),
                    'confidence': ragie_result.get('confidence', 0.8),
                    'fallback_used': True,
                    'intelligence_available': False
                }
                
            except Exception as e:
                self.logger.error(f"Ragie fallback failed: {e}")
        
        # Basic fallback response
        return {
            'response': f"I received your message: {message}. I can help with general QSR questions.",
            'sources': [],
            'confidence': 0.5,
            'fallback_used': True,
            'intelligence_available': False
        }
    
    async def _fallback_voice_processing(self,
                                       message: str,
                                       session_id: str,
                                       conversation_context: Optional[Dict[str, Any]],
                                       audio_metadata: Optional[Dict[str, Any]]) -> VoiceResponse:
        """Fallback to existing voice processing"""
        
        self.logger.info("Using fallback voice processing")
        
        # Create basic voice response
        fallback_response = VoiceResponse(
            text_response=f"I can help with your question: {message}",
            detected_intent=ConversationIntent.NEW_TOPIC,
            confidence_score=0.6,
            should_continue_listening=True,
            next_voice_state=VoiceState.LISTENING,
            context_updates=conversation_context or {},
            conversation_complete=False,
            suggested_follow_ups=["Can you provide more details?", "Would you like help with something else?"]
        )
        
        # Try to enhance with Ragie if available
        if self.fallback_services['ragie_service']:
            try:
                ragie_service = self.fallback_services['ragie_service']
                ragie_result = await ragie_service.search_documents(
                    query=message,
                    limit=3,
                    hybrid_search=True
                )
                
                if ragie_result.get('content'):
                    fallback_response.text_response = ragie_result['content']
                    fallback_response.confidence_score = ragie_result.get('confidence', 0.8)
                
            except Exception as e:
                self.logger.error(f"Ragie enhancement failed: {e}")
        
        return fallback_response
    
    def _extract_equipment_from_context(self, context: Dict[str, Any]) -> Optional[str]:
        """Extract equipment mention from conversation context"""
        if 'equipment_mentioned' in context:
            equipment = context['equipment_mentioned']
            if isinstance(equipment, list) and equipment:
                return equipment[0]
            elif isinstance(equipment, str):
                return equipment
        return None
    
    def _determine_response_type(self, agent_type: AgentType) -> str:
        """Determine response type from agent type"""
        type_mapping = {
            AgentType.EQUIPMENT: "factual",
            AgentType.PROCEDURE: "procedural",
            AgentType.SAFETY: "safety",
            AgentType.MAINTENANCE: "procedural",
            AgentType.GENERAL: "factual"
        }
        return type_mapping.get(agent_type, "factual")
    
    # ===============================================================================
    # MONITORING AND MANAGEMENT
    # ===============================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            'integration_available': INTEGRATION_AVAILABLE,
            'initialized': self.initialized,
            'upgrade_status': self.upgrade_status.get_status_dict(),
            'core_service_available': self.core_service is not None,
            'fallback_services': {
                'ragie_available': self.fallback_services['ragie_service'] is not None,
                'citation_available': self.fallback_services['citation_service'] is not None
            }
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = {
            'integration_metrics': self.upgrade_status.get_status_dict()
        }
        
        # Add core service metrics if available
        if self.core_service:
            try:
                agent_metrics = self.core_service.get_performance_metrics()
                metrics['agent_metrics'] = agent_metrics
            except Exception as e:
                self.logger.error(f"Failed to get agent metrics: {e}")
        
        return metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health = {
            'status': 'healthy',
            'integration_available': INTEGRATION_AVAILABLE,
            'initialized': self.initialized,
            'core_service_healthy': False,
            'fallback_services_available': False,
            'issues': []
        }
        
        # Check core service health
        if self.core_service:
            try:
                core_health = await self.core_service.health_check()
                health['core_service_healthy'] = core_health.get('service_status') == 'healthy'
                health['core_service_details'] = core_health
            except Exception as e:
                health['issues'].append(f"Core service health check failed: {e}")
        
        # Check fallback services
        fallback_available = any(service is not None for service in self.fallback_services.values())
        health['fallback_services_available'] = fallback_available
        
        # Determine overall status
        if not self.initialized and not fallback_available:
            health['status'] = 'unhealthy'
            health['issues'].append("Neither intelligence nor fallback services available")
        elif not self.initialized:
            health['status'] = 'degraded'
            health['issues'].append("Intelligence unavailable, using fallback services")
        
        return health
    
    def enable_intelligence(self):
        """Enable intelligence upgrade"""
        if self.initialized:
            self.upgrade_status.enabled = True
            self.logger.info("Intelligence upgrade enabled")
    
    def disable_intelligence(self):
        """Disable intelligence upgrade (use fallback only)"""
        self.upgrade_status.enabled = False
        self.logger.info("Intelligence upgrade disabled, using fallback")
    
    def toggle_intelligence(self) -> bool:
        """Toggle intelligence upgrade"""
        if self.upgrade_status.enabled:
            self.disable_intelligence()
        else:
            self.enable_intelligence()
        return self.upgrade_status.enabled

# ===============================================================================
# GLOBAL INTEGRATION INSTANCE
# ===============================================================================

# Global integration instance
_intelligence_integration = None

async def get_intelligence_integration() -> IntelligenceIntegration:
    """Get or create global intelligence integration instance"""
    global _intelligence_integration
    
    if _intelligence_integration is None:
        _intelligence_integration = IntelligenceIntegration()
    
    return _intelligence_integration

async def initialize_intelligence_integration(
    ragie_service: Any = None,
    citation_service: Any = None,
    conversation_context: Any = None
) -> bool:
    """Initialize global intelligence integration"""
    
    integration = await get_intelligence_integration()
    return await integration.initialize(
        ragie_service=ragie_service,
        citation_service=citation_service,
        conversation_context=conversation_context
    )

# ===============================================================================
# ENDPOINT INTEGRATION HELPERS
# ===============================================================================

async def enhance_chat_endpoint(
    message: str,
    session_id: str = None,
    conversation_context: Optional[Dict[str, Any]] = None,
    use_intelligence: bool = True
) -> Dict[str, Any]:
    """
    Enhance chat endpoint with intelligence.
    Drop-in replacement for basic chat processing.
    """
    
    integration = await get_intelligence_integration()
    
    # Process message with intelligence
    result = await integration.process_chat_message(
        message=message,
        session_id=session_id,
        conversation_context=conversation_context,
        use_intelligence=use_intelligence
    )
    
    # Convert to standard response format
    if isinstance(result, IntelligentResponse):
        return {
            'response': result.text_response,
            'confidence': result.confidence_score,
            'agent_type': result.primary_agent.value,
            'visual_citations': result.visual_citations,
            'safety_priority': result.safety_priority,
            'safety_warnings': result.safety_warnings,
            'suggested_follow_ups': result.suggested_follow_ups,
            'generation_time_ms': result.generation_time_ms,
            'intelligence_used': True
        }
    else:
        # Fallback result
        return {
            'response': result.get('response', ''),
            'confidence': result.get('confidence', 0.5),
            'agent_type': 'general',
            'visual_citations': [],
            'safety_priority': False,
            'safety_warnings': [],
            'suggested_follow_ups': [],
            'generation_time_ms': 0,
            'intelligence_used': False,
            'fallback_used': result.get('fallback_used', True)
        }

async def enhance_voice_endpoint(
    message: str,
    session_id: str = None,
    conversation_context: Optional[Dict[str, Any]] = None,
    audio_metadata: Optional[Dict[str, Any]] = None,
    use_intelligence: bool = True
) -> VoiceResponse:
    """
    Enhance voice endpoint with intelligence.
    Drop-in replacement for basic voice processing.
    """
    
    integration = await get_intelligence_integration()
    
    # Process message with intelligence
    result = await integration.process_voice_message(
        message=message,
        session_id=session_id,
        conversation_context=conversation_context,
        audio_metadata=audio_metadata,
        use_intelligence=use_intelligence
    )
    
    # Convert to VoiceResponse if needed
    if isinstance(result, IntelligentResponse):
        return await integration.convert_to_voice_response(result)
    else:
        return result

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Core integration
    "IntelligenceIntegration",
    "IntelligenceUpgradeStatus",
    
    # Global functions
    "get_intelligence_integration",
    "initialize_intelligence_integration",
    
    # Endpoint helpers
    "enhance_chat_endpoint",
    "enhance_voice_endpoint"
]