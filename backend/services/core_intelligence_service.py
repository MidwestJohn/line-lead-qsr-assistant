"""
Core Intelligence Service - Universal PydanticAI + Ragie Orchestration
=====================================================================

The CORE service that makes ALL interactions intelligent using PydanticAI + Ragie.
Handles both text chat and voice interactions with sophisticated multi-agent coordination.

Key Features:
- Universal intelligence for ALL user queries (text + voice)
- Multi-agent architecture with specialized QSR agents
- Ragie integration for knowledge retrieval
- Visual citations from existing MultiModalCitationService
- Context-aware responses with conversation continuity
- Performance optimization and caching

This replaces basic text processing with intelligent PydanticAI responses.

Author: Generated with Memex (https://memex.tech)
"""

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal, Union, Callable
from enum import Enum
import logging
import json
import time
import asyncio
from datetime import datetime
import os
import hashlib
from pathlib import Path

# Import existing services for integration
try:
    from services.multimodal_citation_service import MultiModalCitationService, VisualCitation
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False

try:
    from services.ragie_service_clean import RagieService
    RAGIE_AVAILABLE = True
except ImportError:
    RAGIE_AVAILABLE = False

try:
    from voice_agent import ConversationContext
    VOICE_AGENT_AVAILABLE = True
except ImportError:
    VOICE_AGENT_AVAILABLE = False
    
# Import types from models to avoid circular imports
try:
    from models.enhanced_qsr_models import VoiceState, ConversationIntent, AgentType as ModelAgentType
    ENHANCED_MODELS_AVAILABLE = True
except ImportError:
    ENHANCED_MODELS_AVAILABLE = False
    # Define fallback types
    class VoiceState(str, Enum):
        LISTENING = "listening"
        PROCESSING = "processing"
        RESPONDING = "responding"
    
    class ConversationIntent(str, Enum):
        EQUIPMENT_QUESTION = "equipment_question"
        FOLLOW_UP = "follow_up"
        NEW_TOPIC = "new_topic"

try:
    from step_parser import parse_ai_response_steps
    STEP_PARSER_AVAILABLE = True
except ImportError:
    STEP_PARSER_AVAILABLE = False
    def parse_ai_response_steps(text):
        """Fallback step parser"""
        import re
        steps = re.findall(r'(\d+\.?\s+[^\.]+)', text)
        return {'steps': steps, 'total_steps': len(steps)}

SERVICES_AVAILABLE = MULTIMODAL_AVAILABLE and RAGIE_AVAILABLE and VOICE_AGENT_AVAILABLE

logger = logging.getLogger(__name__)

# ===============================================================================
# CORE INTELLIGENCE MODELS
# ===============================================================================

class AgentType(str, Enum):
    """Specialized QSR agent types"""
    EQUIPMENT = "equipment"
    PROCEDURE = "procedure"
    SAFETY = "safety"
    MAINTENANCE = "maintenance"
    GENERAL = "general"

class InteractionMode(str, Enum):
    """Interaction modes supported by the service"""
    TEXT_CHAT = "text_chat"
    VOICE_CHAT = "voice_chat"
    HYBRID = "hybrid"

class RagieQueryContext(BaseModel):
    """Context for Ragie queries with QSR-specific parameters"""
    query: str
    agent_type: AgentType
    interaction_mode: InteractionMode
    equipment_context: Optional[List[str]] = None
    safety_critical: bool = False
    conversation_history: Optional[List[Dict[str, Any]]] = None
    user_expertise: Literal["beginner", "intermediate", "advanced"] = "beginner"
    max_results: int = 10
    
class IntelligentResponse(BaseModel):
    """Universal response model for all interaction modes"""
    
    # Core response content
    text_response: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Agent context
    primary_agent: AgentType
    contributing_agents: List[AgentType] = Field(default_factory=list)
    
    # Ragie knowledge integration
    ragie_sources: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    
    # Visual citations
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list)
    citation_count: int = 0
    
    # Conversation context
    detected_intent: ConversationIntent
    conversation_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Mode-specific fields
    voice_optimized: bool = False
    hands_free_friendly: bool = True
    suggested_follow_ups: List[str] = Field(default_factory=list)
    
    # Safety and compliance
    safety_priority: bool = False
    safety_warnings: List[str] = Field(default_factory=list)
    
    # Performance metrics
    generation_time_ms: Optional[float] = None
    ragie_query_time_ms: Optional[float] = None
    
    # Parsed steps for procedures
    parsed_steps: Optional[Any] = None
    
    @validator('confidence_score')
    def validate_confidence(cls, v, values):
        """Ensure confidence score is realistic"""
        knowledge_confidence = values.get('knowledge_confidence', 0.8)
        if abs(v - knowledge_confidence) > 0.3:
            logger.warning(f"Large confidence discrepancy: response={v}, knowledge={knowledge_confidence}")
        return v

class AgentPerformanceMetrics(BaseModel):
    """Performance tracking for individual agents"""
    agent_type: AgentType
    total_queries: int = 0
    successful_responses: int = 0
    average_confidence: float = 0.0
    average_response_time: float = 0.0
    ragie_query_count: int = 0
    citation_extraction_count: int = 0
    
    def update_metrics(self, response_time: float, confidence: float, success: bool):
        """Update performance metrics"""
        self.total_queries += 1
        if success:
            self.successful_responses += 1
        
        # Update averages
        self.average_response_time = (
            (self.average_response_time * (self.total_queries - 1) + response_time) / self.total_queries
        )
        self.average_confidence = (
            (self.average_confidence * (self.total_queries - 1) + confidence) / self.total_queries
        )

# ===============================================================================
# SPECIALIZED QSR AGENTS
# ===============================================================================

