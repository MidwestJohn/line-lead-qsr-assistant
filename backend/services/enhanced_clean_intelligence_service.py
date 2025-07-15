"""
Enhanced Clean Intelligence Service with Universal Response Models
================================================================

Enhanced version of the clean intelligence service that integrates with
universal response models for consistent Ragie + PydanticAI responses
across text and voice interactions.

CLEAN IMPLEMENTATION: Uses ONLY Ragie + PydanticAI, no Graph-RAG dependencies.

Author: Generated with Memex (https://memex.tech)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import logging
import time
import asyncio
from datetime import datetime
import hashlib

# Import clean intelligence base
from services.clean_intelligence_service import CleanIntelligenceService, CleanQSRAgent
from models.universal_response_models import (
    UniversalQSRResponse, TextChatResponse, VoiceResponse, HybridResponse,
    RagieKnowledge, RagieCitation, RagieEquipmentContext, RagieProcedureContext,
    RagieContext, AgentType, InteractionMode, ResponseFormat, ConversationIntent,
    SafetyLevel, UniversalResponseFactory, ResponseAdapter, ResponseMetrics
)

# Import existing services
try:
    from services.ragie_service_clean import RagieService
    from services.multimodal_citation_service import MultiModalCitationService
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===============================================================================
# ENHANCED CLEAN AGENT WITH UNIVERSAL RESPONSES
# ===============================================================================

class EnhancedCleanQSRAgent(CleanQSRAgent):
    """Enhanced clean QSR agent with universal response models"""
    
    def __init__(self, agent_type: AgentType, ragie_service: Any, citation_service: Any = None):
        super().__init__(agent_type, ragie_service, citation_service)
        self.response_metrics = ResponseMetrics()
    
    async def process_universal_query(self, 
                                    query: str,
                                    interaction_mode: InteractionMode,
                                    response_format: ResponseFormat,
                                    session_id: str = None,
                                    equipment_mentioned: List[str] = None,
                                    conversation_history: List[Dict[str, Any]] = None) -> UniversalQSRResponse:
        """Process query with universal response models"""
        
        start_time = time.time()
        
        try:
            # Create Ragie context
            ragie_context = await self._create_ragie_context(
                session_id or "default",
                interaction_mode,
                equipment_mentioned,
                conversation_history
            )
            
            # Query Ragie for knowledge
            ragie_start = time.time()
            ragie_response = await self._query_ragie_enhanced(query, ragie_context)
            ragie_time = (time.time() - ragie_start) * 1000
            
            # Create Ragie knowledge objects
            knowledge_sources = await self._create_ragie_knowledge(query, ragie_response)
            
            # Update Ragie context with knowledge
            for knowledge in knowledge_sources:
                ragie_context.add_ragie_knowledge(knowledge)
            
            # Extract enhanced visual citations
            visual_citations = await self._extract_enhanced_citations(query, ragie_response)
            
            # Add citations to context
            ragie_context.visual_citations.extend(visual_citations)
            
            # Create equipment context if relevant
            equipment_context = await self._create_equipment_context(query, ragie_response, equipment_mentioned)
            if equipment_context:
                ragie_context.equipment_context = equipment_context
            
            # Create procedure context if relevant
            procedure_context = await self._create_procedure_context(query, ragie_response)
            if procedure_context:
                ragie_context.procedure_context = procedure_context
            
            # Generate enhanced response
            response_text = await self._generate_enhanced_response(query, ragie_response)
            
            # Analyze safety level
            safety_level, safety_warnings = await self._analyze_enhanced_safety(query, ragie_response)
            
            # Determine conversation intent
            intent = self._determine_conversation_intent(query)
            
            # Calculate performance metrics
            generation_time = (time.time() - start_time) * 1000
            total_time = generation_time
            
            # Create response based on format
            if response_format == ResponseFormat.TEXT_UI:
                response = UniversalResponseFactory.create_text_response(
                    text_response=response_text,
                    agent_type=self.agent_type,
                    ragie_context=ragie_context,
                    knowledge_sources=knowledge_sources,
                    visual_citations=visual_citations,
                    confidence_score=ragie_response.get('confidence', 0.8),
                    safety_level=safety_level,
                    safety_warnings=safety_warnings,
                    generation_time_ms=generation_time,
                    ragie_query_time_ms=ragie_time,
                    total_processing_time_ms=total_time
                )
                
                # Add text-specific enhancements
                if isinstance(response, TextChatResponse):
                    response.suggested_follow_ups = self._generate_follow_ups_enhanced(query, ragie_response)
                    response.format_for_ui()
                
            elif response_format == ResponseFormat.VOICE_AUDIO:
                response = UniversalResponseFactory.create_voice_response(
                    text_response=response_text,
                    agent_type=self.agent_type,
                    ragie_context=ragie_context,
                    knowledge_sources=knowledge_sources,
                    visual_citations=visual_citations,
                    confidence_score=ragie_response.get('confidence', 0.8),
                    safety_level=safety_level,
                    safety_warnings=safety_warnings,
                    generation_time_ms=generation_time,
                    ragie_query_time_ms=ragie_time,
                    total_processing_time_ms=total_time
                )
                
                # Add voice-specific enhancements
                if isinstance(response, VoiceResponse):
                    response.optimize_for_speech()
                
            else:  # HYBRID
                response = UniversalResponseFactory.create_hybrid_response(
                    text_response=response_text,
                    agent_type=self.agent_type,
                    ragie_context=ragie_context,
                    knowledge_sources=knowledge_sources,
                    visual_citations=visual_citations,
                    confidence_score=ragie_response.get('confidence', 0.8),
                    safety_level=safety_level,
                    safety_warnings=safety_warnings,
                    generation_time_ms=generation_time,
                    ragie_query_time_ms=ragie_time,
                    total_processing_time_ms=total_time,
                    primary_mode=interaction_mode
                )
            
            # Set final response properties
            response.detected_intent = intent
            response.interaction_mode = interaction_mode
            
            # Update metrics
            self.response_metrics.update_with_response(response)
            
            self.logger.info(f"Generated {response_format.value} response in {total_time:.2f}ms")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Enhanced query processing failed: {e}")
            return await self._create_error_response(str(e), interaction_mode, response_format)
    
    async def _create_ragie_context(self, 
                                  session_id: str,
                                  interaction_mode: InteractionMode,
                                  equipment_mentioned: List[str] = None,
                                  conversation_history: List[Dict[str, Any]] = None) -> RagieContext:
        """Create Ragie context for the query"""
        
        return RagieContext(
            session_id=session_id,
            interaction_mode=interaction_mode,
            agent_type=self.agent_type,
            conversation_history=conversation_history or []
        )
    
    async def _query_ragie_enhanced(self, query: str, context: RagieContext) -> Dict[str, Any]:
        """Enhanced Ragie query with context"""
        
        # Use parent class method
        enhanced_query = self._enhance_query_for_agent_context(query, context)
        
        try:
            ragie_result = await self.ragie_service.search_documents(
                query=enhanced_query,
                limit=10,
                hybrid_search=True
            )
            
            return {
                'content': ragie_result.get('content', ''),
                'confidence': ragie_result.get('confidence', 0.8),
                'sources': ragie_result.get('sources', []),
                'metadata': ragie_result.get('metadata', {})
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced Ragie query failed: {e}")
            return {'content': f'Knowledge query failed: {str(e)}', 'confidence': 0.3, 'sources': []}
    
    def _enhance_query_for_agent_context(self, query: str, context: RagieContext) -> str:
        """Enhance query with agent and context information"""
        
        query_parts = [query]
        
        # Add agent-specific context
        if self.agent_type == AgentType.EQUIPMENT:
            query_parts.append("equipment troubleshooting repair maintenance technical")
        elif self.agent_type == AgentType.PROCEDURE:
            query_parts.append("steps procedure workflow process instructions")
        elif self.agent_type == AgentType.SAFETY:
            query_parts.append("safety protocols compliance emergency regulations")
        elif self.agent_type == AgentType.MAINTENANCE:
            query_parts.append("cleaning maintenance schedule sanitation upkeep")
        
        # Add equipment context from conversation
        equipment_mentions = context.get_equipment_mentions()
        if equipment_mentions:
            query_parts.append(f"equipment: {' '.join(equipment_mentions)}")
        
        # Add conversation context
        if context.conversation_history:
            recent_context = context.conversation_history[-2:]  # Last 2 exchanges
            context_terms = []
            for exchange in recent_context:
                if 'equipment' in exchange.get('response', '').lower():
                    context_terms.append('equipment')
                if 'safety' in exchange.get('response', '').lower():
                    context_terms.append('safety')
            
            if context_terms:
                query_parts.append(f"context: {' '.join(set(context_terms))}")
        
        return " | ".join(query_parts)
    
    async def _create_ragie_knowledge(self, query: str, ragie_response: Dict[str, Any]) -> List[RagieKnowledge]:
        """Create Ragie knowledge objects from response"""
        
        knowledge_sources = []
        
        # Main knowledge from response
        if ragie_response.get('content'):
            knowledge = RagieKnowledge(
                content=ragie_response['content'],
                confidence=ragie_response.get('confidence', 0.8),
                source_title=ragie_response.get('sources', [{}])[0].get('title', 'QSR Manual'),
                source_page=ragie_response.get('sources', [{}])[0].get('page'),
                agent_type=self.agent_type,
                knowledge_type=self._get_knowledge_type(),
                ragie_query=query,
                retrieval_time_ms=100.0  # Placeholder
            )
            knowledge_sources.append(knowledge)
        
        # Additional knowledge from sources
        for source in ragie_response.get('sources', []):
            if source.get('content') and source.get('content') != ragie_response.get('content'):
                knowledge = RagieKnowledge(
                    content=source.get('content', ''),
                    confidence=ragie_response.get('confidence', 0.8) * 0.9,  # Slightly lower
                    source_title=source.get('title', 'QSR Manual'),
                    source_page=source.get('page'),
                    agent_type=self.agent_type,
                    knowledge_type=self._get_knowledge_type(),
                    ragie_query=query,
                    retrieval_time_ms=100.0
                )
                knowledge_sources.append(knowledge)
        
        return knowledge_sources
    
    def _get_knowledge_type(self) -> str:
        """Get knowledge type based on agent"""
        type_map = {
            AgentType.EQUIPMENT: "factual",
            AgentType.PROCEDURE: "procedural",
            AgentType.SAFETY: "safety",
            AgentType.MAINTENANCE: "maintenance"
        }
        return type_map.get(self.agent_type, "factual")
    
    async def _extract_enhanced_citations(self, query: str, ragie_response: Dict[str, Any]) -> List[RagieCitation]:
        """Extract enhanced visual citations"""
        
        citations = []
        
        if not self.citation_service:
            return citations
        
        try:
            # Extract visual references using available method
            text_to_analyze = query + " " + ragie_response.get('content', '')
            
            # Use the detect references method that's actually available
            visual_refs = self.citation_service._detect_references_in_text(text_to_analyze)
            
            for ref in visual_refs[:3]:  # Limit to 3 references
                # Map reference types to valid citation types
                ref_type = ref['type']
                if ref_type in ['safety', 'equipment', 'procedure']:
                    citation_type = "diagram"
                elif ref_type in ['steps', 'process']:
                    citation_type = "flowchart"
                elif ref_type in ['temperature', 'time', 'measurement']:
                    citation_type = "table"
                elif ref_type in ['visual', 'picture', 'photo']:
                    citation_type = "image"
                else:
                    citation_type = "diagram"  # Default fallback
                
                citation = RagieCitation(
                    citation_id=hashlib.md5(f"{ref_type}_{ref['matched_text']}".encode()).hexdigest()[:8],
                    citation_type=citation_type,
                    source_document='QSR Manual',
                    title=f"{ref['type'].title()}: {ref['matched_text']}",
                    description=f"Visual reference for {ref['matched_text']}",
                    agent_type=self.agent_type,
                    ragie_confidence=ragie_response.get('confidence', 0.8),
                    ragie_relevance=0.8,
                    safety_level=SafetyLevel.HIGH if self.agent_type == AgentType.SAFETY else SafetyLevel.LOW
                )
                citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Enhanced citation extraction failed: {e}")
            return []
    
    async def _create_equipment_context(self, 
                                      query: str, 
                                      ragie_response: Dict[str, Any],
                                      equipment_mentioned: List[str] = None) -> Optional[RagieEquipmentContext]:
        """Create equipment context if relevant"""
        
        if self.agent_type != AgentType.EQUIPMENT and not equipment_mentioned:
            return None
        
        # Extract equipment name
        equipment_name = None
        if equipment_mentioned:
            equipment_name = equipment_mentioned[0]
        elif 'fryer' in query.lower():
            equipment_name = 'Taylor C602 Fryer'
        elif 'oven' in query.lower():
            equipment_name = 'QSR Oven'
        elif 'grill' in query.lower():
            equipment_name = 'QSR Grill'
        
        if not equipment_name:
            return None
        
        # Create knowledge for equipment
        equipment_knowledge = [
            RagieKnowledge(
                content=ragie_response.get('content', ''),
                confidence=ragie_response.get('confidence', 0.8),
                source_title='Equipment Manual',
                agent_type=self.agent_type,
                knowledge_type="factual",
                ragie_query=query,
                equipment_context=[equipment_name]
            )
        ]
        
        return RagieEquipmentContext(
            equipment_name=equipment_name,
            equipment_type=self._get_equipment_type(equipment_name),
            ragie_knowledge=equipment_knowledge,
            safety_level=SafetyLevel.MEDIUM,
            safety_warnings=self._get_equipment_safety_warnings(equipment_name)
        )
    
    def _get_equipment_type(self, equipment_name: str) -> str:
        """Get equipment type from name"""
        name_lower = equipment_name.lower()
        if 'fryer' in name_lower:
            return 'fryer'
        elif 'oven' in name_lower:
            return 'oven'
        elif 'grill' in name_lower:
            return 'grill'
        else:
            return 'equipment'
    
    def _get_equipment_safety_warnings(self, equipment_name: str) -> List[str]:
        """Get equipment-specific safety warnings"""
        warnings = []
        name_lower = equipment_name.lower()
        
        if 'fryer' in name_lower:
            warnings.extend([
                "Hot oil hazard - allow cooling before service",
                "Use appropriate PPE when working with fryer",
                "Follow lockout/tagout procedures"
            ])
        elif 'oven' in name_lower:
            warnings.extend([
                "High temperature surfaces",
                "Use heat-resistant gloves",
                "Ensure proper ventilation"
            ])
        
        return warnings
    
    async def _create_procedure_context(self, 
                                      query: str, 
                                      ragie_response: Dict[str, Any]) -> Optional[RagieProcedureContext]:
        """Create procedure context if relevant"""
        
        if self.agent_type != AgentType.PROCEDURE and 'step' not in query.lower():
            return None
        
        # Determine procedure type
        procedure_type = "operation"
        if 'clean' in query.lower():
            procedure_type = "cleaning"
        elif 'maintenance' in query.lower():
            procedure_type = "maintenance"
        elif 'troubleshoot' in query.lower():
            procedure_type = "troubleshooting"
        elif 'setup' in query.lower():
            procedure_type = "setup"
        
        # Extract steps from response
        steps = self._extract_steps_from_response(ragie_response.get('content', ''))
        
        # Create procedure knowledge
        procedure_knowledge = [
            RagieKnowledge(
                content=ragie_response.get('content', ''),
                confidence=ragie_response.get('confidence', 0.8),
                source_title='Procedure Manual',
                agent_type=self.agent_type,
                knowledge_type="procedural",
                ragie_query=query
            )
        ]
        
        return RagieProcedureContext(
            procedure_name=f"{procedure_type.title()} Procedure",
            procedure_type=procedure_type,
            ragie_knowledge=procedure_knowledge,
            steps=steps,
            difficulty_level="beginner" if 'basic' in query.lower() else "intermediate",
            safety_requirements=self._get_procedure_safety_requirements(procedure_type)
        )
    
    def _extract_steps_from_response(self, content: str) -> List[Dict[str, Any]]:
        """Extract steps from response content"""
        import re
        
        steps = []
        step_patterns = [
            r'(\d+)\.\s+([^\.]+)',  # Numbered steps
            r'Step\s+(\d+):\s+([^\.]+)',  # "Step 1:" format
            r'([A-Z][^\.]+)\.',  # Sentence-based steps
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for i, match in enumerate(matches):
                    if isinstance(match, tuple) and len(match) == 2:
                        step_num, step_desc = match
                        steps.append({
                            'step_number': int(step_num) if step_num.isdigit() else i + 1,
                            'description': step_desc.strip(),
                            'safety_critical': 'safety' in step_desc.lower()
                        })
                    else:
                        steps.append({
                            'step_number': i + 1,
                            'description': match.strip(),
                            'safety_critical': 'safety' in match.lower()
                        })
                break
        
        return steps[:10]  # Limit to 10 steps
    
    def _get_procedure_safety_requirements(self, procedure_type: str) -> List[str]:
        """Get safety requirements for procedure type"""
        requirements = []
        
        if procedure_type == "cleaning":
            requirements.extend([
                "Use appropriate cleaning chemicals",
                "Ensure proper ventilation",
                "Wear protective equipment"
            ])
        elif procedure_type == "maintenance":
            requirements.extend([
                "Follow lockout/tagout procedures",
                "Use proper tools and equipment",
                "Document all maintenance activities"
            ])
        elif procedure_type == "troubleshooting":
            requirements.extend([
                "Ensure equipment is safe to work on",
                "Follow diagnostic procedures",
                "Contact supervisor if unsure"
            ])
        
        return requirements
    
    async def _generate_enhanced_response(self, query: str, ragie_response: Dict[str, Any]) -> str:
        """Generate enhanced response text"""
        
        ragie_content = ragie_response.get('content', '')
        
        if not ragie_content:
            return f"I don't have specific information for your {self.agent_type.value} question. Could you provide more details?"
        
        # Agent-specific response formatting
        if self.agent_type == AgentType.SAFETY:
            return f"🚨 SAFETY PRIORITY: {ragie_content}"
        elif self.agent_type == AgentType.EQUIPMENT:
            return f"For your equipment question: {ragie_content}"
        elif self.agent_type == AgentType.PROCEDURE:
            return f"Here's the procedure: {ragie_content}"
        elif self.agent_type == AgentType.MAINTENANCE:
            return f"For maintenance: {ragie_content}"
        else:
            return ragie_content
    
    async def _analyze_enhanced_safety(self, query: str, ragie_response: Dict[str, Any]) -> tuple[SafetyLevel, List[str]]:
        """Analyze safety level and generate warnings"""
        
        safety_keywords = ['safety', 'danger', 'hot', 'electrical', 'chemical', 'emergency', 'fire', 'burn']
        critical_keywords = ['emergency', 'fire', 'burn', 'toxic', 'hazard']
        
        content = (query + " " + ragie_response.get('content', '')).lower()
        
        # Determine safety level
        if self.agent_type == AgentType.SAFETY:
            safety_level = SafetyLevel.HIGH
        elif any(keyword in content for keyword in critical_keywords):
            safety_level = SafetyLevel.CRITICAL
        elif any(keyword in content for keyword in safety_keywords):
            safety_level = SafetyLevel.HIGH
        else:
            safety_level = SafetyLevel.LOW
        
        # Generate warnings
        warnings = []
        if safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]:
            warnings.append("Follow all safety protocols")
            
            if 'electrical' in content:
                warnings.append("Disconnect power before electrical work")
            if any(word in content for word in ['hot', 'heat', 'temperature']):
                warnings.append("Allow equipment to cool before service")
            if 'chemical' in content:
                warnings.append("Use appropriate PPE and ventilation")
        
        return safety_level, warnings
    
    def _determine_conversation_intent(self, query: str) -> ConversationIntent:
        """Determine conversation intent from query"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['how', 'what', 'when', 'where', 'why']):
            if self.agent_type == AgentType.EQUIPMENT:
                return ConversationIntent.EQUIPMENT_QUESTION
            elif self.agent_type == AgentType.PROCEDURE:
                return ConversationIntent.PROCEDURE_QUESTION
            elif self.agent_type == AgentType.SAFETY:
                return ConversationIntent.SAFETY_QUESTION
            elif self.agent_type == AgentType.MAINTENANCE:
                return ConversationIntent.MAINTENANCE_QUESTION
        
        if any(word in query_lower for word in ['explain', 'clarify', 'what do you mean']):
            return ConversationIntent.CLARIFICATION
        
        if any(word in query_lower for word in ['also', 'more', 'additionally']):
            return ConversationIntent.FOLLOW_UP
        
        return ConversationIntent.GENERAL_QUESTION
    
    def _generate_follow_ups_enhanced(self, query: str, ragie_response: Dict[str, Any]) -> List[str]:
        """Generate enhanced follow-up questions"""
        
        follow_ups = []
        
        if self.agent_type == AgentType.EQUIPMENT:
            follow_ups = [
                "Would you like troubleshooting steps?",
                "Do you need maintenance information?",
                "Would you like safety considerations?"
            ]
        elif self.agent_type == AgentType.PROCEDURE:
            follow_ups = [
                "Do you need more detailed steps?",
                "Would you like safety requirements?",
                "Do you need equipment specifications?"
            ]
        elif self.agent_type == AgentType.SAFETY:
            follow_ups = [
                "Do you need emergency procedures?",
                "Would you like compliance information?",
                "Do you need PPE requirements?"
            ]
        elif self.agent_type == AgentType.MAINTENANCE:
            follow_ups = [
                "Do you need cleaning schedules?",
                "Would you like chemical safety information?",
                "Do you need maintenance tracking?"
            ]
        else:
            follow_ups = [
                "Would you like more specific information?",
                "Do you have follow-up questions?",
                "Would you like related procedures?"
            ]
        
        return follow_ups
    
    async def _create_error_response(self, 
                                   error_msg: str, 
                                   interaction_mode: InteractionMode,
                                   response_format: ResponseFormat) -> UniversalQSRResponse:
        """Create error response"""
        
        # Create minimal Ragie context
        ragie_context = RagieContext(
            session_id="error",
            interaction_mode=interaction_mode,
            agent_type=self.agent_type
        )
        
        error_text = f"I encountered an issue: {error_msg}. Please try rephrasing your question."
        
        if response_format == ResponseFormat.TEXT_UI:
            return UniversalResponseFactory.create_text_response(
                text_response=error_text,
                agent_type=self.agent_type,
                ragie_context=ragie_context,
                confidence_score=0.3,
                safety_level=SafetyLevel.HIGH,
                safety_warnings=["Unable to process query due to error"]
            )
        elif response_format == ResponseFormat.VOICE_AUDIO:
            return UniversalResponseFactory.create_voice_response(
                text_response=error_text,
                agent_type=self.agent_type,
                ragie_context=ragie_context,
                confidence_score=0.3,
                safety_level=SafetyLevel.HIGH,
                safety_warnings=["Unable to process query due to error"]
            )
        else:
            return UniversalResponseFactory.create_hybrid_response(
                text_response=error_text,
                agent_type=self.agent_type,
                ragie_context=ragie_context,
                confidence_score=0.3,
                safety_level=SafetyLevel.HIGH,
                safety_warnings=["Unable to process query due to error"]
            )

