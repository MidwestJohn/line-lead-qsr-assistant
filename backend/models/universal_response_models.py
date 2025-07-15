"""
Universal Response Models for PydanticAI + Ragie Integration
==========================================================

Universal response models that work across text and voice interactions
with consistent Ragie integration. These models enable:

- Unified intelligence across all interaction modes
- Consistent Ragie knowledge integration
- Cross-modal context preservation
- Response adaptation for different formats
- Performance tracking and optimization

CLEAN IMPLEMENTATION: Uses ONLY Ragie + PydanticAI, no Graph-RAG dependencies.

Author: Generated with Memex (https://memex.tech)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)

# ===============================================================================
# CORE ENUMS AND TYPES
# ===============================================================================

# Import AgentType from shared location
from ..agents.types import AgentType

class InteractionMode(str, Enum):
    """Interaction modes for universal responses"""
    TEXT_CHAT = "text_chat"
    VOICE_CHAT = "voice_chat"
    HYBRID = "hybrid"

class ResponseFormat(str, Enum):
    """Response format types"""
    TEXT_UI = "text_ui"           # For chat UI display
    VOICE_AUDIO = "voice_audio"   # For TTS synthesis
    STRUCTURED = "structured"     # For API consumption
    HYBRID = "hybrid"            # For multi-modal display

class ConversationIntent(str, Enum):
    """Conversation intents"""
    EQUIPMENT_QUESTION = "equipment_question"
    PROCEDURE_QUESTION = "procedure_question"
    SAFETY_QUESTION = "safety_question"
    MAINTENANCE_QUESTION = "maintenance_question"
    GENERAL_QUESTION = "general_question"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"

class SafetyLevel(str, Enum):
    """Safety criticality levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ===============================================================================
# RAGIE INTEGRATION MODELS
# ===============================================================================

class RagieKnowledge(BaseModel):
    """Knowledge snippet from Ragie with context"""
    
    # Core knowledge
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_title: str
    source_page: Optional[int] = None
    
    # Context information
    agent_type: AgentType
    knowledge_type: Literal["factual", "procedural", "safety", "maintenance"] = "factual"
    equipment_context: Optional[List[str]] = None
    
    # Metadata
    ragie_query: str
    retrieval_time_ms: Optional[float] = None
    relevance_score: Optional[float] = None
    
    # Quality indicators
    completeness: float = Field(ge=0.0, le=1.0, default=0.8)
    accuracy_confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    
    def get_knowledge_id(self) -> str:
        """Generate unique knowledge ID"""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
        return f"{self.agent_type.value}_{content_hash}"
    
    def is_high_quality(self) -> bool:
        """Check if knowledge meets high quality thresholds"""
        return (self.confidence >= 0.8 and 
                self.completeness >= 0.8 and 
                self.accuracy_confidence >= 0.8)

class RagieCitation(BaseModel):
    """Visual citation from Ragie with enhanced context"""
    
    # Citation identification
    citation_id: str
    citation_type: Literal["image", "diagram", "table", "chart", "flowchart", "schematic"] = "image"
    
    # Source information
    source_document: str
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    
    # Visual content
    title: str
    description: Optional[str] = None
    visual_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Context integration
    agent_type: AgentType
    equipment_context: Optional[List[str]] = None
    procedure_step: Optional[int] = None
    safety_level: SafetyLevel = SafetyLevel.LOW
    
    # Ragie integration
    ragie_confidence: float = Field(ge=0.0, le=1.0)
    ragie_relevance: float = Field(ge=0.0, le=1.0)
    ragie_source: bool = True
    
    # Usage tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    user_feedback: Optional[float] = None
    
    def increment_access(self):
        """Track citation usage"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy citation format for backward compatibility"""
        return {
            'citation_id': self.citation_id,
            'type': self.citation_type,
            'source': self.source_document,
            'page': self.source_page,
            'description': self.description,
            'confidence': self.ragie_confidence,
            'agent_type': self.agent_type.value,
            'equipment_context': self.equipment_context,
            'safety_level': self.safety_level.value
        }

