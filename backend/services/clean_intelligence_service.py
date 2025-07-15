"""
Clean Intelligence Service - Pure Ragie + PydanticAI Implementation
=================================================================

CLEAN implementation that ONLY uses Ragie + PydanticAI without any:
- Graph-RAG dependencies
- Neo4j dependencies  
- LightRAG dependencies
- Enterprise Bridge dependencies
- RAG-Anything dependencies

This is a pure Ragie + PydanticAI multi-agent system for QSR operations.

Author: Generated with Memex (https://memex.tech)
"""

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum
import logging
import json
import time
import asyncio
from datetime import datetime
import hashlib
import os

# ONLY import Ragie and basic services - NO Graph-RAG dependencies
try:
    from services.ragie_service_clean import RagieService
    from services.multimodal_citation_service import MultiModalCitationService
    RAGIE_AVAILABLE = True
except ImportError:
    RAGIE_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===============================================================================
# CLEAN MODELS - No Graph-RAG dependencies
# ===============================================================================

class AgentType(str, Enum):
    """QSR agent specializations"""
    EQUIPMENT = "equipment"
    PROCEDURE = "procedure"
    SAFETY = "safety"
    MAINTENANCE = "maintenance"
    GENERAL = "general"

class InteractionMode(str, Enum):
    """Interaction modes"""
    TEXT_CHAT = "text_chat"
    VOICE_CHAT = "voice_chat"

class ConversationIntent(str, Enum):
    """Conversation intents"""
    EQUIPMENT_QUESTION = "equipment_question"
    PROCEDURE_QUESTION = "procedure_question"
    SAFETY_QUESTION = "safety_question"
    MAINTENANCE_QUESTION = "maintenance_question"
    GENERAL_QUESTION = "general_question"
    FOLLOW_UP = "follow_up"

class CleanQueryContext(BaseModel):
    """Clean query context - only Ragie + basic context"""
    query: str
    agent_type: AgentType
    interaction_mode: InteractionMode
    session_id: Optional[str] = None
    equipment_mentioned: Optional[List[str]] = None
    safety_critical: bool = False
    user_expertise: Literal["beginner", "intermediate", "advanced"] = "beginner"
    
class CleanIntelligentResponse(BaseModel):
    """Clean intelligent response - only Ragie + PydanticAI data"""
    
    # Core response
    text_response: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Agent context
    primary_agent: AgentType
    
    # Ragie integration
    ragie_sources: List[Dict[str, Any]] = Field(default_factory=list)
    ragie_confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    
    # Visual citations (from existing service)
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Conversation context
    detected_intent: ConversationIntent
    
    # Safety
    safety_priority: bool = False
    safety_warnings: List[str] = Field(default_factory=list)
    
    # Performance
    generation_time_ms: Optional[float] = None
    ragie_query_time_ms: Optional[float] = None
    
    # Voice optimization
    voice_optimized: bool = False
    suggested_follow_ups: List[str] = Field(default_factory=list)

# ===============================================================================
# CLEAN AGENTS - Pure Ragie + PydanticAI
# ===============================================================================