# ===============================================================================
# ENHANCED CLEAN INTELLIGENCE SERVICE
# ===============================================================================

class EnhancedCleanIntelligenceService(CleanIntelligenceService):
    """Enhanced clean intelligence service with universal response models"""
    
    def __init__(self, ragie_service: Any = None, citation_service: Any = None):
        # Initialize parent class
        super().__init__(ragie_service, citation_service)
        
        # Replace agents with enhanced versions
        self.agents = {
            agent_type: EnhancedCleanQSRAgent(agent_type, ragie_service, citation_service)
            for agent_type in AgentType
        }
        
        # Response metrics
        self.response_metrics = ResponseMetrics()
        
        # Response adapter
        self.response_adapter = ResponseAdapter()
        
        self.logger.info(f"✅ Enhanced Clean Intelligence Service initialized with {len(self.agents)} enhanced agents")
    
    async def process_text_query(self, 
                                query: str,
                                session_id: str = None,
                                equipment_mentioned: List[str] = None,
                                conversation_history: List[Dict[str, Any]] = None) -> TextChatResponse:
        """Process query for text chat"""
        
        # Select agent
        agent_type = self._select_agent_clean(query)
        agent = self.agents[agent_type]
        
        # Process with universal response
        response = await agent.process_universal_query(
            query=query,
            interaction_mode=InteractionMode.TEXT_CHAT,
            response_format=ResponseFormat.TEXT_UI,
            session_id=session_id,
            equipment_mentioned=equipment_mentioned,
            conversation_history=conversation_history
        )
        
        # Update global metrics
        self.response_metrics.update_with_response(response)
        
        return response
    
    async def process_voice_query(self, 
                                 query: str,
                                 session_id: str = None,
                                 equipment_mentioned: List[str] = None,
                                 conversation_history: List[Dict[str, Any]] = None) -> VoiceResponse:
        """Process query for voice chat"""
        
        # Select agent
        agent_type = self._select_agent_clean(query)
        agent = self.agents[agent_type]
        
        # Process with universal response
        response = await agent.process_universal_query(
            query=query,
            interaction_mode=InteractionMode.VOICE_CHAT,
            response_format=ResponseFormat.VOICE_AUDIO,
            session_id=session_id,
            equipment_mentioned=equipment_mentioned,
            conversation_history=conversation_history
        )
        
        # Update global metrics
        self.response_metrics.update_with_response(response)
        
        return response
    
    async def process_hybrid_query(self, 
                                  query: str,
                                  primary_mode: InteractionMode = InteractionMode.TEXT_CHAT,
                                  session_id: str = None,
                                  equipment_mentioned: List[str] = None,
                                  conversation_history: List[Dict[str, Any]] = None) -> HybridResponse:
        """Process query for hybrid interaction"""
        
        # Select agent
        agent_type = self._select_agent_clean(query)
        agent = self.agents[agent_type]
        
        # Process with universal response
        response = await agent.process_universal_query(
            query=query,
            interaction_mode=InteractionMode.HYBRID,
            response_format=ResponseFormat.HYBRID,
            session_id=session_id,
            equipment_mentioned=equipment_mentioned,
            conversation_history=conversation_history
        )
        
        # Update global metrics
        self.response_metrics.update_with_response(response)
        
        return response
    
    def adapt_response_format(self, 
                             response: UniversalQSRResponse,
                             target_mode: InteractionMode) -> UniversalQSRResponse:
        """Adapt response to different interaction mode"""
        
        if isinstance(response, TextChatResponse) and target_mode == InteractionMode.VOICE_CHAT:
            return self.response_adapter.adapt_text_to_voice(response)
        elif isinstance(response, VoiceResponse) and target_mode == InteractionMode.TEXT_CHAT:
            return self.response_adapter.adapt_voice_to_text(response)
        else:
            return response
    
    def get_response_metrics(self) -> Dict[str, Any]:
        """Get response metrics"""
        return self.response_metrics.get_summary()
    
    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health check"""
        basic_health = await super().health_check()
        
        # Add enhanced features
        basic_health.update({
            'enhanced_features': {
                'universal_responses': True,
                'ragie_integration': True,
                'visual_citations': True,
                'safety_analysis': True,
                'performance_metrics': True
            },
            'response_metrics': self.response_metrics.get_summary()
        })
        
        return basic_health

# ===============================================================================
# FACTORY FUNCTION
# ===============================================================================

async def create_enhanced_clean_intelligence_service(
    ragie_service: Any = None,
    citation_service: Any = None
) -> EnhancedCleanIntelligenceService:
    """Create enhanced clean intelligence service"""
    
    service = EnhancedCleanIntelligenceService(
        ragie_service=ragie_service,
        citation_service=citation_service
    )
    
    # Health check
    health = await service.health_check()
    logger.info(f"Enhanced Clean Intelligence Service created: {health}")
    
    return service

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    "EnhancedCleanIntelligenceService",
    "EnhancedCleanQSRAgent",
    "create_enhanced_clean_intelligence_service"
]