class RagieEquipmentContext(BaseModel):
    """Equipment context from Ragie knowledge"""
    
    # Equipment identification
    equipment_name: str
    equipment_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    
    # Ragie knowledge
    ragie_knowledge: List[RagieKnowledge] = Field(default_factory=list)
    technical_specs: Dict[str, Any] = Field(default_factory=dict)
    
    # Operational context
    current_status: Optional[str] = None
    common_issues: List[str] = Field(default_factory=list)
    maintenance_schedule: Optional[str] = None
    
    # Safety information
    safety_warnings: List[str] = Field(default_factory=list)
    safety_level: SafetyLevel = SafetyLevel.LOW
    
    # Related content
    related_procedures: List[str] = Field(default_factory=list)
    visual_citations: List[RagieCitation] = Field(default_factory=list)
    
    def get_primary_knowledge(self) -> Optional[RagieKnowledge]:
        """Get highest confidence knowledge"""
        if not self.ragie_knowledge:
            return None
        return max(self.ragie_knowledge, key=lambda k: k.confidence)
    
    def get_safety_critical_info(self) -> List[str]:
        """Get safety-critical information"""
        critical_info = []
        
        # Add safety warnings
        critical_info.extend(self.safety_warnings)
        
        # Add safety knowledge
        for knowledge in self.ragie_knowledge:
            if knowledge.knowledge_type == "safety":
                critical_info.append(knowledge.content)
        
        return critical_info

class RagieProcedureContext(BaseModel):
    """Procedure context from Ragie knowledge"""
    
    # Procedure identification
    procedure_name: str
    procedure_type: Literal["operation", "maintenance", "cleaning", "troubleshooting", "setup"]
    
    # Ragie knowledge
    ragie_knowledge: List[RagieKnowledge] = Field(default_factory=list)
    
    # Procedure details
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_duration: Optional[str] = None
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    
    # Context
    equipment_required: List[str] = Field(default_factory=list)
    tools_required: List[str] = Field(default_factory=list)
    safety_requirements: List[str] = Field(default_factory=list)
    
    # Quality control
    verification_steps: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    
    # Visual aids
    visual_citations: List[RagieCitation] = Field(default_factory=list)
    
    def get_step_count(self) -> int:
        """Get total number of steps"""
        return len(self.steps)
    
    def get_safety_critical_steps(self) -> List[Dict[str, Any]]:
        """Get safety-critical steps"""
        return [step for step in self.steps if step.get('safety_critical', False)]

class RagieContext(BaseModel):
    """Context passed between agents with Ragie integration"""
    
    # Session context
    session_id: str
    interaction_mode: InteractionMode
    agent_type: AgentType
    
    # Ragie integration
    ragie_knowledge: List[RagieKnowledge] = Field(default_factory=list)
    total_ragie_queries: int = 0
    avg_ragie_confidence: float = 0.0
    
    # Equipment context
    equipment_context: Optional[RagieEquipmentContext] = None
    
    # Procedure context
    procedure_context: Optional[RagieProcedureContext] = None
    
    # Visual citations
    visual_citations: List[RagieCitation] = Field(default_factory=list)
    
    # Conversation history
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Performance metrics
    total_response_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def add_ragie_knowledge(self, knowledge: RagieKnowledge):
        """Add Ragie knowledge and update metrics"""
        self.ragie_knowledge.append(knowledge)
        self.total_ragie_queries += 1
        
        # Update average confidence
        total_confidence = sum(k.confidence for k in self.ragie_knowledge)
        self.avg_ragie_confidence = total_confidence / len(self.ragie_knowledge)
    
    def get_high_confidence_knowledge(self, threshold: float = 0.8) -> List[RagieKnowledge]:
        """Get high-confidence knowledge"""
        return [k for k in self.ragie_knowledge if k.confidence >= threshold]
    
    def get_equipment_mentions(self) -> List[str]:
        """Get all equipment mentioned in context"""
        equipment_mentions = []
        
        if self.equipment_context:
            equipment_mentions.append(self.equipment_context.equipment_name)
        
        for knowledge in self.ragie_knowledge:
            if knowledge.equipment_context:
                equipment_mentions.extend(knowledge.equipment_context)
        
        return list(set(equipment_mentions))

# ===============================================================================
# UNIVERSAL RESPONSE MODELS
# ===============================================================================