class CleanQSRAgent:
    """Base clean QSR agent using only Ragie"""
    
    def __init__(self, agent_type: AgentType, ragie_service: Any, citation_service: Any = None):
        self.agent_type = agent_type
        self.ragie_service = ragie_service
        self.citation_service = citation_service
        self.logger = logging.getLogger(f"{__name__}.{agent_type.value.title()}Agent")
        
        # Agent-specific prompts
        self.prompts = {
            AgentType.EQUIPMENT: """You are a QSR Equipment Specialist. Help with equipment troubleshooting, 
            technical specifications, and equipment operation. Focus on practical solutions.""",
            
            AgentType.PROCEDURE: """You are a QSR Procedure Specialist. Help with step-by-step procedures, 
            workflows, and operational processes. Provide clear, numbered steps.""",
            
            AgentType.SAFETY: """You are a QSR Safety Specialist. Help with safety protocols, compliance, 
            and emergency procedures. Safety is the highest priority.""",
            
            AgentType.MAINTENANCE: """You are a QSR Maintenance Specialist. Help with cleaning procedures, 
            maintenance schedules, and equipment upkeep. Focus on proper procedures.""",
            
            AgentType.GENERAL: """You are a QSR General Assistant. Help with general QSR operations, 
            information lookup, and cross-functional questions."""
        }
    
    async def process_query(self, context: CleanQueryContext) -> CleanIntelligentResponse:
        """Process query using only Ragie + PydanticAI"""
        start_time = time.time()
        
        try:
            # Step 1: Query Ragie for knowledge
            ragie_start = time.time()
            ragie_response = await self._query_ragie_clean(context)
            ragie_time = (time.time() - ragie_start) * 1000
            
            # Step 2: Extract visual citations (existing service)
            visual_citations = await self._extract_visual_citations_clean(context, ragie_response)
            
            # Step 3: Generate agent-specific response
            response_text = await self._generate_agent_response(context, ragie_response)
            
            # Step 4: Analyze safety requirements
            safety_info = self._analyze_safety_clean(context, ragie_response)
            
            # Step 5: Generate follow-ups
            follow_ups = self._generate_follow_ups_clean(context, ragie_response)
            
            generation_time = (time.time() - start_time) * 1000
            
            return CleanIntelligentResponse(
                text_response=response_text,
                confidence_score=ragie_response.get('confidence', 0.8),
                primary_agent=self.agent_type,
                ragie_sources=ragie_response.get('sources', []),
                ragie_confidence=ragie_response.get('confidence', 0.8),
                visual_citations=visual_citations,
                detected_intent=self._map_to_intent(self.agent_type),
                safety_priority=safety_info['is_safety_critical'],
                safety_warnings=safety_info['warnings'],
                generation_time_ms=generation_time,
                ragie_query_time_ms=ragie_time,
                voice_optimized=context.interaction_mode == InteractionMode.VOICE_CHAT,
                suggested_follow_ups=follow_ups
            )
            
        except Exception as e:
            self.logger.error(f"Agent processing failed: {e}")
            return self._create_error_response(str(e))
    
    async def _query_ragie_clean(self, context: CleanQueryContext) -> Dict[str, Any]:
        """Query Ragie service cleanly"""
        if not self.ragie_service:
            return {'content': 'Ragie service not available', 'confidence': 0.5, 'sources': []}
        
        try:
            # Enhance query with agent context
            enhanced_query = self._enhance_query_for_agent(context)
            
            # Query Ragie
            ragie_result = await self.ragie_service.search_documents(
                query=enhanced_query,
                limit=8,
                hybrid_search=True
            )
            
            return {
                'content': ragie_result.get('content', ''),
                'confidence': ragie_result.get('confidence', 0.8),
                'sources': ragie_result.get('sources', []),
                'metadata': ragie_result.get('metadata', {})
            }
            
        except Exception as e:
            self.logger.error(f"Ragie query failed: {e}")
            return {'content': f'Knowledge query failed: {str(e)}', 'confidence': 0.3, 'sources': []}
    
    def _enhance_query_for_agent(self, context: CleanQueryContext) -> str:
        """Enhance query based on agent specialization"""
        query_parts = [context.query]
        
        # Add agent-specific context
        if self.agent_type == AgentType.EQUIPMENT:
            query_parts.append("equipment troubleshooting repair maintenance")
        elif self.agent_type == AgentType.PROCEDURE:
            query_parts.append("steps procedure workflow process")
        elif self.agent_type == AgentType.SAFETY:
            query_parts.append("safety protocols compliance emergency")
        elif self.agent_type == AgentType.MAINTENANCE:
            query_parts.append("cleaning maintenance schedule sanitation")
        
        # Add equipment context if available
        if context.equipment_mentioned:
            query_parts.append(f"equipment: {' '.join(context.equipment_mentioned)}")
        
        return " | ".join(query_parts)
    
    async def _extract_visual_citations_clean(self, context: CleanQueryContext, ragie_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract visual citations using existing service only"""
        if not self.citation_service:
            return []
        
        try:
            # Extract visual references from query + Ragie response
            text_to_analyze = context.query + " " + ragie_response.get('content', '')
            visual_refs = self.citation_service.extract_visual_references(text_to_analyze)
            
            citations = []
            for ref_type, references in visual_refs.items():
                for ref in references[:2]:  # Limit per type
                    citation = {
                        'citation_id': hashlib.md5(f"{ref_type}_{ref}".encode()).hexdigest()[:8],
                        'type': ref_type,
                        'source': 'QSR Manual',
                        'description': f"{ref_type.title()}: {ref}",
                        'confidence': 0.8,
                        'agent_type': self.agent_type.value,
                        'ragie_source': True
                    }
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Visual citation extraction failed: {e}")
            return []
    
    async def _generate_agent_response(self, context: CleanQueryContext, ragie_response: Dict[str, Any]) -> str:
        """Generate agent-specific response"""
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
    
    def _analyze_safety_clean(self, context: CleanQueryContext, ragie_response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze safety requirements without Graph-RAG"""
        safety_keywords = ['safety', 'danger', 'hot', 'electrical', 'chemical', 'emergency', 'fire', 'burn']
        
        content = (context.query + " " + ragie_response.get('content', '')).lower()
        is_safety_critical = any(keyword in content for keyword in safety_keywords)
        
        warnings = []
        if is_safety_critical or self.agent_type == AgentType.SAFETY:
            warnings.append("Follow all safety protocols")
            if 'electrical' in content:
                warnings.append("Disconnect power before electrical work")
            if any(word in content for word in ['hot', 'heat', 'temperature']):
                warnings.append("Allow equipment to cool before service")
        
        return {
            'is_safety_critical': is_safety_critical or self.agent_type == AgentType.SAFETY,
            'warnings': warnings
        }
    
    def _generate_follow_ups_clean(self, context: CleanQueryContext, ragie_response: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions"""
        follow_ups = []
        
        if self.agent_type == AgentType.EQUIPMENT:
            follow_ups = ["Do you need troubleshooting steps?", "Would you like maintenance information?"]
        elif self.agent_type == AgentType.PROCEDURE:
            follow_ups = ["Do you need more detailed steps?", "Would you like safety considerations?"]
        elif self.agent_type == AgentType.SAFETY:
            follow_ups = ["Do you need emergency procedures?", "Would you like compliance information?"]
        elif self.agent_type == AgentType.MAINTENANCE:
            follow_ups = ["Do you need cleaning schedules?", "Would you like chemical safety information?"]
        else:
            follow_ups = ["Would you like more specific information?", "Do you have follow-up questions?"]
        
        return follow_ups
    
    def _map_to_intent(self, agent_type: AgentType) -> ConversationIntent:
        """Map agent type to conversation intent"""
        intent_map = {
            AgentType.EQUIPMENT: ConversationIntent.EQUIPMENT_QUESTION,
            AgentType.PROCEDURE: ConversationIntent.PROCEDURE_QUESTION,
            AgentType.SAFETY: ConversationIntent.SAFETY_QUESTION,
            AgentType.MAINTENANCE: ConversationIntent.MAINTENANCE_QUESTION,
            AgentType.GENERAL: ConversationIntent.GENERAL_QUESTION
        }
        return intent_map.get(agent_type, ConversationIntent.GENERAL_QUESTION)
    
    def _create_error_response(self, error_msg: str) -> CleanIntelligentResponse:
        """Create error response"""
        return CleanIntelligentResponse(
            text_response=f"I encountered an issue: {error_msg}. Please try rephrasing your question.",
            confidence_score=0.3,
            primary_agent=self.agent_type,
            detected_intent=self._map_to_intent(self.agent_type),
            safety_priority=True,
            safety_warnings=["Unable to process query due to error"]
        )

# ===============================================================================
# CLEAN INTELLIGENCE SERVICE - Pure Ragie + PydanticAI
# ===============================================================================

class CleanIntelligenceService:
    """Clean Intelligence Service - ONLY Ragie + PydanticAI, NO Graph-RAG dependencies"""
    
    def __init__(self, ragie_service: Any = None, citation_service: Any = None):
        self.logger = logging.getLogger(f"{__name__}.CleanIntelligenceService")
        
        # Store services
        self.ragie_service = ragie_service
        self.citation_service = citation_service
        
        # Create clean agents
        self.agents = {
            agent_type: CleanQSRAgent(agent_type, ragie_service, citation_service)
            for agent_type in AgentType
        }
        
        # Performance tracking
        self.performance_metrics = {
            agent_type: {'total_queries': 0, 'successful_queries': 0, 'avg_time': 0.0}
            for agent_type in AgentType
        }
        
        # Response cache
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        self.logger.info(f"✅ Clean Intelligence Service initialized with {len(self.agents)} agents")
    
    async def process_query(self, 
                           query: str,
                           interaction_mode: InteractionMode = InteractionMode.TEXT_CHAT,
                           session_id: Optional[str] = None,
                           equipment_mentioned: Optional[List[str]] = None) -> CleanIntelligentResponse:
        """Process query with clean agent selection"""
        
        start_time = time.time()
        
        try:
            # Select appropriate agent
            agent_type = self._select_agent_clean(query)
            
            # Create query context
            context = CleanQueryContext(
                query=query,
                agent_type=agent_type,
                interaction_mode=interaction_mode,
                session_id=session_id,
                equipment_mentioned=equipment_mentioned,
                safety_critical=self._is_safety_critical(query)
            )
            
            # Check cache first
            cache_key = self._generate_cache_key(query, agent_type, interaction_mode)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
            
            # Process with selected agent
            agent = self.agents[agent_type]
            response = await agent.process_query(context)
            
            # Cache response
            self._cache_response(cache_key, response)
            
            # Update metrics
            processing_time = (time.time() - start_time) * 1000
            self._update_metrics(agent_type, processing_time, True)
            
            self.logger.info(f"Processed query with {agent_type.value} agent in {processing_time:.2f}ms")
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(f"Query processing failed: {e}")
            
            # Update metrics for failure
            self._update_metrics(AgentType.GENERAL, processing_time, False)
            
            return CleanIntelligentResponse(
                text_response=f"I encountered an issue processing your query: {str(e)}",
                confidence_score=0.3,
                primary_agent=AgentType.GENERAL,
                detected_intent=ConversationIntent.GENERAL_QUESTION,
                safety_priority=True,
                safety_warnings=["Unable to process query due to system error"]
            )
    
    def _select_agent_clean(self, query: str) -> AgentType:
        """Clean agent selection based only on query keywords"""
        query_lower = query.lower()
        
        # Safety takes highest priority
        safety_keywords = ['safety', 'danger', 'hazard', 'emergency', 'fire', 'burn', 'toxic', 'accident']
        if any(keyword in query_lower for keyword in safety_keywords):
            return AgentType.SAFETY
        
        # Equipment keywords
        equipment_keywords = ['equipment', 'machine', 'fryer', 'oven', 'grill', 'compressor', 'troubleshoot', 'repair', 'fix', 'broken']
        if any(keyword in query_lower for keyword in equipment_keywords):
            return AgentType.EQUIPMENT
        
        # Procedure keywords
        procedure_keywords = ['how to', 'steps', 'procedure', 'process', 'workflow', 'guide', 'instructions']
        if any(keyword in query_lower for keyword in procedure_keywords):
            return AgentType.PROCEDURE
        
        # Maintenance keywords
        maintenance_keywords = ['clean', 'cleaning', 'maintenance', 'sanitize', 'schedule', 'chemical', 'wash']
        if any(keyword in query_lower for keyword in maintenance_keywords):
            return AgentType.MAINTENANCE
        
        # Default to general
        return AgentType.GENERAL
    
    def _is_safety_critical(self, query: str) -> bool:
        """Determine if query is safety-critical"""
        safety_keywords = ['safety', 'danger', 'hazard', 'emergency', 'fire', 'burn', 'toxic', 'chemical', 'injury']
        return any(keyword in query.lower() for keyword in safety_keywords)
    
    def _generate_cache_key(self, query: str, agent_type: AgentType, interaction_mode: InteractionMode) -> str:
        """Generate cache key"""
        key_parts = [query, agent_type.value, interaction_mode.value]
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[CleanIntelligentResponse]:
        """Get cached response if available"""
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['response']
        return None
    
    def _cache_response(self, cache_key: str, response: CleanIntelligentResponse):
        """Cache response"""
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
    
    def _update_metrics(self, agent_type: AgentType, processing_time: float, success: bool):
        """Update performance metrics"""
        metrics = self.performance_metrics[agent_type]
        metrics['total_queries'] += 1
        if success:
            metrics['successful_queries'] += 1
        
        # Update average time
        metrics['avg_time'] = (metrics['avg_time'] * (metrics['total_queries'] - 1) + processing_time) / metrics['total_queries']
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            'status': 'healthy',
            'ragie_available': self.ragie_service is not None,
            'citation_available': self.citation_service is not None,
            'agents_count': len(self.agents),
            'cache_size': len(self.response_cache),
            'dependencies': {
                'graph_rag': False,
                'neo4j': False,
                'lightrag': False,
                'enterprise_bridge': False,
                'ragie_only': True
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            agent_type.value: {
                'total_queries': metrics['total_queries'],
                'success_rate': metrics['successful_queries'] / max(metrics['total_queries'], 1),
                'avg_time_ms': metrics['avg_time']
            }
            for agent_type, metrics in self.performance_metrics.items()
        }

# ===============================================================================
# FACTORY FUNCTION
# ===============================================================================

async def create_clean_intelligence_service(ragie_service: Any = None, citation_service: Any = None) -> CleanIntelligenceService:
    """Create clean intelligence service with only Ragie + PydanticAI"""
    
    service = CleanIntelligenceService(
        ragie_service=ragie_service,
        citation_service=citation_service
    )
    
    # Health check
    health = await service.health_check()
    logger.info(f"Clean Intelligence Service created: {health}")
    
    return service

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    "CleanIntelligenceService",
    "CleanIntelligentResponse",
    "CleanQueryContext",
    "AgentType",
    "InteractionMode",
    "ConversationIntent",
    "create_clean_intelligence_service"
]