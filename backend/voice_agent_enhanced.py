#!/usr/bin/env python3
"""
Enhanced Voice Agent with Ragie Integration
==========================================

Enhances the existing voice system with Ragie intelligence while preserving
all existing voice architecture and functionality. Integrates Ragie tools
for enhanced knowledge retrieval and context-aware responses.

Key Features:
- Preserves existing VoiceOrchestrator structure
- Maintains ConversationContext and voice optimization
- Integrates Ragie tools for enhanced knowledge
- Adds visual citation coordination
- Voice-optimized Ragie responses
- Multi-agent voice enhancement

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Import existing voice architecture
from voice_agent import (
    VoiceOrchestrator, ConversationContext, VoiceResponse, VoiceState,
    ConversationIntent, AgentType, AgentCoordinationStrategy,
    SpecializedAgentResponse
)

# Import Ragie tools
try:
    from tools.ragie_tools import (
        ragie_tools,
        ToolExecutionContext,
        search_ragie_knowledge,
        extract_ragie_visual,
        get_ragie_equipment_info,
        get_ragie_procedure_info,
        get_ragie_safety_info,
        RagieKnowledgeResult,
        RagieVisualResult,
        RagieEquipmentResult,
        RagieProcedureResult,
        RagieSafetyResult
    )
    RAGIE_TOOLS_AVAILABLE = True
except ImportError:
    RAGIE_TOOLS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===============================================================================
# ENHANCED VOICE RESPONSE MODELS
# ===============================================================================

class RagieEnhancedVoiceResponse(VoiceResponse):
    """Enhanced voice response with Ragie intelligence"""
    
    # Ragie integration fields
    ragie_knowledge_used: bool = False
    ragie_confidence: float = 0.0
    ragie_sources: List[Dict[str, Any]] = Field(default_factory=list)
    ragie_visual_citations: List[Dict[str, Any]] = Field(default_factory=list)
    ragie_execution_time_ms: float = 0.0
    
    # Enhanced context fields
    knowledge_type: Optional[str] = None
    equipment_context: Optional[Dict[str, Any]] = None
    procedure_context: Optional[Dict[str, Any]] = None
    safety_context: Optional[Dict[str, Any]] = None
    
    # Voice optimization fields
    voice_optimized_response: Optional[str] = None
    citation_descriptions: List[str] = Field(default_factory=list)
    simplified_for_voice: bool = False

class RagieVoiceContext(BaseModel):
    """Extended context for Ragie-enhanced voice interactions"""
    
    # Ragie session context
    ragie_session_id: str
    ragie_query_history: List[Dict[str, Any]] = Field(default_factory=list)
    ragie_knowledge_cache: Dict[str, Any] = Field(default_factory=dict)
    
    # Voice-specific Ragie context
    last_ragie_query: Optional[str] = None
    last_ragie_result: Optional[Dict[str, Any]] = None
    ragie_context_depth: int = 0
    
    # Equipment and procedure context from Ragie
    current_ragie_equipment: Optional[str] = None
    current_ragie_procedure: Optional[str] = None
    ragie_safety_warnings: List[str] = Field(default_factory=list)
    
    # Performance tracking
    ragie_total_queries: int = 0
    ragie_avg_response_time: float = 0.0
    ragie_success_rate: float = 1.0

# ===============================================================================
# ENHANCED VOICE ORCHESTRATOR
# ===============================================================================

class RagieEnhancedVoiceOrchestrator(VoiceOrchestrator):
    """Enhanced voice orchestrator with Ragie integration"""
    
    def __init__(self):
        super().__init__()
        self.ragie_contexts: Dict[str, RagieVoiceContext] = {}
        self.ragie_performance_metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'avg_response_time': 0.0,
            'knowledge_cache_hits': 0,
            'voice_optimizations': 0
        }
        
        # Initialize Ragie tools availability
        self.ragie_available = RAGIE_TOOLS_AVAILABLE
        if self.ragie_available:
            logger.info("✅ Ragie tools available for voice enhancement")
        else:
            logger.warning("⚠️ Ragie tools not available - using fallback mode")
    
    def get_ragie_context(self, session_id: str) -> RagieVoiceContext:
        """Get or create Ragie context for session"""
        if session_id not in self.ragie_contexts:
            self.ragie_contexts[session_id] = RagieVoiceContext(
                ragie_session_id=f"voice_{session_id}_{int(time.time())}"
            )
        return self.ragie_contexts[session_id]
    
    async def process_voice_message_with_ragie(
        self, 
        message: str, 
        relevant_docs: List[Dict] = None,
        session_id: str = None
    ) -> RagieEnhancedVoiceResponse:
        """Process voice message with Ragie intelligence enhancement"""
        
        start_time = time.time()
        session_id = session_id or self.default_session
        
        # Get existing contexts
        context = self.get_context(session_id)
        ragie_context = self.get_ragie_context(session_id)
        
        # First process with existing voice orchestrator
        base_response = await super().process_voice_message(message, relevant_docs, session_id)
        
        # If Ragie tools are not available, return enhanced base response
        if not self.ragie_available:
            return self._convert_to_enhanced_response(base_response, ragie_used=False)
        
        # Enhance with Ragie intelligence
        try:
            enhanced_response = await self._enhance_with_ragie(
                message, base_response, context, ragie_context
            )
            
            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            self._update_ragie_metrics(processing_time, True)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Ragie enhancement failed: {e}")
            
            # Update metrics for failure
            processing_time = (time.time() - start_time) * 1000
            self._update_ragie_metrics(processing_time, False)
            
            # Return base response with error context
            return self._convert_to_enhanced_response(base_response, ragie_used=False)
    
    async def _enhance_with_ragie(
        self, 
        message: str, 
        base_response: VoiceResponse, 
        context: ConversationContext, 
        ragie_context: RagieVoiceContext
    ) -> RagieEnhancedVoiceResponse:
        """Enhance voice response with Ragie intelligence"""
        
        # Create tool execution context
        tool_context = ToolExecutionContext(
            query=message,
            interaction_mode="voice",
            equipment_context=context.current_entity,
            safety_priority=base_response.safety_priority,
            session_id=ragie_context.ragie_session_id,
            conversation_history=self._convert_conversation_history(context.conversation_history)
        )
        
        # Determine which Ragie tool to use based on base response
        ragie_result = await self._select_and_execute_ragie_tool(
            base_response, tool_context, ragie_context
        )
        
        # Enhance base response with Ragie intelligence
        enhanced_response = await self._merge_ragie_with_voice_response(
            base_response, ragie_result, context, ragie_context
        )
        
        # Optimize response for voice
        enhanced_response = await self._optimize_for_voice_output(enhanced_response)
        
        # Update Ragie context
        await self._update_ragie_context(ragie_context, message, ragie_result)
        
        return enhanced_response
    
    async def _select_and_execute_ragie_tool(
        self, 
        base_response: VoiceResponse, 
        tool_context: ToolExecutionContext,
        ragie_context: RagieVoiceContext
    ) -> Union[RagieKnowledgeResult, RagieEquipmentResult, RagieProcedureResult, RagieSafetyResult, RagieVisualResult]:
        """Select and execute appropriate Ragie tool based on voice response"""
        
        query = tool_context.query
        
        # Check cache first
        cache_key = f"{query}_{tool_context.equipment_context}_{base_response.primary_agent.value}"
        if cache_key in ragie_context.ragie_knowledge_cache:
            self.ragie_performance_metrics['knowledge_cache_hits'] += 1
            return ragie_context.ragie_knowledge_cache[cache_key]
        
        # Select tool based on primary agent and response type
        if base_response.safety_priority or base_response.primary_agent == AgentType.SAFETY:
            logger.info("🛡️ Using Ragie safety tool for voice enhancement")
            result = await get_ragie_safety_info(query, tool_context)
            
        elif base_response.primary_agent == AgentType.EQUIPMENT or base_response.equipment_mentioned:
            logger.info("⚙️ Using Ragie equipment tool for voice enhancement")
            equipment_name = base_response.equipment_mentioned or tool_context.equipment_context or "equipment"
            result = await get_ragie_equipment_info(equipment_name, tool_context)
            
        elif base_response.primary_agent == AgentType.PROCEDURE or base_response.response_type == "procedural":
            logger.info("📋 Using Ragie procedure tool for voice enhancement")
            procedure_name = self._extract_procedure_name(query, base_response)
            result = await get_ragie_procedure_info(procedure_name, tool_context)
            
        elif "visual" in query.lower() or "show" in query.lower():
            logger.info("📸 Using Ragie visual tool for voice enhancement")
            result = await extract_ragie_visual(query, tool_context)
            
        else:
            logger.info("🧠 Using Ragie knowledge tool for voice enhancement")
            result = await search_ragie_knowledge(query, tool_context)
        
        # Cache the result
        ragie_context.ragie_knowledge_cache[cache_key] = result
        
        return result
    
    async def _merge_ragie_with_voice_response(
        self,
        base_response: VoiceResponse,
        ragie_result: Any,
        context: ConversationContext,
        ragie_context: RagieVoiceContext
    ) -> RagieEnhancedVoiceResponse:
        """Merge Ragie intelligence with voice response"""
        
        # Create enhanced response
        enhanced_response = RagieEnhancedVoiceResponse(
            **base_response.dict(),
            ragie_knowledge_used=ragie_result.success,
            ragie_confidence=ragie_result.confidence,
            ragie_sources=ragie_result.sources,
            ragie_visual_citations=ragie_result.visual_citations,
            ragie_execution_time_ms=ragie_result.execution_time_ms
        )
        
        # Enhance text response with Ragie knowledge
        if ragie_result.success and ragie_result.content:
            enhanced_response.text_response = await self._enhance_text_with_ragie_knowledge(
                base_response.text_response, 
                ragie_result,
                context
            )
        
        # Add Ragie-specific context
        if isinstance(ragie_result, RagieEquipmentResult):
            enhanced_response.equipment_context = {
                'equipment_name': ragie_result.equipment_name,
                'equipment_type': ragie_result.equipment_type,
                'maintenance_required': ragie_result.maintenance_required,
                'safety_level': ragie_result.safety_level,
                'troubleshooting_steps': ragie_result.troubleshooting_steps
            }
            enhanced_response.knowledge_type = "equipment"
            
        elif isinstance(ragie_result, RagieProcedureResult):
            enhanced_response.procedure_context = {
                'procedure_name': ragie_result.procedure_name,
                'step_count': ragie_result.step_count,
                'estimated_time': ragie_result.estimated_time,
                'difficulty_level': ragie_result.difficulty_level,
                'procedure_steps': ragie_result.procedure_steps
            }
            enhanced_response.knowledge_type = "procedure"
            
        elif isinstance(ragie_result, RagieSafetyResult):
            enhanced_response.safety_context = {
                'safety_level': ragie_result.safety_level,
                'risk_factors': ragie_result.risk_factors,
                'emergency_procedures': ragie_result.emergency_procedures,
                'immediate_actions': ragie_result.immediate_actions
            }
            enhanced_response.knowledge_type = "safety"
            enhanced_response.safety_priority = True
            
        elif isinstance(ragie_result, RagieKnowledgeResult):
            enhanced_response.knowledge_type = ragie_result.knowledge_type
        
        # Add safety warnings from Ragie
        if ragie_result.safety_warnings:
            enhanced_response.safety_priority = True
            ragie_context.ragie_safety_warnings.extend(ragie_result.safety_warnings)
        
        # Add suggested actions
        if ragie_result.suggested_actions:
            enhanced_response.suggested_follow_ups.extend(ragie_result.suggested_actions)
        
        return enhanced_response
    
    async def _enhance_text_with_ragie_knowledge(
        self,
        base_text: str,
        ragie_result: Any,
        context: ConversationContext
    ) -> str:
        """Enhance voice response text with Ragie knowledge"""
        
        # If Ragie has more detailed or accurate information, blend it with base response
        if ragie_result.confidence > 0.7 and len(ragie_result.content) > 50:
            
            # Extract key insights from Ragie content
            key_insights = self._extract_voice_friendly_insights(ragie_result.content)
            
            # Blend with base response
            if key_insights:
                enhanced_text = f"{base_text} Based on the manual: {key_insights}"
                
                # Keep within voice response length limits
                if len(enhanced_text) > 200:
                    enhanced_text = enhanced_text[:200] + "..."
                
                return enhanced_text
        
        return base_text
    
    def _extract_voice_friendly_insights(self, ragie_content: str) -> str:
        """Extract voice-friendly insights from Ragie content"""
        
        # Extract key sentences that are voice-friendly
        sentences = ragie_content.split('.')
        voice_friendly_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip very short or very long sentences
            if len(sentence) < 10 or len(sentence) > 100:
                continue
            
            # Skip sentences with too many technical terms
            if sentence.count('_') > 2 or sentence.count('.pdf') > 0:
                continue
            
            # Prefer sentences with action words
            if any(action in sentence.lower() for action in ['turn', 'check', 'ensure', 'clean', 'set']):
                voice_friendly_sentences.append(sentence)
            
            # Limit to 2 sentences for voice
            if len(voice_friendly_sentences) >= 2:
                break
        
        return '. '.join(voice_friendly_sentences)
    
    async def _optimize_for_voice_output(
        self, 
        enhanced_response: RagieEnhancedVoiceResponse
    ) -> RagieEnhancedVoiceResponse:
        """Optimize response for voice output"""
        
        # Create voice-optimized version of response
        voice_optimized_text = self._create_voice_optimized_text(enhanced_response.text_response)
        
        # Create voice-friendly citation descriptions
        citation_descriptions = self._create_voice_citation_descriptions(enhanced_response.ragie_visual_citations)
        
        # Update response with voice optimizations
        enhanced_response.voice_optimized_response = voice_optimized_text
        enhanced_response.citation_descriptions = citation_descriptions
        enhanced_response.simplified_for_voice = True
        
        # If voice optimization is significantly different, use it
        if len(voice_optimized_text) > 0 and voice_optimized_text != enhanced_response.text_response:
            enhanced_response.text_response = voice_optimized_text
            self.ragie_performance_metrics['voice_optimizations'] += 1
        
        return enhanced_response
    
    def _create_voice_optimized_text(self, text: str) -> str:
        """Create voice-optimized version of text"""
        
        # Remove technical references that don't work well in voice
        voice_text = text.replace('.pdf', '')
        voice_text = voice_text.replace('_', ' ')
        
        # Replace technical terms with voice-friendly alternatives
        replacements = {
            'equipment': 'machine',
            'procedure': 'process',
            'documentation': 'manual',
            'specifications': 'details',
            'maintenance': 'upkeep'
        }
        
        for technical, friendly in replacements.items():
            voice_text = voice_text.replace(technical, friendly)
        
        # Ensure proper sentence structure for voice
        sentences = voice_text.split('.')
        voice_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                # Ensure sentence ends properly
                if not sentence.endswith('.'):
                    sentence += '.'
                voice_sentences.append(sentence)
        
        return ' '.join(voice_sentences)
    
    def _create_voice_citation_descriptions(self, visual_citations: List[Dict[str, Any]]) -> List[str]:
        """Create voice-friendly descriptions of visual citations"""
        
        descriptions = []
        
        for citation in visual_citations:
            citation_type = citation.get('type', 'reference')
            source = citation.get('source', 'manual')
            title = citation.get('title', citation_type)
            
            # Create voice-friendly description
            if citation_type == 'image':
                description = f"There's an image in the {source} showing {title.lower()}"
            elif citation_type == 'diagram':
                description = f"Check the diagram in the {source} for {title.lower()}"
            elif citation_type == 'table':
                description = f"The {source} has a table with {title.lower()}"
            else:
                description = f"See the {source} for more on {title.lower()}"
            
            descriptions.append(description)
        
        return descriptions
    
    def _extract_procedure_name(self, query: str, base_response: VoiceResponse) -> str:
        """Extract procedure name from query and response"""
        
        # Look for procedure keywords in query
        procedure_keywords = {
            'clean': 'cleaning',
            'maintenance': 'maintenance',
            'repair': 'repair',
            'troubleshoot': 'troubleshooting',
            'operate': 'operation',
            'setup': 'setup'
        }
        
        query_lower = query.lower()
        
        for keyword, procedure in procedure_keywords.items():
            if keyword in query_lower:
                # If equipment is mentioned, combine
                if base_response.equipment_mentioned:
                    return f"{base_response.equipment_mentioned} {procedure}"
                return procedure
        
        # Default to generic procedure
        return "procedure"
    
    def _convert_conversation_history(self, history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Convert voice conversation history to tool context format"""
        
        converted_history = []
        
        for entry in history:
            converted_entry = {
                'query': entry.get('user', ''),
                'response': entry.get('assistant', ''),
                'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                'type': 'voice_interaction'
            }
            converted_history.append(converted_entry)
        
        return converted_history
    
    async def _update_ragie_context(
        self, 
        ragie_context: RagieVoiceContext,
        message: str,
        ragie_result: Any
    ):
        """Update Ragie context with query results"""
        
        # Add to query history
        ragie_context.ragie_query_history.append({
            'query': message,
            'result_type': type(ragie_result).__name__,
            'success': ragie_result.success,
            'confidence': ragie_result.confidence,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update context state
        ragie_context.last_ragie_query = message
        ragie_context.last_ragie_result = ragie_result.dict()
        ragie_context.ragie_total_queries += 1
        
        # Update average response time
        if ragie_result.execution_time_ms > 0:
            ragie_context.ragie_avg_response_time = (
                (ragie_context.ragie_avg_response_time * (ragie_context.ragie_total_queries - 1) + 
                 ragie_result.execution_time_ms) / ragie_context.ragie_total_queries
            )
        
        # Update equipment/procedure context
        if isinstance(ragie_result, RagieEquipmentResult):
            ragie_context.current_ragie_equipment = ragie_result.equipment_name
            
        elif isinstance(ragie_result, RagieProcedureResult):
            ragie_context.current_ragie_procedure = ragie_result.procedure_name
        
        # Update safety warnings
        if ragie_result.safety_warnings:
            ragie_context.ragie_safety_warnings.extend(ragie_result.safety_warnings)
        
        # Update success rate
        successful_queries = sum(1 for entry in ragie_context.ragie_query_history if entry['success'])
        ragie_context.ragie_success_rate = successful_queries / ragie_context.ragie_total_queries
    
    def _convert_to_enhanced_response(self, base_response: VoiceResponse, ragie_used: bool = False) -> RagieEnhancedVoiceResponse:
        """Convert base VoiceResponse to RagieEnhancedVoiceResponse"""
        
        return RagieEnhancedVoiceResponse(
            **base_response.dict(),
            ragie_knowledge_used=ragie_used,
            ragie_confidence=0.0,
            ragie_sources=[],
            ragie_visual_citations=[],
            ragie_execution_time_ms=0.0,
            voice_optimized_response=base_response.text_response,
            simplified_for_voice=False
        )
    
    def _update_ragie_metrics(self, processing_time: float, success: bool):
        """Update Ragie performance metrics"""
        
        self.ragie_performance_metrics['total_queries'] += 1
        
        if success:
            self.ragie_performance_metrics['successful_queries'] += 1
        
        # Update average response time
        current_total = self.ragie_performance_metrics['total_queries']
        current_avg = self.ragie_performance_metrics['avg_response_time']
        
        self.ragie_performance_metrics['avg_response_time'] = (
            (current_avg * (current_total - 1) + processing_time) / current_total
        )
    
    def get_ragie_performance_metrics(self) -> Dict[str, Any]:
        """Get Ragie performance metrics"""
        
        total_queries = self.ragie_performance_metrics['total_queries']
        successful_queries = self.ragie_performance_metrics['successful_queries']
        
        return {
            'ragie_available': self.ragie_available,
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': successful_queries / max(total_queries, 1),
            'avg_response_time_ms': self.ragie_performance_metrics['avg_response_time'],
            'knowledge_cache_hits': self.ragie_performance_metrics['knowledge_cache_hits'],
            'voice_optimizations': self.ragie_performance_metrics['voice_optimizations'],
            'active_sessions': len(self.ragie_contexts)
        }
    
    async def get_ragie_health_check(self) -> Dict[str, Any]:
        """Get Ragie health check information"""
        
        health_info = {
            'ragie_tools_available': self.ragie_available,
            'performance_metrics': self.get_ragie_performance_metrics(),
            'active_sessions': len(self.ragie_contexts),
            'cache_efficiency': 0.0
        }
        
        # Calculate cache efficiency
        total_queries = self.ragie_performance_metrics['total_queries']
        cache_hits = self.ragie_performance_metrics['knowledge_cache_hits']
        
        if total_queries > 0:
            health_info['cache_efficiency'] = cache_hits / total_queries
        
        # Get tool-specific health
        if self.ragie_available:
            health_info['tool_health'] = ragie_tools.health_check()
        
        return health_info
    
    # ===============================================================================
    # BACKWARD COMPATIBILITY METHODS
    # ===============================================================================
    
    async def process_voice_message(
        self, 
        message: str, 
        relevant_docs: List[Dict] = None,
        session_id: str = None
    ) -> VoiceResponse:
        """Backward compatible voice message processing"""
        
        # Use enhanced processing if available
        if self.ragie_available:
            enhanced_response = await self.process_voice_message_with_ragie(
                message, relevant_docs, session_id
            )
            
            # Convert enhanced response to base response for backward compatibility
            return VoiceResponse(
                text_response=enhanced_response.text_response,
                audio_data=enhanced_response.audio_data,
                should_continue_listening=enhanced_response.should_continue_listening,
                next_voice_state=enhanced_response.next_voice_state,
                detected_intent=enhanced_response.detected_intent,
                context_updates=enhanced_response.context_updates,
                conversation_complete=enhanced_response.conversation_complete,
                confidence_score=enhanced_response.confidence_score,
                suggested_follow_ups=enhanced_response.suggested_follow_ups,
                requires_document_lookup=enhanced_response.requires_document_lookup,
                document_query=enhanced_response.document_query,
                equipment_mentioned=enhanced_response.equipment_mentioned,
                equipment_switch_detected=enhanced_response.equipment_switch_detected,
                procedure_step_info=enhanced_response.procedure_step_info,
                workflow_phase=enhanced_response.workflow_phase,
                safety_priority=enhanced_response.safety_priority,
                response_type=enhanced_response.response_type,
                context_references=enhanced_response.context_references,
                hands_free_recommendation=enhanced_response.hands_free_recommendation,
                parsed_steps=enhanced_response.parsed_steps,
                primary_agent=enhanced_response.primary_agent,
                contributing_agents=enhanced_response.contributing_agents,
                coordination_strategy=enhanced_response.coordination_strategy,
                agent_confidence_scores=enhanced_response.agent_confidence_scores,
                specialized_insights=enhanced_response.specialized_insights
            )
        
        # Fallback to base implementation
        return await super().process_voice_message(message, relevant_docs, session_id)
    
    async def process_message(
        self, 
        message: str, 
        relevant_docs: List[Dict] = None,
        session_id: str = None,
        message_type: str = "text"
    ) -> VoiceResponse:
        """Backward compatible message processing for text and voice"""
        
        # Use enhanced processing with Ragie
        if self.ragie_available:
            enhanced_response = await self.process_voice_message_with_ragie(
                message, relevant_docs, session_id
            )
            
            # Adjust for message type
            if message_type == "text":
                enhanced_response.should_continue_listening = False
                enhanced_response.hands_free_recommendation = False
            
            # Convert to base response for backward compatibility
            return self._convert_enhanced_to_base_response(enhanced_response)
        
        # Fallback to base implementation
        return await super().process_message(message, relevant_docs, session_id, message_type)
    
    def _convert_enhanced_to_base_response(self, enhanced_response: RagieEnhancedVoiceResponse) -> VoiceResponse:
        """Convert enhanced response to base response for backward compatibility"""
        
        return VoiceResponse(
            text_response=enhanced_response.text_response,
            audio_data=enhanced_response.audio_data,
            should_continue_listening=enhanced_response.should_continue_listening,
            next_voice_state=enhanced_response.next_voice_state,
            detected_intent=enhanced_response.detected_intent,
            context_updates=enhanced_response.context_updates,
            conversation_complete=enhanced_response.conversation_complete,
            confidence_score=enhanced_response.confidence_score,
            suggested_follow_ups=enhanced_response.suggested_follow_ups,
            requires_document_lookup=enhanced_response.requires_document_lookup,
            document_query=enhanced_response.document_query,
            equipment_mentioned=enhanced_response.equipment_mentioned,
            equipment_switch_detected=enhanced_response.equipment_switch_detected,
            procedure_step_info=enhanced_response.procedure_step_info,
            workflow_phase=enhanced_response.workflow_phase,
            safety_priority=enhanced_response.safety_priority,
            response_type=enhanced_response.response_type,
            context_references=enhanced_response.context_references,
            hands_free_recommendation=enhanced_response.hands_free_recommendation,
            parsed_steps=enhanced_response.parsed_steps,
            primary_agent=enhanced_response.primary_agent,
            contributing_agents=enhanced_response.contributing_agents,
            coordination_strategy=enhanced_response.coordination_strategy,
            agent_confidence_scores=enhanced_response.agent_confidence_scores,
            specialized_insights=enhanced_response.specialized_insights
        )

# ===============================================================================
# GLOBAL ENHANCED ORCHESTRATOR
# ===============================================================================

# Global enhanced voice orchestrator instance
enhanced_voice_orchestrator = RagieEnhancedVoiceOrchestrator()

# ===============================================================================
# CONVENIENCE FUNCTIONS
# ===============================================================================

async def process_enhanced_voice_message(
    message: str, 
    relevant_docs: List[Dict] = None,
    session_id: str = None
) -> RagieEnhancedVoiceResponse:
    """Convenience function for enhanced voice processing"""
    
    return await enhanced_voice_orchestrator.process_voice_message_with_ragie(
        message, relevant_docs, session_id
    )

async def get_enhanced_voice_health() -> Dict[str, Any]:
    """Get enhanced voice system health information"""
    
    return await enhanced_voice_orchestrator.get_ragie_health_check()

def get_enhanced_voice_metrics() -> Dict[str, Any]:
    """Get enhanced voice system metrics"""
    
    return enhanced_voice_orchestrator.get_ragie_performance_metrics()

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    'RagieEnhancedVoiceOrchestrator',
    'RagieEnhancedVoiceResponse',
    'RagieVoiceContext',
    'enhanced_voice_orchestrator',
    'process_enhanced_voice_message',
    'get_enhanced_voice_health',
    'get_enhanced_voice_metrics'
]