class UniversalQSRResponse(BaseModel):
    """Base universal response model for all interactions with Ragie"""
    
    # Core response
    text_response: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Agent context
    primary_agent: AgentType
    contributing_agents: List[AgentType] = Field(default_factory=list)
    
    # Interaction context
    interaction_mode: InteractionMode
    response_format: ResponseFormat
    detected_intent: ConversationIntent
    
    # Ragie integration
    ragie_context: RagieContext
    knowledge_sources: List[RagieKnowledge] = Field(default_factory=list)
    
    # Visual citations
    visual_citations: List[RagieCitation] = Field(default_factory=list)
    citation_count: int = 0
    
    # Safety and compliance
    safety_level: SafetyLevel = SafetyLevel.LOW
    safety_warnings: List[str] = Field(default_factory=list)
    compliance_notes: List[str] = Field(default_factory=list)
    
    # Performance metrics
    generation_time_ms: float = 0.0
    ragie_query_time_ms: float = 0.0
    total_processing_time_ms: float = 0.0
    
    # Response metadata
    response_id: str = Field(default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('citation_count', always=True)
    def update_citation_count(cls, v, values):
        """Update citation count based on visual citations"""
        visual_citations = values.get('visual_citations', [])
        return len(visual_citations)
    
    def get_response_summary(self) -> Dict[str, Any]:
        """Get response summary for logging/monitoring"""
        return {
            'response_id': self.response_id,
            'agent': self.primary_agent.value,
            'interaction_mode': self.interaction_mode.value,
            'confidence': self.confidence_score,
            'knowledge_sources': len(self.knowledge_sources),
            'visual_citations': self.citation_count,
            'safety_level': self.safety_level.value,
            'processing_time_ms': self.total_processing_time_ms
        }
    
    def is_high_quality(self) -> bool:
        """Check if response meets high quality standards"""
        return (self.confidence_score >= 0.8 and
                len(self.knowledge_sources) > 0 and
                self.total_processing_time_ms < 5000)  # Under 5 seconds
    
    def get_equipment_context(self) -> Optional[RagieEquipmentContext]:
        """Get equipment context if available"""
        return self.ragie_context.equipment_context
    
    def get_procedure_context(self) -> Optional[RagieProcedureContext]:
        """Get procedure context if available"""
        return self.ragie_context.procedure_context

class TextChatResponse(UniversalQSRResponse):
    """Text chat response optimized for UI display"""
    
    # Text UI specific fields
    response_format: ResponseFormat = ResponseFormat.TEXT_UI
    formatted_text: str = ""
    
    # UI display elements
    show_citations: bool = True
    show_follow_ups: bool = True
    show_safety_warnings: bool = True
    
    # Follow-up suggestions
    suggested_follow_ups: List[str] = Field(default_factory=list)
    
    # UI formatting
    text_formatting: Dict[str, Any] = Field(default_factory=dict)
    
    # Interaction elements
    requires_user_input: bool = False
    input_prompt: Optional[str] = None
    
    def format_for_ui(self) -> str:
        """Format response for text UI display"""
        formatted_parts = []
        
        # Main response
        formatted_parts.append(self.text_response)
        
        # Safety warnings (if any)
        if self.safety_warnings and self.show_safety_warnings:
            formatted_parts.append("\n⚠️ Safety Warnings:")
            for warning in self.safety_warnings:
                formatted_parts.append(f"• {warning}")
        
        # Citation references (if any)
        if self.visual_citations and self.show_citations:
            formatted_parts.append(f"\n📋 See {len(self.visual_citations)} visual reference(s)")
        
        # Follow-up suggestions
        if self.suggested_follow_ups and self.show_follow_ups:
            formatted_parts.append("\n💡 You might also ask:")
            for follow_up in self.suggested_follow_ups[:3]:  # Limit to 3
                formatted_parts.append(f"• {follow_up}")
        
        self.formatted_text = "\n".join(formatted_parts)
        return self.formatted_text
    
    def to_api_format(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            'response': self.text_response,
            'formatted_response': self.format_for_ui(),
            'agent': self.primary_agent.value,
            'confidence': self.confidence_score,
            'visual_citations': [c.to_legacy_format() for c in self.visual_citations],
            'safety_priority': self.safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL],
            'safety_warnings': self.safety_warnings,
            'suggested_follow_ups': self.suggested_follow_ups,
            'knowledge_sources': len(self.knowledge_sources),
            'response_time_ms': self.total_processing_time_ms
        }