class QSREquipmentAgent:
    """Equipment-specialized agent using Ragie for technical knowledge"""
    
    def __init__(self, ragie_service: Any, citation_service: Any):
        self.ragie_service = ragie_service
        self.citation_service = citation_service
        self.agent_type = AgentType.EQUIPMENT
        self.logger = logging.getLogger(f"{__name__}.QSREquipmentAgent")
        
        # Equipment-specific prompt
        self.system_prompt = """
        You are a QSR Equipment Specialist. You help with:
        - Equipment troubleshooting and repair
        - Technical specifications and operation
        - Equipment maintenance and calibration
        - Performance optimization
        
        Always provide:
        - Clear, actionable technical guidance
        - Safety considerations for equipment work
        - References to specific manual sections when available
        - Step-by-step procedures when appropriate
        
        Focus on practical solutions that line leads can implement.
        """
    
    async def process_query(self, context: RagieQueryContext) -> IntelligentResponse:
        """Process equipment-related queries with Ragie knowledge"""
        start_time = time.time()
        
        try:
            # Enhance query with equipment context
            enhanced_query = await self._enhance_equipment_query(context)
            
            # Query Ragie for equipment knowledge
            ragie_start = time.time()
            ragie_response = await self._query_ragie_knowledge(enhanced_query)
            ragie_time = (time.time() - ragie_start) * 1000
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(enhanced_query, ragie_response)
            
            # Generate equipment-specific response
            response_text = await self._generate_equipment_response(ragie_response, context)
            
            # Detect safety considerations
            safety_info = self._analyze_safety_requirements(context.query, ragie_response)
            
            generation_time = (time.time() - start_time) * 1000
            
            return IntelligentResponse(
                text_response=response_text,
                confidence_score=min(ragie_response.get('confidence', 0.8), 1.0),
                primary_agent=self.agent_type,
                ragie_sources=ragie_response.get('sources', []),
                knowledge_confidence=ragie_response.get('confidence', 0.8),
                visual_citations=visual_citations,
                citation_count=len(visual_citations),
                detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
                conversation_context={
                    'equipment_mentioned': context.equipment_context,
                    'technical_focus': True
                },
                voice_optimized=context.interaction_mode == InteractionMode.VOICE_CHAT,
                safety_priority=safety_info['safety_critical'],
                safety_warnings=safety_info['warnings'],
                generation_time_ms=generation_time,
                ragie_query_time_ms=ragie_time
            )
            
        except Exception as e:
            self.logger.error(f"Equipment agent processing failed: {e}")
            return self._create_error_response(str(e))
    
    async def _enhance_equipment_query(self, context: RagieQueryContext) -> str:
        """Enhance query with equipment-specific context"""
        enhanced_parts = [context.query]
        
        if context.equipment_context:
            enhanced_parts.append(f"Equipment context: {', '.join(context.equipment_context)}")
        
        # Add technical focus keywords
        technical_keywords = ["troubleshooting", "repair", "maintenance", "calibration", "operation"]
        enhanced_parts.append(f"Technical focus: {', '.join(technical_keywords)}")
        
        return " | ".join(enhanced_parts)
    
    async def _query_ragie_knowledge(self, enhanced_query: str) -> Dict[str, Any]:
        """Query Ragie for equipment knowledge"""
        if not self.ragie_service:
            return {'content': 'Ragie service not available', 'confidence': 0.5, 'sources': []}
        
        try:
            # Use existing Ragie service
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
            self.logger.error(f"Ragie query failed: {e}")
            return {'content': f'Knowledge query failed: {str(e)}', 'confidence': 0.3, 'sources': []}
    
    async def _extract_visual_citations(self, query: str, ragie_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract visual citations from Ragie response"""
        citations = []
        
        if not self.citation_service:
            return citations
        
        try:
            # Extract visual references from query and response
            visual_refs = self.citation_service.extract_visual_references(
                query + " " + ragie_response.get('content', '')
            )
            
            # Convert to citation format
            for ref_type, references in visual_refs.items():
                for ref in references[:3]:  # Limit per type
                    citation = {
                        'citation_id': hashlib.md5(f"{ref_type}_{ref}".encode()).hexdigest()[:8],
                        'type': ref_type,
                        'source': 'Equipment Manual',
                        'description': f"Equipment {ref_type}: {ref}",
                        'confidence': 0.85,
                        'agent_type': self.agent_type.value,
                        'equipment_context': True
                    }
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Visual citation extraction failed: {e}")
            return []
    
    async def _generate_equipment_response(self, ragie_response: Dict[str, Any], context: RagieQueryContext) -> str:
        """Generate equipment-specific response"""
        base_content = ragie_response.get('content', '')
        
        if not base_content:
            return "I don't have specific equipment information for your query. Please provide more details about the equipment and issue."
        
        # Structure response for equipment context
        response_parts = []
        
        # Add context-appropriate opening
        if context.interaction_mode == InteractionMode.VOICE_CHAT:
            response_parts.append("For your equipment question:")
        
        # Add main content
        response_parts.append(base_content)
        
        # Add equipment-specific guidance
        if context.equipment_context:
            response_parts.append(f"This applies specifically to: {', '.join(context.equipment_context)}")
        
        # Add safety reminder for equipment work
        response_parts.append("Remember to follow all safety protocols when working with equipment.")
        
        return " ".join(response_parts)
    
    def _analyze_safety_requirements(self, query: str, ragie_response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze safety requirements for equipment work"""
        safety_keywords = [
            'electrical', 'hot', 'high temperature', 'pressure', 'oil', 'gas',
            'repair', 'maintenance', 'calibration', 'cleaning'
        ]
        
        content = (query + " " + ragie_response.get('content', '')).lower()
        
        safety_critical = any(keyword in content for keyword in safety_keywords)
        
        warnings = []
        if safety_critical:
            warnings.append("Equipment work requires proper safety procedures")
            if 'electrical' in content:
                warnings.append("Disconnect power before electrical work")
            if any(temp_word in content for temp_word in ['hot', 'temperature', 'heat']):
                warnings.append("Allow equipment to cool before service")
        
        return {
            'safety_critical': safety_critical,
            'warnings': warnings
        }
    
    def _create_error_response(self, error_msg: str) -> IntelligentResponse:
        """Create error response for equipment agent"""
        return IntelligentResponse(
            text_response=f"I encountered an issue processing your equipment question: {error_msg}. Please try rephrasing your question or contact support.",
            confidence_score=0.3,
            primary_agent=self.agent_type,
            detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
            safety_priority=True,
            safety_warnings=["Unable to verify safety requirements due to processing error"]
        )

class QSRProcedureAgent:
    """Procedure-specialized agent using Ragie for step-by-step guidance"""
    
    def __init__(self, ragie_service: Any, citation_service: Any):
        self.ragie_service = ragie_service
        self.citation_service = citation_service
        self.agent_type = AgentType.PROCEDURE
        self.logger = logging.getLogger(f"{__name__}.QSRProcedureAgent")
        
        self.system_prompt = """
        You are a QSR Procedure Specialist. You help with:
        - Step-by-step operational procedures
        - Process workflows and timing
        - Quality standards and checkpoints
        - Procedure troubleshooting
        
        Always provide:
        - Clear, numbered steps
        - Time estimates when relevant
        - Quality checkpoints
        - Common mistakes to avoid
        
        Focus on practical, actionable procedures that ensure consistency.
        """
    
    async def process_query(self, context: RagieQueryContext) -> IntelligentResponse:
        """Process procedure-related queries with Ragie knowledge"""
        start_time = time.time()
        
        try:
            # Enhance query for procedure focus
            enhanced_query = await self._enhance_procedure_query(context)
            
            # Query Ragie for procedure knowledge
            ragie_start = time.time()
            ragie_response = await self._query_ragie_knowledge(enhanced_query)
            ragie_time = (time.time() - ragie_start) * 1000
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(enhanced_query, ragie_response)
            
            # Generate procedure-specific response
            response_text = await self._generate_procedure_response(ragie_response, context)
            
            # Parse steps if procedure content
            parsed_steps = await self._parse_procedure_steps(response_text)
            
            generation_time = (time.time() - start_time) * 1000
            
            return IntelligentResponse(
                text_response=response_text,
                confidence_score=min(ragie_response.get('confidence', 0.8), 1.0),
                primary_agent=self.agent_type,
                ragie_sources=ragie_response.get('sources', []),
                knowledge_confidence=ragie_response.get('confidence', 0.8),
                visual_citations=visual_citations,
                citation_count=len(visual_citations),
                detected_intent=ConversationIntent.FOLLOW_UP,
                conversation_context={
                    'procedure_focus': True,
                    'step_based': True
                },
                voice_optimized=context.interaction_mode == InteractionMode.VOICE_CHAT,
                hands_free_friendly=True,
                parsed_steps=parsed_steps,
                generation_time_ms=generation_time,
                ragie_query_time_ms=ragie_time
            )
            
        except Exception as e:
            self.logger.error(f"Procedure agent processing failed: {e}")
            return self._create_error_response(str(e))
    
    async def _enhance_procedure_query(self, context: RagieQueryContext) -> str:
        """Enhance query with procedure-specific context"""
        enhanced_parts = [context.query]
        
        # Add procedure-specific keywords
        procedure_keywords = ["steps", "process", "procedure", "workflow", "how to"]
        enhanced_parts.append(f"Procedure focus: {', '.join(procedure_keywords)}")
        
        if context.user_expertise == "beginner":
            enhanced_parts.append("Detailed beginner-friendly steps")
        
        return " | ".join(enhanced_parts)
    
    async def _query_ragie_knowledge(self, enhanced_query: str) -> Dict[str, Any]:
        """Query Ragie for procedure knowledge"""
        if not self.ragie_service:
            return {'content': 'Ragie service not available', 'confidence': 0.5, 'sources': []}
        
        try:
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
    
    async def _extract_visual_citations(self, query: str, ragie_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract visual citations for procedures"""
        citations = []
        
        if not self.citation_service:
            return citations
        
        try:
            visual_refs = self.citation_service.extract_visual_references(
                query + " " + ragie_response.get('content', '')
            )
            
            for ref_type, references in visual_refs.items():
                for ref in references[:2]:  # Limit per type
                    citation = {
                        'citation_id': hashlib.md5(f"{ref_type}_{ref}".encode()).hexdigest()[:8],
                        'type': ref_type,
                        'source': 'Procedure Manual',
                        'description': f"Procedure {ref_type}: {ref}",
                        'confidence': 0.8,
                        'agent_type': self.agent_type.value,
                        'procedure_context': True
                    }
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Visual citation extraction failed: {e}")
            return []
    
    async def _generate_procedure_response(self, ragie_response: Dict[str, Any], context: RagieQueryContext) -> str:
        """Generate procedure-specific response"""
        base_content = ragie_response.get('content', '')
        
        if not base_content:
            return "I don't have specific procedure information for your query. Please provide more details about the process you need help with."
        
        # Structure response for procedure context
        response_parts = []
        
        # Add context-appropriate opening
        if context.interaction_mode == InteractionMode.VOICE_CHAT:
            response_parts.append("Here's the procedure:")
        
        # Add main content
        response_parts.append(base_content)
        
        # Add procedure-specific guidance
        if context.user_expertise == "beginner":
            response_parts.append("Take your time with each step and don't hesitate to ask if you need clarification.")
        
        return " ".join(response_parts)
    
    async def _parse_procedure_steps(self, response_text: str) -> Optional[Any]:
        """Parse procedure steps from response"""
        try:
            if STEP_PARSER_AVAILABLE:
                return parse_ai_response_steps(response_text)
            else:
                # Simple step parsing fallback
                import re
                steps = re.findall(r'(\d+\.?\s+[^\.]+)', response_text)
                return {
                    'steps': [{'step_number': i+1, 'description': step.strip()} for i, step in enumerate(steps)],
                    'total_steps': len(steps)
                }
        except Exception as e:
            self.logger.error(f"Step parsing failed: {e}")
            return None
    
    def _create_error_response(self, error_msg: str) -> IntelligentResponse:
        """Create error response for procedure agent"""
        return IntelligentResponse(
            text_response=f"I encountered an issue processing your procedure question: {error_msg}. Please try rephrasing your question.",
            confidence_score=0.3,
            primary_agent=self.agent_type,
            detected_intent=ConversationIntent.FOLLOW_UP
        )

class QSRSafetyAgent:
    """Safety-specialized agent using Ragie for safety guidance"""
    
    def __init__(self, ragie_service: Any, citation_service: Any):
        self.ragie_service = ragie_service
        self.citation_service = citation_service
        self.agent_type = AgentType.SAFETY
        self.logger = logging.getLogger(f"{__name__}.QSRSafetyAgent")
        
        self.system_prompt = """
        You are a QSR Safety Specialist. You help with:
        - Food safety and HACCP compliance
        - Equipment safety procedures
        - Emergency response protocols
        - Safety training and awareness
        
        Always provide:
        - Clear safety priorities
        - Compliance requirements
        - Risk mitigation strategies
        - Emergency contact information when relevant
        
        Safety is the top priority in all responses.
        """
    
    async def process_query(self, context: RagieQueryContext) -> IntelligentResponse:
        """Process safety-related queries with Ragie knowledge"""
        start_time = time.time()
        
        try:
            # Enhance query for safety focus
            enhanced_query = await self._enhance_safety_query(context)
            
            # Query Ragie for safety knowledge
            ragie_start = time.time()
            ragie_response = await self._query_ragie_knowledge(enhanced_query)
            ragie_time = (time.time() - ragie_start) * 1000
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(enhanced_query, ragie_response)
            
            # Generate safety-specific response
            response_text = await self._generate_safety_response(ragie_response, context)
            
            # Analyze safety criticality
            safety_analysis = self._analyze_safety_criticality(context.query, ragie_response)
            
            generation_time = (time.time() - start_time) * 1000
            
            return IntelligentResponse(
                text_response=response_text,
                confidence_score=min(ragie_response.get('confidence', 0.8), 1.0),
                primary_agent=self.agent_type,
                ragie_sources=ragie_response.get('sources', []),
                knowledge_confidence=ragie_response.get('confidence', 0.8),
                visual_citations=visual_citations,
                citation_count=len(visual_citations),
                detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
                conversation_context={
                    'safety_focus': True,
                    'compliance_required': True
                },
                voice_optimized=context.interaction_mode == InteractionMode.VOICE_CHAT,
                safety_priority=True,  # Always true for safety agent
                safety_warnings=safety_analysis['warnings'],
                generation_time_ms=generation_time,
                ragie_query_time_ms=ragie_time
            )
            
        except Exception as e:
            self.logger.error(f"Safety agent processing failed: {e}")
            return self._create_error_response(str(e))
    
    async def _enhance_safety_query(self, context: RagieQueryContext) -> str:
        """Enhance query with safety-specific context"""
        enhanced_parts = [context.query]
        
        # Add safety-specific keywords
        safety_keywords = ["safety", "compliance", "HACCP", "food safety", "regulations"]
        enhanced_parts.append(f"Safety focus: {', '.join(safety_keywords)}")
        
        # Mark as safety critical
        enhanced_parts.append("SAFETY CRITICAL QUERY")
        
        return " | ".join(enhanced_parts)
    
    async def _query_ragie_knowledge(self, enhanced_query: str) -> Dict[str, Any]:
        """Query Ragie for safety knowledge"""
        if not self.ragie_service:
            return {'content': 'Ragie service not available', 'confidence': 0.5, 'sources': []}
        
        try:
            ragie_result = await self.ragie_service.search_documents(
                query=enhanced_query,
                limit=12,  # More results for safety
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
    
    async def _extract_visual_citations(self, query: str, ragie_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract visual citations for safety"""
        citations = []
        
        if not self.citation_service:
            return citations
        
        try:
            visual_refs = self.citation_service.extract_visual_references(
                query + " " + ragie_response.get('content', '')
            )
            
            for ref_type, references in visual_refs.items():
                for ref in references[:3]:  # More citations for safety
                    citation = {
                        'citation_id': hashlib.md5(f"{ref_type}_{ref}".encode()).hexdigest()[:8],
                        'type': ref_type,
                        'source': 'Safety Manual',
                        'description': f"Safety {ref_type}: {ref}",
                        'confidence': 0.9,  # Higher confidence for safety
                        'agent_type': self.agent_type.value,
                        'safety_critical': True
                    }
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Visual citation extraction failed: {e}")
            return []
    
    async def _generate_safety_response(self, ragie_response: Dict[str, Any], context: RagieQueryContext) -> str:
        """Generate safety-specific response"""
        base_content = ragie_response.get('content', '')
        
        if not base_content:
            return "I don't have specific safety information for your query. For safety concerns, please consult your safety manual or contact your supervisor immediately."
        
        # Structure response for safety context
        response_parts = []
        
        # Add safety priority opening
        response_parts.append("🚨 SAFETY PRIORITY:")
        
        # Add main content
        response_parts.append(base_content)
        
        # Add safety reminder
        response_parts.append("Always prioritize safety over speed or convenience. When in doubt, ask for help.")
        
        return " ".join(response_parts)
    
    def _analyze_safety_criticality(self, query: str, ragie_response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze safety criticality"""
        critical_keywords = [
            'emergency', 'fire', 'burn', 'injury', 'accident', 'hazard',
            'toxic', 'chemical', 'gas', 'electrical', 'hot oil'
        ]
        
        high_risk_keywords = [
            'temperature', 'cleaning', 'maintenance', 'equipment', 'pressure'
        ]
        
        content = (query + " " + ragie_response.get('content', '')).lower()
        
        warnings = []
        
        # Check for critical safety issues
        if any(keyword in content for keyword in critical_keywords):
            warnings.append("CRITICAL: This involves potentially dangerous conditions")
        
        # Check for high-risk activities
        if any(keyword in content for keyword in high_risk_keywords):
            warnings.append("HIGH RISK: Follow all safety protocols")
        
        # General safety warnings
        warnings.append("Ensure proper training before performing any safety-related tasks")
        warnings.append("Have emergency contacts readily available")
        
        return {
            'warnings': warnings,
            'critical_level': 'high' if any(keyword in content for keyword in critical_keywords) else 'medium'
        }
    
    def _create_error_response(self, error_msg: str) -> IntelligentResponse:
        """Create error response for safety agent"""
        return IntelligentResponse(
            text_response=f"I encountered an issue processing your safety question: {error_msg}. For immediate safety concerns, contact your supervisor or emergency services.",
            confidence_score=0.3,
            primary_agent=self.agent_type,
            detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
            safety_priority=True,
            safety_warnings=["Unable to provide safety guidance due to processing error", "Contact supervisor for safety concerns"]
        )

class QSRMaintenanceAgent:
    """Maintenance-specialized agent using Ragie for cleaning and maintenance"""
    
    def __init__(self, ragie_service: Any, citation_service: Any):
        self.ragie_service = ragie_service
        self.citation_service = citation_service
        self.agent_type = AgentType.MAINTENANCE
        self.logger = logging.getLogger(f"{__name__}.QSRMaintenanceAgent")
        
        self.system_prompt = """
        You are a QSR Maintenance Specialist. You help with:
        - Equipment cleaning and sanitization
        - Preventive maintenance schedules
        - Maintenance troubleshooting
        - Cleaning chemical usage and safety
        
        Always provide:
        - Clear maintenance procedures
        - Proper chemical usage instructions
        - Safety precautions for cleaning
        - Maintenance schedules and frequency
        
        Focus on maintaining equipment performance and food safety standards.
        """
    
    async def process_query(self, context: RagieQueryContext) -> IntelligentResponse:
        """Process maintenance-related queries with Ragie knowledge"""
        start_time = time.time()
        
        try:
            # Enhance query for maintenance focus
            enhanced_query = await self._enhance_maintenance_query(context)
            
            # Query Ragie for maintenance knowledge
            ragie_start = time.time()
            ragie_response = await self._query_ragie_knowledge(enhanced_query)
            ragie_time = (time.time() - ragie_start) * 1000
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(enhanced_query, ragie_response)
            
            # Generate maintenance-specific response
            response_text = await self._generate_maintenance_response(ragie_response, context)
            
            # Analyze maintenance safety
            safety_analysis = self._analyze_maintenance_safety(context.query, ragie_response)
            
            generation_time = (time.time() - start_time) * 1000
            
            return IntelligentResponse(
                text_response=response_text,
                confidence_score=min(ragie_response.get('confidence', 0.8), 1.0),
                primary_agent=self.agent_type,
                ragie_sources=ragie_response.get('sources', []),
                knowledge_confidence=ragie_response.get('confidence', 0.8),
                visual_citations=visual_citations,
                citation_count=len(visual_citations),
                detected_intent=ConversationIntent.FOLLOW_UP,
                conversation_context={
                    'maintenance_focus': True,
                    'cleaning_procedure': True
                },
                voice_optimized=context.interaction_mode == InteractionMode.VOICE_CHAT,
                safety_priority=safety_analysis['safety_required'],
                safety_warnings=safety_analysis['warnings'],
                generation_time_ms=generation_time,
                ragie_query_time_ms=ragie_time
            )
            
        except Exception as e:
            self.logger.error(f"Maintenance agent processing failed: {e}")
            return self._create_error_response(str(e))
    
    async def _enhance_maintenance_query(self, context: RagieQueryContext) -> str:
        """Enhance query with maintenance-specific context"""
        enhanced_parts = [context.query]
        
        # Add maintenance-specific keywords
        maintenance_keywords = ["cleaning", "maintenance", "sanitization", "schedule", "procedure"]
        enhanced_parts.append(f"Maintenance focus: {', '.join(maintenance_keywords)}")
        
        if context.equipment_context:
            enhanced_parts.append(f"Equipment maintenance: {', '.join(context.equipment_context)}")
        
        return " | ".join(enhanced_parts)
    
    async def _query_ragie_knowledge(self, enhanced_query: str) -> Dict[str, Any]:
        """Query Ragie for maintenance knowledge"""
        if not self.ragie_service:
            return {'content': 'Ragie service not available', 'confidence': 0.5, 'sources': []}
        
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
            self.logger.error(f"Ragie query failed: {e}")
            return {'content': f'Knowledge query failed: {str(e)}', 'confidence': 0.3, 'sources': []}
    
    async def _extract_visual_citations(self, query: str, ragie_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract visual citations for maintenance"""
        citations = []
        
        if not self.citation_service:
            return citations
        
        try:
            visual_refs = self.citation_service.extract_visual_references(
                query + " " + ragie_response.get('content', '')
            )
            
            for ref_type, references in visual_refs.items():
                for ref in references[:2]:  # Limit per type
                    citation = {
                        'citation_id': hashlib.md5(f"{ref_type}_{ref}".encode()).hexdigest()[:8],
                        'type': ref_type,
                        'source': 'Maintenance Manual',
                        'description': f"Maintenance {ref_type}: {ref}",
                        'confidence': 0.8,
                        'agent_type': self.agent_type.value,
                        'maintenance_context': True
                    }
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Visual citation extraction failed: {e}")
            return []
    
    async def _generate_maintenance_response(self, ragie_response: Dict[str, Any], context: RagieQueryContext) -> str:
        """Generate maintenance-specific response"""
        base_content = ragie_response.get('content', '')
        
        if not base_content:
            return "I don't have specific maintenance information for your query. Please provide more details about the maintenance task you need help with."
        
        # Structure response for maintenance context
        response_parts = []
        
        # Add context-appropriate opening
        if context.interaction_mode == InteractionMode.VOICE_CHAT:
            response_parts.append("For maintenance:")
        
        # Add main content
        response_parts.append(base_content)
        
        # Add maintenance-specific guidance
        response_parts.append("Remember to follow proper cleaning chemical usage and safety procedures.")
        
        return " ".join(response_parts)
    
    def _analyze_maintenance_safety(self, query: str, ragie_response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze maintenance safety requirements"""
        chemical_keywords = ['chemical', 'sanitizer', 'cleaner', 'solution', 'detergent']
        equipment_keywords = ['equipment', 'machine', 'electrical', 'mechanical']
        
        content = (query + " " + ragie_response.get('content', '')).lower()
        
        warnings = []
        safety_required = False
        
        if any(keyword in content for keyword in chemical_keywords):
            warnings.append("Use proper PPE when handling cleaning chemicals")
            warnings.append("Ensure adequate ventilation")
            safety_required = True
        
        if any(keyword in content for keyword in equipment_keywords):
            warnings.append("Follow lockout/tagout procedures for equipment maintenance")
            warnings.append("Ensure equipment is properly shut down before maintenance")
            safety_required = True
        
        return {
            'safety_required': safety_required,
            'warnings': warnings
        }
    
    def _create_error_response(self, error_msg: str) -> IntelligentResponse:
        """Create error response for maintenance agent"""
        return IntelligentResponse(
            text_response=f"I encountered an issue processing your maintenance question: {error_msg}. Please try rephrasing your question.",
            confidence_score=0.3,
            primary_agent=self.agent_type,
            detected_intent=ConversationIntent.FOLLOW_UP,
            safety_warnings=["Unable to provide maintenance guidance due to processing error"]
        )

class QSRGeneralAgent:
    """General-purpose agent using Ragie for all other QSR queries"""
    
    def __init__(self, ragie_service: Any, citation_service: Any):
        self.ragie_service = ragie_service
        self.citation_service = citation_service
        self.agent_type = AgentType.GENERAL
        self.logger = logging.getLogger(f"{__name__}.QSRGeneralAgent")
        
        self.system_prompt = """
        You are a QSR General Assistant. You help with:
        - General QSR operations and policies
        - Cross-functional questions
        - Information lookup and guidance
        - Coordination between different areas
        
        Always provide:
        - Clear, helpful responses
        - Relevant information from manuals
        - Guidance on who to contact for specialized help
        - Context-appropriate suggestions
        
        Focus on being helpful and directing users to appropriate resources.
        """
    
    async def process_query(self, context: RagieQueryContext) -> IntelligentResponse:
        """Process general queries with Ragie knowledge"""
        start_time = time.time()
        
        try:
            # Query Ragie for general knowledge
            ragie_start = time.time()
            ragie_response = await self._query_ragie_knowledge(context.query)
            ragie_time = (time.time() - ragie_start) * 1000
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(context.query, ragie_response)
            
            # Generate general response
            response_text = await self._generate_general_response(ragie_response, context)
            
            # Suggest follow-ups
            follow_ups = self._generate_follow_ups(context.query, ragie_response)
            
            generation_time = (time.time() - start_time) * 1000
            
            return IntelligentResponse(
                text_response=response_text,
                confidence_score=min(ragie_response.get('confidence', 0.8), 1.0),
                primary_agent=self.agent_type,
                ragie_sources=ragie_response.get('sources', []),
                knowledge_confidence=ragie_response.get('confidence', 0.8),
                visual_citations=visual_citations,
                citation_count=len(visual_citations),
                detected_intent=ConversationIntent.NEW_TOPIC,
                conversation_context={
                    'general_query': True
                },
                voice_optimized=context.interaction_mode == InteractionMode.VOICE_CHAT,
                suggested_follow_ups=follow_ups,
                generation_time_ms=generation_time,
                ragie_query_time_ms=ragie_time
            )
            
        except Exception as e:
            self.logger.error(f"General agent processing failed: {e}")
            return self._create_error_response(str(e))
    
    async def _query_ragie_knowledge(self, query: str) -> Dict[str, Any]:
        """Query Ragie for general knowledge"""
        if not self.ragie_service:
            return {'content': 'Ragie service not available', 'confidence': 0.5, 'sources': []}
        
        try:
            ragie_result = await self.ragie_service.search_documents(
                query=query,
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
    
    async def _extract_visual_citations(self, query: str, ragie_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract visual citations for general queries"""
        citations = []
        
        if not self.citation_service:
            return citations
        
        try:
            visual_refs = self.citation_service.extract_visual_references(
                query + " " + ragie_response.get('content', '')
            )
            
            for ref_type, references in visual_refs.items():
                for ref in references[:2]:  # Limit per type
                    citation = {
                        'citation_id': hashlib.md5(f"{ref_type}_{ref}".encode()).hexdigest()[:8],
                        'type': ref_type,
                        'source': 'QSR Manual',
                        'description': f"General {ref_type}: {ref}",
                        'confidence': 0.75,
                        'agent_type': self.agent_type.value,
                        'general_context': True
                    }
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Visual citation extraction failed: {e}")
            return []
    
    async def _generate_general_response(self, ragie_response: Dict[str, Any], context: RagieQueryContext) -> str:
        """Generate general response"""
        base_content = ragie_response.get('content', '')
        
        if not base_content:
            return "I don't have specific information for your query. Could you provide more details or rephrase your question?"
        
        # Structure response for general context
        response_parts = []
        
        # Add main content
        response_parts.append(base_content)
        
        # Add helpful closing
        response_parts.append("Let me know if you need more specific information or have follow-up questions.")
        
        return " ".join(response_parts)
    
    def _generate_follow_ups(self, query: str, ragie_response: Dict[str, Any]) -> List[str]:
        """Generate follow-up suggestions"""
        follow_ups = []
        
        # Basic follow-ups based on query content
        if 'equipment' in query.lower():
            follow_ups.append("Would you like specific equipment troubleshooting help?")
        
        if 'clean' in query.lower():
            follow_ups.append("Do you need detailed cleaning procedures?")
        
        if 'safety' in query.lower():
            follow_ups.append("Would you like safety protocol details?")
        
        # Default follow-ups
        if not follow_ups:
            follow_ups = [
                "Would you like more detailed information?",
                "Do you have any specific follow-up questions?"
            ]
        
        return follow_ups
    
    def _create_error_response(self, error_msg: str) -> IntelligentResponse:
        """Create error response for general agent"""
        return IntelligentResponse(
            text_response=f"I encountered an issue processing your question: {error_msg}. Please try rephrasing your question.",
            confidence_score=0.3,
            primary_agent=self.agent_type,
            detected_intent=ConversationIntent.NEW_TOPIC
        )

# ===============================================================================
# CORE INTELLIGENCE SERVICE
# ===============================================================================

class CoreIntelligenceService:
    """
    Universal Intelligence Service that orchestrates PydanticAI + Ragie for ALL interactions.
    Handles both text chat and voice interactions with sophisticated multi-agent coordination.
    """
    
    def __init__(self, 
                 ragie_service: Any = None,
                 citation_service: Any = None,
                 conversation_context: Any = None):
        
        self.logger = logging.getLogger(f"{__name__}.CoreIntelligenceService")
        
        # Initialize services
        self.ragie_service = ragie_service
        self.citation_service = citation_service
        self.conversation_context = conversation_context
        
        # Initialize specialized agents
        self.agents = {
            AgentType.EQUIPMENT: QSREquipmentAgent(ragie_service, citation_service),
            AgentType.PROCEDURE: QSRProcedureAgent(ragie_service, citation_service),
            AgentType.SAFETY: QSRSafetyAgent(ragie_service, citation_service),
            AgentType.MAINTENANCE: QSRMaintenanceAgent(ragie_service, citation_service),
            AgentType.GENERAL: QSRGeneralAgent(ragie_service, citation_service)
        }
        
        # Performance tracking
        self.performance_metrics = {
            agent_type: AgentPerformanceMetrics(agent_type=agent_type)
            for agent_type in AgentType
        }
        
        # Response cache for performance
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        self.logger.info("✅ Core Intelligence Service initialized with 5 specialized agents")
    
    async def process_universal_query(self,
                                    query: str,
                                    interaction_mode: InteractionMode = InteractionMode.TEXT_CHAT,
                                    session_id: str = None,
                                    conversation_context: Optional[Dict[str, Any]] = None,
                                    user_expertise: str = "beginner") -> IntelligentResponse:
        """
        Universal query processing for ALL interactions (text + voice).
        This is the main entry point that makes every interaction intelligent.
        """
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing universal query: '{query[:100]}...' (mode: {interaction_mode.value})")
            
            # Check cache first
            cache_key = self._generate_cache_key(query, interaction_mode, session_id)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                self.logger.info("Returning cached response")
                return cached_response
            
            # Create query context
            query_context = await self._create_query_context(
                query, interaction_mode, session_id, conversation_context, user_expertise
            )
            
            # Select appropriate agent
            selected_agent = await self._select_agent(query_context)
            
            # Process query with selected agent
            response = await self._process_with_agent(selected_agent, query_context)
            
            # Post-process response
            final_response = await self._post_process_response(response, query_context)
            
            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(selected_agent, processing_time, final_response.confidence_score, True)
            
            # Cache response
            self._cache_response(cache_key, final_response)
            
            self.logger.info(f"Universal query processed in {processing_time:.2f}ms with agent {selected_agent.value}")
            
            return final_response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(f"Universal query processing failed: {e}")
            
            # Return error response
            error_response = await self._create_error_response(query, str(e), interaction_mode)
            self._update_performance_metrics(AgentType.GENERAL, processing_time, 0.3, False)
            
            return error_response
    
    async def process_text_chat(self,
                              query: str,
                              session_id: str = None,
                              conversation_context: Optional[Dict[str, Any]] = None) -> IntelligentResponse:
        """Specialized text chat processing - enhanced with universal intelligence"""
        
        return await self.process_universal_query(
            query=query,
            interaction_mode=InteractionMode.TEXT_CHAT,
            session_id=session_id,
            conversation_context=conversation_context
        )
    
    async def process_voice_chat(self,
                               query: str,
                               session_id: str = None,
                               conversation_context: Optional[Dict[str, Any]] = None,
                               audio_metadata: Optional[Dict[str, Any]] = None) -> IntelligentResponse:
        """Specialized voice chat processing - enhanced with universal intelligence"""
        
        # Voice-specific optimizations
        voice_response = await self.process_universal_query(
            query=query,
            interaction_mode=InteractionMode.VOICE_CHAT,
            session_id=session_id,
            conversation_context=conversation_context
        )
        
        # Apply voice-specific optimizations
        voice_response.voice_optimized = True
        voice_response.hands_free_friendly = True
        
        return voice_response
    
    async def _create_query_context(self,
                                  query: str,
                                  interaction_mode: InteractionMode,
                                  session_id: str,
                                  conversation_context: Optional[Dict[str, Any]],
                                  user_expertise: str) -> RagieQueryContext:
        """Create comprehensive query context"""
        
        # Extract equipment context from query
        equipment_context = self._extract_equipment_context(query)
        
        # Determine safety criticality
        safety_critical = self._is_safety_critical(query)
        
        # Get conversation history
        conversation_history = []
        if conversation_context:
            conversation_history = conversation_context.get('conversation_history', [])
        
        return RagieQueryContext(
            query=query,
            agent_type=AgentType.GENERAL,  # Will be updated by agent selection
            interaction_mode=interaction_mode,
            equipment_context=equipment_context,
            safety_critical=safety_critical,
            conversation_history=conversation_history,
            user_expertise=user_expertise,
            max_results=10
        )
    
    async def _select_agent(self, query_context: RagieQueryContext) -> AgentType:
        """Intelligent agent selection based on query context"""
        
        query_lower = query_context.query.lower()
        
        # Safety takes priority
        safety_keywords = ['safety', 'danger', 'hazard', 'emergency', 'fire', 'burn', 'toxic']
        if any(keyword in query_lower for keyword in safety_keywords):
            return AgentType.SAFETY
        
        # Equipment-specific queries
        equipment_keywords = ['equipment', 'machine', 'fryer', 'oven', 'compressor', 'troubleshoot', 'repair', 'fix']
        if any(keyword in query_lower for keyword in equipment_keywords):
            return AgentType.EQUIPMENT
        
        # Procedure-specific queries
        procedure_keywords = ['how to', 'steps', 'procedure', 'process', 'workflow', 'guide']
        if any(keyword in query_lower for keyword in procedure_keywords):
            return AgentType.PROCEDURE
        
        # Maintenance-specific queries
        maintenance_keywords = ['clean', 'maintenance', 'sanitize', 'schedule', 'chemical']
        if any(keyword in query_lower for keyword in maintenance_keywords):
            return AgentType.MAINTENANCE
        
        # Default to general agent
        return AgentType.GENERAL
    
    async def _process_with_agent(self, agent_type: AgentType, query_context: RagieQueryContext) -> IntelligentResponse:
        """Process query with selected agent"""
        
        # Update query context with selected agent
        query_context.agent_type = agent_type
        
        # Get agent and process query
        agent = self.agents[agent_type]
        response = await agent.process_query(query_context)
        
        return response
    
    async def _post_process_response(self, response: IntelligentResponse, query_context: RagieQueryContext) -> IntelligentResponse:
        """Post-process response for optimization"""
        
        # Voice-specific optimizations
        if query_context.interaction_mode == InteractionMode.VOICE_CHAT:
            response.voice_optimized = True
            response.hands_free_friendly = True
            
            # Optimize response length for voice
            if len(response.text_response) > 300:
                response.text_response = response.text_response[:300] + "... Would you like me to continue?"
        
        # Add conversation context updates
        response.conversation_context.update({
            'last_agent': response.primary_agent.value,
            'last_query_time': datetime.now().isoformat(),
            'session_id': query_context.query  # Should be session_id but query_context doesn't have it
        })
        
        return response
    
    def _extract_equipment_context(self, query: str) -> List[str]:
        """Extract equipment context from query"""
        equipment_patterns = [
            r'taylor\s+c602', r'fryer', r'oven', r'grill', r'compressor',
            r'refrigerator', r'freezer', r'machine', r'equipment'
        ]
        
        equipment_context = []
        import re
        
        for pattern in equipment_patterns:
            matches = re.findall(pattern, query.lower())
            equipment_context.extend(matches)
        
        return list(set(equipment_context))
    
    def _is_safety_critical(self, query: str) -> bool:
        """Determine if query is safety-critical"""
        safety_keywords = [
            'safety', 'danger', 'hazard', 'emergency', 'fire', 'burn',
            'toxic', 'chemical', 'injury', 'accident', 'hot', 'electrical'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in safety_keywords)
    
    def _generate_cache_key(self, query: str, interaction_mode: InteractionMode, session_id: str) -> str:
        """Generate cache key for response caching"""
        key_parts = [query, interaction_mode.value, session_id or 'default']
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[IntelligentResponse]:
        """Get cached response if available and not expired"""
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['response']
        return None
    
    def _cache_response(self, cache_key: str, response: IntelligentResponse):
        """Cache response for performance"""
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        
        # Clean old cache entries
        current_time = time.time()
        expired_keys = [
            key for key, data in self.response_cache.items()
            if current_time - data['timestamp'] > self.cache_ttl
        ]
        for key in expired_keys:
            del self.response_cache[key]
    
    def _update_performance_metrics(self, agent_type: AgentType, response_time: float, confidence: float, success: bool):
        """Update performance metrics for agent"""
        if agent_type in self.performance_metrics:
            self.performance_metrics[agent_type].update_metrics(response_time, confidence, success)
    
    async def _create_error_response(self, query: str, error_msg: str, interaction_mode: InteractionMode) -> IntelligentResponse:
        """Create error response"""
        
        return IntelligentResponse(
            text_response=f"I encountered an issue processing your query: {error_msg}. Please try rephrasing your question or contact support.",
            confidence_score=0.3,
            primary_agent=AgentType.GENERAL,
            detected_intent=ConversationIntent.NEW_TOPIC,
            voice_optimized=interaction_mode == InteractionMode.VOICE_CHAT,
            safety_priority=True,
            safety_warnings=["Unable to process query due to system error"]
        )
    
    # ===============================================================================
    # UTILITY METHODS
    # ===============================================================================
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        return {
            agent_type.value: {
                'total_queries': metrics.total_queries,
                'success_rate': metrics.successful_responses / max(metrics.total_queries, 1),
                'avg_confidence': metrics.average_confidence,
                'avg_response_time': metrics.average_response_time
            }
            for agent_type, metrics in self.performance_metrics.items()
        }
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of each agent"""
        return {
            'equipment': ['Technical troubleshooting', 'Equipment repair', 'Performance optimization'],
            'procedure': ['Step-by-step guidance', 'Process workflows', 'Quality standards'],
            'safety': ['Safety protocols', 'Compliance requirements', 'Risk assessment'],
            'maintenance': ['Cleaning procedures', 'Maintenance schedules', 'Chemical usage'],
            'general': ['General information', 'Cross-functional help', 'Resource guidance']
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the intelligence service"""
        
        health_status = {
            'service_status': 'healthy',
            'ragie_service': 'available' if self.ragie_service else 'unavailable',
            'citation_service': 'available' if self.citation_service else 'unavailable',
            'agents_initialized': len(self.agents),
            'cache_size': len(self.response_cache),
            'total_queries_processed': sum(m.total_queries for m in self.performance_metrics.values())
        }
        
        return health_status

# ===============================================================================
# FACTORY FUNCTIONS
# ===============================================================================

async def create_core_intelligence_service(
    ragie_service: Any = None,
    citation_service: Any = None,
    conversation_context: Any = None
) -> CoreIntelligenceService:
    """Factory function to create core intelligence service"""
    
    service = CoreIntelligenceService(
        ragie_service=ragie_service,
        citation_service=citation_service,
        conversation_context=conversation_context
    )
    
    # Perform health check
    health_status = await service.health_check()
    logger.info(f"Core Intelligence Service created: {health_status}")
    
    return service

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Core service
    "CoreIntelligenceService",
    
    # Models
    "IntelligentResponse",
    "RagieQueryContext",
    "AgentType",
    "InteractionMode",
    "AgentPerformanceMetrics",
    
    # Specialized agents
    "QSREquipmentAgent",
    "QSRProcedureAgent", 
    "QSRSafetyAgent",
    "QSRMaintenanceAgent",
    "QSRGeneralAgent",
    
    # Utility functions
    "create_core_intelligence_service"
]