class VoiceResponse(UniversalQSRResponse):
    """Voice response optimized for audio synthesis"""
    
    # Voice specific fields
    response_format: ResponseFormat = ResponseFormat.VOICE_AUDIO
    audio_optimized_text: str = ""
    
    # TTS optimization
    speech_rate: Literal["slow", "normal", "fast"] = "normal"
    emphasis_words: List[str] = Field(default_factory=list)
    pause_points: List[int] = Field(default_factory=list)  # Character positions
    
    # Voice interaction
    should_continue_listening: bool = True
    voice_state: Literal["listening", "processing", "responding"] = "listening"
    expect_response: bool = False
    
    # Audio metadata
    audio_data: Optional[str] = None
    audio_duration_ms: Optional[int] = None
    audio_format: str = "mp3"
    
    # Hands-free optimization
    hands_free_friendly: bool = True
    requires_visual_confirmation: bool = False
    
    def optimize_for_speech(self) -> str:
        """Optimize text for speech synthesis"""
        speech_parts = []
        
        # Safety priority announcement
        if self.safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]:
            speech_parts.append("Safety Priority. ")
        
        # Main response
        speech_text = self.text_response
        
        # Replace abbreviations and technical terms
        speech_replacements = {
            "°F": " degrees Fahrenheit",
            "°C": " degrees Celsius",
            "PPE": "Personal Protective Equipment",
            "HACCP": "H A C C P",
            "QSR": "Q S R",
        }
        
        for abbrev, full_form in speech_replacements.items():
            speech_text = speech_text.replace(abbrev, full_form)
        
        speech_parts.append(speech_text)
        
        # Add safety warnings for voice
        if self.safety_warnings:
            speech_parts.append("Important safety reminders: ")
            for warning in self.safety_warnings[:2]:  # Limit to 2 for voice
                speech_parts.append(f"{warning}. ")
        
        # Add visual citation notice
        if self.visual_citations:
            speech_parts.append(f"I've provided {len(self.visual_citations)} visual reference that you can see on screen.")
        
        self.audio_optimized_text = " ".join(speech_parts)
        return self.audio_optimized_text
    
    def to_legacy_voice_format(self) -> Dict[str, Any]:
        """Convert to legacy VoiceResponse format"""
        return {
            'text_response': self.optimize_for_speech(),
            'audio_data': self.audio_data,
            'should_continue_listening': self.should_continue_listening,
            'next_voice_state': self.voice_state,
            'detected_intent': self.detected_intent.value,
            'context_updates': {'equipment_context': self.get_equipment_context()},
            'conversation_complete': False,
            'confidence_score': self.confidence_score,
            'suggested_follow_ups': [],  # Not used in voice
            'safety_priority': self.safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL],
            'response_type': self._get_response_type(),
            'hands_free_recommendation': self.hands_free_friendly,
            'primary_agent': self.primary_agent.value,
            'visual_citations': [c.to_legacy_format() for c in self.visual_citations]
        }
    
    def _get_response_type(self) -> str:
        """Get response type based on agent"""
        type_map = {
            AgentType.EQUIPMENT: "factual",
            AgentType.PROCEDURE: "procedural",
            AgentType.SAFETY: "safety",
            AgentType.MAINTENANCE: "procedural",
            AgentType.GENERAL: "factual"
        }
        return type_map.get(self.primary_agent, "factual")

class HybridResponse(UniversalQSRResponse):
    """Hybrid response for multi-modal interactions"""
    
    # Hybrid specific fields
    response_format: ResponseFormat = ResponseFormat.HYBRID
    
    # Text and voice variants
    text_variant: Optional[TextChatResponse] = None
    voice_variant: Optional[VoiceResponse] = None
    
    # Multi-modal elements
    visual_emphasis: List[str] = Field(default_factory=list)
    audio_cues: List[str] = Field(default_factory=list)
    
    # Interaction coordination
    primary_mode: InteractionMode = InteractionMode.TEXT_CHAT
    fallback_mode: InteractionMode = InteractionMode.VOICE_CHAT
    
    def get_text_response(self) -> TextChatResponse:
        """Get text response variant"""
        if self.text_variant:
            return self.text_variant
        
        # Create text variant from universal response
        return TextChatResponse(
            text_response=self.text_response,
            confidence_score=self.confidence_score,
            primary_agent=self.primary_agent,
            contributing_agents=self.contributing_agents,
            interaction_mode=InteractionMode.TEXT_CHAT,
            response_format=ResponseFormat.TEXT_UI,
            detected_intent=self.detected_intent,
            ragie_context=self.ragie_context,
            knowledge_sources=self.knowledge_sources,
            visual_citations=self.visual_citations,
            safety_level=self.safety_level,
            safety_warnings=self.safety_warnings,
            generation_time_ms=self.generation_time_ms,
            ragie_query_time_ms=self.ragie_query_time_ms,
            total_processing_time_ms=self.total_processing_time_ms
        )
    
    def get_voice_response(self) -> VoiceResponse:
        """Get voice response variant"""
        if self.voice_variant:
            return self.voice_variant
        
        # Create voice variant from universal response
        return VoiceResponse(
            text_response=self.text_response,
            confidence_score=self.confidence_score,
            primary_agent=self.primary_agent,
            contributing_agents=self.contributing_agents,
            interaction_mode=InteractionMode.VOICE_CHAT,
            response_format=ResponseFormat.VOICE_AUDIO,
            detected_intent=self.detected_intent,
            ragie_context=self.ragie_context,
            knowledge_sources=self.knowledge_sources,
            visual_citations=self.visual_citations,
            safety_level=self.safety_level,
            safety_warnings=self.safety_warnings,
            generation_time_ms=self.generation_time_ms,
            ragie_query_time_ms=self.ragie_query_time_ms,
            total_processing_time_ms=self.total_processing_time_ms
        )

# ===============================================================================
# RESPONSE FACTORY
# ===============================================================================

class UniversalResponseFactory:
    """Factory for creating universal responses with Ragie integration"""
    
    @staticmethod
    def create_text_response(
        text_response: str,
        agent_type: AgentType,
        ragie_context: RagieContext,
        knowledge_sources: List[RagieKnowledge] = None,
        visual_citations: List[RagieCitation] = None,
        **kwargs
    ) -> TextChatResponse:
        """Create text chat response"""
        
        return TextChatResponse(
            text_response=text_response,
            primary_agent=agent_type,
            interaction_mode=InteractionMode.TEXT_CHAT,
            response_format=ResponseFormat.TEXT_UI,
            ragie_context=ragie_context,
            knowledge_sources=knowledge_sources or [],
            visual_citations=visual_citations or [],
            detected_intent=ConversationIntent.GENERAL_QUESTION,
            confidence_score=kwargs.get('confidence_score', 0.8),
            safety_level=kwargs.get('safety_level', SafetyLevel.LOW),
            safety_warnings=kwargs.get('safety_warnings', []),
            generation_time_ms=kwargs.get('generation_time_ms', 0.0),
            ragie_query_time_ms=kwargs.get('ragie_query_time_ms', 0.0),
            total_processing_time_ms=kwargs.get('total_processing_time_ms', 0.0)
        )
    
    @staticmethod
    def create_voice_response(
        text_response: str,
        agent_type: AgentType,
        ragie_context: RagieContext,
        knowledge_sources: List[RagieKnowledge] = None,
        visual_citations: List[RagieCitation] = None,
        **kwargs
    ) -> VoiceResponse:
        """Create voice response"""
        
        return VoiceResponse(
            text_response=text_response,
            primary_agent=agent_type,
            interaction_mode=InteractionMode.VOICE_CHAT,
            response_format=ResponseFormat.VOICE_AUDIO,
            ragie_context=ragie_context,
            knowledge_sources=knowledge_sources or [],
            visual_citations=visual_citations or [],
            detected_intent=ConversationIntent.GENERAL_QUESTION,
            confidence_score=kwargs.get('confidence_score', 0.8),
            safety_level=kwargs.get('safety_level', SafetyLevel.LOW),
            safety_warnings=kwargs.get('safety_warnings', []),
            generation_time_ms=kwargs.get('generation_time_ms', 0.0),
            ragie_query_time_ms=kwargs.get('ragie_query_time_ms', 0.0),
            total_processing_time_ms=kwargs.get('total_processing_time_ms', 0.0),
            should_continue_listening=kwargs.get('should_continue_listening', True),
            hands_free_friendly=kwargs.get('hands_free_friendly', True)
        )
    
    @staticmethod
    def create_hybrid_response(
        text_response: str,
        agent_type: AgentType,
        ragie_context: RagieContext,
        knowledge_sources: List[RagieKnowledge] = None,
        visual_citations: List[RagieCitation] = None,
        **kwargs
    ) -> HybridResponse:
        """Create hybrid response"""
        
        return HybridResponse(
            text_response=text_response,
            primary_agent=agent_type,
            interaction_mode=InteractionMode.HYBRID,
            response_format=ResponseFormat.HYBRID,
            ragie_context=ragie_context,
            knowledge_sources=knowledge_sources or [],
            visual_citations=visual_citations or [],
            detected_intent=ConversationIntent.GENERAL_QUESTION,
            confidence_score=kwargs.get('confidence_score', 0.8),
            safety_level=kwargs.get('safety_level', SafetyLevel.LOW),
            safety_warnings=kwargs.get('safety_warnings', []),
            generation_time_ms=kwargs.get('generation_time_ms', 0.0),
            ragie_query_time_ms=kwargs.get('ragie_query_time_ms', 0.0),
            total_processing_time_ms=kwargs.get('total_processing_time_ms', 0.0),
            primary_mode=kwargs.get('primary_mode', InteractionMode.TEXT_CHAT)
        )

# ===============================================================================
# RESPONSE ADAPTATION UTILITIES
# ===============================================================================

class ResponseAdapter:
    """Utilities for adapting responses across interaction modes"""
    
    @staticmethod
    def adapt_text_to_voice(text_response: TextChatResponse) -> VoiceResponse:
        """Adapt text response to voice format"""
        
        # Create voice response from text response
        voice_response = VoiceResponse(
            text_response=text_response.text_response,
            confidence_score=text_response.confidence_score,
            primary_agent=text_response.primary_agent,
            contributing_agents=text_response.contributing_agents,
            interaction_mode=InteractionMode.VOICE_CHAT,
            response_format=ResponseFormat.VOICE_AUDIO,
            detected_intent=text_response.detected_intent,
            ragie_context=text_response.ragie_context,
            knowledge_sources=text_response.knowledge_sources,
            visual_citations=text_response.visual_citations,
            safety_level=text_response.safety_level,
            safety_warnings=text_response.safety_warnings,
            generation_time_ms=text_response.generation_time_ms,
            ragie_query_time_ms=text_response.ragie_query_time_ms,
            total_processing_time_ms=text_response.total_processing_time_ms
        )
        
        # Optimize for speech
        voice_response.optimize_for_speech()
        
        return voice_response
    
    @staticmethod
    def adapt_voice_to_text(voice_response: VoiceResponse) -> TextChatResponse:
        """Adapt voice response to text format"""
        
        # Create text response from voice response
        text_response = TextChatResponse(
            text_response=voice_response.text_response,
            confidence_score=voice_response.confidence_score,
            primary_agent=voice_response.primary_agent,
            contributing_agents=voice_response.contributing_agents,
            interaction_mode=InteractionMode.TEXT_CHAT,
            response_format=ResponseFormat.TEXT_UI,
            detected_intent=voice_response.detected_intent,
            ragie_context=voice_response.ragie_context,
            knowledge_sources=voice_response.knowledge_sources,
            visual_citations=voice_response.visual_citations,
            safety_level=voice_response.safety_level,
            safety_warnings=voice_response.safety_warnings,
            generation_time_ms=voice_response.generation_time_ms,
            ragie_query_time_ms=voice_response.ragie_query_time_ms,
            total_processing_time_ms=voice_response.total_processing_time_ms
        )
        
        # Format for UI
        text_response.format_for_ui()
        
        return text_response
    
    @staticmethod
    def preserve_context_across_modes(
        source_response: UniversalQSRResponse,
        target_mode: InteractionMode
    ) -> RagieContext:
        """Preserve context when switching interaction modes"""
        
        # Create updated context
        updated_context = RagieContext(
            session_id=source_response.ragie_context.session_id,
            interaction_mode=target_mode,
            agent_type=source_response.primary_agent,
            ragie_knowledge=source_response.ragie_context.ragie_knowledge,
            total_ragie_queries=source_response.ragie_context.total_ragie_queries,
            avg_ragie_confidence=source_response.ragie_context.avg_ragie_confidence,
            equipment_context=source_response.ragie_context.equipment_context,
            procedure_context=source_response.ragie_context.procedure_context,
            visual_citations=source_response.visual_citations,
            conversation_history=source_response.ragie_context.conversation_history,
            total_response_time_ms=source_response.total_processing_time_ms,
            cache_hits=source_response.ragie_context.cache_hits,
            cache_misses=source_response.ragie_context.cache_misses
        )
        
        # Add current interaction to history
        updated_context.conversation_history.append({
            'timestamp': source_response.created_at.isoformat(),
            'agent': source_response.primary_agent.value,
            'mode': source_response.interaction_mode.value,
            'response': source_response.text_response,
            'confidence': source_response.confidence_score,
            'safety_level': source_response.safety_level.value
        })
        
        return updated_context

# ===============================================================================
# PERFORMANCE MONITORING
# ===============================================================================

class ResponseMetrics(BaseModel):
    """Performance metrics for universal responses"""
    
    # Response quality
    avg_confidence: float = 0.0
    high_quality_responses: int = 0
    total_responses: int = 0
    
    # Ragie integration
    avg_ragie_confidence: float = 0.0
    ragie_queries_per_response: float = 0.0
    knowledge_sources_per_response: float = 0.0
    
    # Performance
    avg_response_time_ms: float = 0.0
    avg_ragie_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    
    # By interaction mode
    text_responses: int = 0
    voice_responses: int = 0
    hybrid_responses: int = 0
    
    # By agent type
    agent_usage: Dict[str, int] = Field(default_factory=dict)
    
    # Safety metrics
    safety_critical_responses: int = 0
    safety_warnings_issued: int = 0
    
    def update_with_response(self, response: UniversalQSRResponse):
        """Update metrics with new response"""
        self.total_responses += 1
        
        # Quality metrics
        self.avg_confidence = (self.avg_confidence * (self.total_responses - 1) + response.confidence_score) / self.total_responses
        
        if response.is_high_quality():
            self.high_quality_responses += 1
        
        # Ragie metrics
        self.avg_ragie_confidence = (self.avg_ragie_confidence * (self.total_responses - 1) + response.ragie_context.avg_ragie_confidence) / self.total_responses
        self.ragie_queries_per_response = (self.ragie_queries_per_response * (self.total_responses - 1) + response.ragie_context.total_ragie_queries) / self.total_responses
        self.knowledge_sources_per_response = (self.knowledge_sources_per_response * (self.total_responses - 1) + len(response.knowledge_sources)) / self.total_responses
        
        # Performance metrics
        self.avg_response_time_ms = (self.avg_response_time_ms * (self.total_responses - 1) + response.total_processing_time_ms) / self.total_responses
        self.avg_ragie_time_ms = (self.avg_ragie_time_ms * (self.total_responses - 1) + response.ragie_query_time_ms) / self.total_responses
        
        # Mode tracking
        if response.interaction_mode == InteractionMode.TEXT_CHAT:
            self.text_responses += 1
        elif response.interaction_mode == InteractionMode.VOICE_CHAT:
            self.voice_responses += 1
        elif response.interaction_mode == InteractionMode.HYBRID:
            self.hybrid_responses += 1
        
        # Agent usage
        agent_key = response.primary_agent.value
        self.agent_usage[agent_key] = self.agent_usage.get(agent_key, 0) + 1
        
        # Safety metrics
        if response.safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]:
            self.safety_critical_responses += 1
        
        if response.safety_warnings:
            self.safety_warnings_issued += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            'total_responses': self.total_responses,
            'avg_confidence': round(self.avg_confidence, 3),
            'high_quality_rate': self.high_quality_responses / max(self.total_responses, 1),
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
            'ragie_performance': {
                'avg_confidence': round(self.avg_ragie_confidence, 3),
                'queries_per_response': round(self.ragie_queries_per_response, 2),
                'knowledge_sources_per_response': round(self.knowledge_sources_per_response, 2)
            },
            'interaction_modes': {
                'text': self.text_responses,
                'voice': self.voice_responses,
                'hybrid': self.hybrid_responses
            },
            'agent_usage': self.agent_usage,
            'safety_metrics': {
                'critical_responses': self.safety_critical_responses,
                'warnings_issued': self.safety_warnings_issued
            }
        }

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Core models
    "UniversalQSRResponse",
    "TextChatResponse",
    "VoiceResponse",
    "HybridResponse",
    
    # Ragie integration
    "RagieKnowledge",
    "RagieCitation",
    "RagieEquipmentContext",
    "RagieProcedureContext",
    "RagieContext",
    
    # Enums
    "AgentType",
    "InteractionMode",
    "ResponseFormat",
    "ConversationIntent",
    "SafetyLevel",
    
    # Utilities
    "UniversalResponseFactory",
    "ResponseAdapter",
    "ResponseMetrics"
]