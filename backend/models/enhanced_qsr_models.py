"""
Enhanced QSR Response Models with Advanced Visual Integration
===========================================================

Advanced Pydantic models that enhance existing visual citations system
while integrating seamlessly with the multi-agent architecture.

Builds upon:
- Existing VoiceResponse and visual citation system
- Working Graph-RAG with 20 entities and 40 relationships  
- MultiModalCitationService and PDF extraction
- Neo4j visual storage and equipment tracking

Author: Generated with Memex (https://memex.tech)
"""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum
import time
import logging
from datetime import datetime

# Import shared types first to avoid circular imports
from ..agents.types import AgentType, AgentCoordinationStrategy, ConversationIntent

# Then import existing types from voice_agent
try:
    from voice_agent import (
        VoiceResponse, VoiceState, ConversationContext
    )
    from ..step_parser import ParsedStepsResponse
    HAS_IMPORTS = True
except ImportError:
    # Fallback definitions if imports fail
    class VoiceState(str, Enum):
        LISTENING = "listening"
        PROCESSING = "processing"
        RESPONDING = "responding"
    
    class ParsedStepsResponse(BaseModel):
        """Fallback ParsedStepsResponse"""
        pass
    
    class ConversationContext(BaseModel):
        """Fallback ConversationContext"""
        pass
    
    class VoiceResponse(BaseModel):
        """Fallback VoiceResponse"""
        pass
    
    HAS_IMPORTS = False

logger = logging.getLogger(__name__)

# ===============================================================================
# ENHANCED VISUAL CITATION MODELS
# ===============================================================================

class VisualCitationType(str, Enum):
    """Enhanced visual citation types with agent context"""
    IMAGE = "image"
    DIAGRAM = "diagram"
    VIDEO = "video"
    PDF_PAGE = "pdf_page"
    EQUIPMENT_SCHEMATIC = "equipment_schematic"
    PROCEDURE_FLOWCHART = "procedure_flowchart"
    SAFETY_POSTER = "safety_poster"
    MAINTENANCE_CHART = "maintenance_chart"
    TEMPERATURE_CHART = "temperature_chart"
    CLEANING_GUIDE = "cleaning_guide"

class VisualCitationSource(str, Enum):
    """Sources of visual citations"""
    RAGIE_EXTRACTION = "ragie_extraction"
    GRAPH_RAG_ENTITY = "graph_rag_entity"
    PDF_EXTRACTION = "pdf_extraction"
    MANUAL_REFERENCE = "manual_reference"
    AGENT_GENERATED = "agent_generated"

class EnhancedVisualCitation(BaseModel):
    """Enhanced visual citation model with agent context and relevance scoring"""
    
    # Core citation information
    citation_id: str
    type: VisualCitationType
    source: VisualCitationSource
    title: str
    description: Optional[str] = None
    
    # Content references
    content_url: Optional[str] = None
    pdf_url: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    
    # Agent context integration
    contributing_agent: AgentType
    agent_confidence: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    
    # QSR domain context
    equipment_context: List[str] = Field(default_factory=list)
    procedure_steps: List[str] = Field(default_factory=list)
    safety_level: Literal["low", "medium", "high", "critical"] = "low"
    maintenance_frequency: Optional[str] = None
    
    # Visual content metadata
    visual_metadata: Dict[str, Any] = Field(default_factory=dict)
    thumbnail_url: Optional[str] = None
    full_resolution_url: Optional[str] = None
    
    # Performance tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    user_feedback_score: Optional[float] = None
    
    @validator('relevance_score')
    def validate_relevance_score(cls, v, values):
        """Ensure relevance score aligns with agent confidence"""
        agent_confidence = values.get('agent_confidence', 0.5)
        if abs(v - agent_confidence) > 0.3:
            logger.warning(f"Large discrepancy between relevance ({v}) and agent confidence ({agent_confidence})")
        return v
    
    def increment_access(self):
        """Track citation usage for performance optimization"""
        self.access_count += 1
        self.last_accessed = datetime.now()

class VisualCitationCollection(BaseModel):
    """Collection of visual citations with coordination metadata"""
    
    citations: List[EnhancedVisualCitation] = Field(default_factory=list)
    primary_citation: Optional[str] = None  # citation_id of primary citation
    total_relevance_score: float = 0.0
    coordination_strategy: AgentCoordinationStrategy = AgentCoordinationStrategy.SINGLE_AGENT
    
    # Collection-level metadata
    equipment_focus: List[str] = Field(default_factory=list)
    safety_critical: bool = False
    procedure_complete: bool = False
    
    @model_validator(mode='after')
    def calculate_total_relevance(self):
        """Calculate total relevance score from individual citations"""
        if self.citations:
            self.total_relevance_score = sum(c.relevance_score for c in self.citations) / len(self.citations)
        return self
    
    def get_by_type(self, citation_type: VisualCitationType) -> List[EnhancedVisualCitation]:
        """Get citations filtered by type"""
        return [c for c in self.citations if c.type == citation_type]
    
    def get_safety_critical(self) -> List[EnhancedVisualCitation]:
        """Get safety-critical citations"""
        return [c for c in self.citations if c.safety_level in ["high", "critical"]]

# ===============================================================================
# ENHANCED EQUIPMENT CONTEXT MODELS
# ===============================================================================

class EquipmentStatus(str, Enum):
    """Equipment operational status"""
    OPERATIONAL = "operational"
    MAINTENANCE_REQUIRED = "maintenance_required"
    OUT_OF_ORDER = "out_of_order"
    CLEANING_IN_PROGRESS = "cleaning_in_progress"
    UNKNOWN = "unknown"

class EquipmentContext(BaseModel):
    """Enhanced equipment context with Graph-RAG integration"""
    
    # Core equipment information (from Graph-RAG entities)
    equipment_id: str
    equipment_name: str
    equipment_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    
    # Operational context
    current_status: EquipmentStatus = EquipmentStatus.UNKNOWN
    last_maintenance: Optional[datetime] = None
    next_maintenance_due: Optional[datetime] = None
    
    # Graph-RAG relationships
    related_procedures: List[str] = Field(default_factory=list)
    safety_protocols: List[str] = Field(default_factory=list)
    maintenance_tasks: List[str] = Field(default_factory=list)
    
    # Visual content associations
    associated_citations: List[str] = Field(default_factory=list)  # citation_ids
    schematic_available: bool = False
    manual_sections: List[str] = Field(default_factory=list)
    
    # Performance tracking
    usage_frequency: float = 0.0
    common_issues: List[str] = Field(default_factory=list)
    resolution_time_avg: Optional[float] = None

class ConversationEquipmentHistory(BaseModel):
    """Enhanced conversation equipment tracking"""
    
    equipment_timeline: List[EquipmentContext] = Field(default_factory=list)
    current_equipment: Optional[str] = None
    equipment_switches: int = 0
    total_equipment_mentioned: int = 0
    
    # Conversation patterns
    preferred_equipment: Optional[str] = None
    expertise_indicators: Dict[str, float] = Field(default_factory=dict)
    recurring_issues: List[str] = Field(default_factory=list)

# ===============================================================================
# ENHANCED RESPONSE MODELS
# ===============================================================================

class QSRResponseMetadata(BaseModel):
    """Metadata for QSR response quality and performance"""
    
    # Response quality indicators
    completeness_score: float = Field(ge=0.0, le=1.0, default=0.8)
    accuracy_confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    safety_compliance: bool = True
    procedure_completeness: bool = True
    
    # Performance metrics
    generation_time_ms: Optional[float] = None
    agent_processing_time: Dict[str, float] = Field(default_factory=dict)
    citation_retrieval_time: Optional[float] = None
    
    # Content analysis
    equipment_coverage: List[str] = Field(default_factory=list)
    procedure_steps_covered: int = 0
    safety_warnings_included: int = 0
    
    # User experience indicators
    expected_follow_up_likelihood: float = Field(ge=0.0, le=1.0, default=0.5)
    hands_free_optimization: bool = True
    cognitive_load_score: Literal["low", "medium", "high"] = "medium"

class EnhancedQSRResponse(BaseModel):
    """
    Enhanced QSR response that extends VoiceResponse with advanced visual integration
    and multi-agent coordination.
    """
    
    # ===== CORE RESPONSE (from VoiceResponse) =====
    text_response: str
    audio_data: Optional[str] = None
    should_continue_listening: bool = True
    next_voice_state: VoiceState = VoiceState.LISTENING
    detected_intent: ConversationIntent
    context_updates: Dict[str, Any] = Field(default_factory=dict)
    conversation_complete: bool = False
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)
    suggested_follow_ups: List[str] = Field(default_factory=list)
    
    # ===== ENHANCED VISUAL INTEGRATION =====
    visual_citations: VisualCitationCollection = Field(default_factory=VisualCitationCollection)
    primary_visual_focus: Optional[VisualCitationType] = None
    visual_complexity: Literal["simple", "moderate", "complex"] = "simple"
    
    # ===== MULTI-AGENT COORDINATION =====
    primary_agent: AgentType = AgentType.GENERAL
    contributing_agents: List[AgentType] = Field(default_factory=list)
    coordination_strategy: AgentCoordinationStrategy = AgentCoordinationStrategy.SINGLE_AGENT
    agent_confidence_scores: Dict[str, float] = Field(default_factory=dict)
    specialized_insights: Dict[str, Any] = Field(default_factory=dict)
    
    # ===== EQUIPMENT & PROCEDURE CONTEXT =====
    equipment_context: Optional[EquipmentContext] = None
    procedure_step_info: Optional[Dict[str, Any]] = None
    workflow_phase: Optional[str] = None
    parsed_steps: Optional[ParsedStepsResponse] = None
    
    # ===== SAFETY & COMPLIANCE =====
    safety_priority: bool = False
    safety_warnings: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    temperature_requirements: Optional[Dict[str, Any]] = None
    
    # ===== RESPONSE METADATA & PERFORMANCE =====
    response_metadata: QSRResponseMetadata = Field(default_factory=QSRResponseMetadata)
    response_type: Literal["procedural", "factual", "clarification", "safety", "completion"] = "factual"
    
    # ===== USER EXPERIENCE =====
    hands_free_recommendation: bool = True
    response_length_category: Literal["brief", "standard", "detailed"] = "standard"
    cognitive_complexity: Literal["simple", "moderate", "complex"] = "simple"
    
    @validator('visual_citations')
    def validate_visual_citations(cls, v, values):
        """Ensure visual citations align with response content"""
        if v.safety_critical and not values.get('safety_priority', False):
            logger.warning("Safety-critical visual citations without safety priority flag")
        return v
    
    @model_validator(mode='after')
    def ensure_response_coherence(self):
        """Ensure all response components are coherent"""
        
        # Align visual complexity with cognitive complexity
        visual_complexity = self.visual_complexity
        cognitive_complexity = self.cognitive_complexity
        
        complexity_map = {"simple": 1, "moderate": 2, "complex": 3}
        if abs(complexity_map[visual_complexity] - complexity_map[cognitive_complexity]) > 1:
            logger.warning("Visual and cognitive complexity misalignment")
        
        # Ensure safety priority consistency
        safety_priority = self.safety_priority
        safety_warnings = self.safety_warnings
        
        if safety_priority and not safety_warnings:
            logger.warning("Safety priority set but no safety warnings provided")
        
        return self
    
    def to_voice_response(self) -> 'VoiceResponse':
        """Convert to legacy VoiceResponse for backward compatibility"""
        try:
            from voice_agent import VoiceResponse
            
            # Convert visual citations to legacy format
            legacy_citations = []
            for citation in self.visual_citations.citations:
                legacy_citations.append({
                    "citation_id": citation.citation_id,
                    "type": citation.type.value,
                    "source": citation.title,
                    "confidence": citation.agent_confidence,
                    "description": citation.description,
                    "page": citation.page_number,
                    "equipment_type": citation.equipment_context[0] if citation.equipment_context else None
                })
            
            return VoiceResponse(
                text_response=self.text_response,
                audio_data=self.audio_data,
                should_continue_listening=self.should_continue_listening,
                next_voice_state=self.next_voice_state,
                detected_intent=self.detected_intent,
                context_updates=self.context_updates,
                conversation_complete=self.conversation_complete,
                confidence_score=self.confidence_score,
                suggested_follow_ups=self.suggested_follow_ups,
                equipment_mentioned=self.equipment_context.equipment_name if self.equipment_context else None,
                safety_priority=self.safety_priority,
                response_type=self.response_type,
                hands_free_recommendation=self.hands_free_recommendation,
                primary_agent=self.primary_agent,
                contributing_agents=self.contributing_agents,
                coordination_strategy=self.coordination_strategy,
                agent_confidence_scores=self.agent_confidence_scores,
                specialized_insights=self.specialized_insights,
                parsed_steps=self.parsed_steps
            )
        except ImportError:
            logger.error("Cannot import VoiceResponse for backward compatibility")
            return None

# ===============================================================================
# SPECIALIZED AGENT RESPONSE MODELS
# ===============================================================================

class EquipmentResponse(EnhancedQSRResponse):
    """Equipment-specific response with technical details and schematics"""
    
    # Equipment-specific fields
    technical_specifications: Dict[str, Any] = Field(default_factory=dict)
    troubleshooting_steps: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    
    # Visual focus for equipment
    schematic_references: List[str] = Field(default_factory=list)
    parts_diagram_available: bool = False
    
    # Performance and maintenance
    maintenance_schedule: Optional[Dict[str, Any]] = None
    performance_indicators: Dict[str, float] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "text_response": "The fryer temperature should be set to 350°F for optimal cooking...",
                "primary_agent": "equipment",
                "equipment_context": {
                    "equipment_name": "Taylor C602 Fryer",
                    "equipment_type": "fryer",
                    "current_status": "operational"
                },
                "technical_specifications": {
                    "max_temperature": "375°F",
                    "oil_capacity": "50 lbs",
                    "power_requirements": "240V"
                }
            }
        }

class ProcedureResponse(EnhancedQSRResponse):
    """Procedure-specific response with step-by-step instructions and visual guides"""
    
    # Procedure-specific fields
    procedure_title: str
    step_count: int
    estimated_duration: Optional[str] = None
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    
    # Step details
    detailed_steps: List[Dict[str, Any]] = Field(default_factory=list)
    verification_checkpoints: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    
    # Visual workflow
    workflow_diagram_available: bool = False
    step_illustrations: List[str] = Field(default_factory=list)
    
    # Quality control
    quality_standards: List[str] = Field(default_factory=list)
    success_indicators: List[str] = Field(default_factory=list)

class SafetyResponse(EnhancedQSRResponse):
    """Safety-specific response with critical safety information and compliance requirements"""
    
    # Safety-specific fields (overrides)
    safety_priority: bool = True  # Always true for SafetyResponse
    
    # Critical safety information
    immediate_actions: List[str] = Field(default_factory=list)
    hazard_warnings: List[str] = Field(default_factory=list)
    protective_equipment: List[str] = Field(default_factory=list)
    
    # Compliance and regulations
    regulatory_references: List[str] = Field(default_factory=list)
    temperature_critical_points: Dict[str, float] = Field(default_factory=dict)
    haccp_considerations: List[str] = Field(default_factory=list)
    
    # Emergency procedures
    emergency_contacts: List[str] = Field(default_factory=list)
    escalation_procedures: List[str] = Field(default_factory=list)
    
    @validator('safety_priority')
    def ensure_safety_priority(cls, v):
        """Safety responses must have safety priority"""
        return True

class MaintenanceResponse(EnhancedQSRResponse):
    """Maintenance-specific response with cleaning protocols and schedules"""
    
    # Maintenance-specific fields
    maintenance_type: Literal["daily", "weekly", "monthly", "deep_clean", "repair"] = "daily"
    estimated_time: Optional[str] = None
    required_supplies: List[str] = Field(default_factory=list)
    
    # Cleaning protocols
    cleaning_steps: List[Dict[str, Any]] = Field(default_factory=list)
    chemical_requirements: List[str] = Field(default_factory=list)
    safety_precautions: List[str] = Field(default_factory=list)
    
    # Schedule and tracking
    frequency_recommendation: str = "daily"
    last_completed: Optional[datetime] = None
    next_due: Optional[datetime] = None
    
    # Verification
    inspection_checklist: List[str] = Field(default_factory=list)
    completion_verification: List[str] = Field(default_factory=list)

# ===============================================================================
# PERFORMANCE AND VALIDATION MODELS
# ===============================================================================

class ResponseQualityMetrics(BaseModel):
    """Comprehensive response quality assessment"""
    
    # Content quality
    information_completeness: float = Field(ge=0.0, le=1.0)
    accuracy_confidence: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    
    # User experience
    clarity_score: float = Field(ge=0.0, le=1.0)
    actionability_score: float = Field(ge=0.0, le=1.0)
    safety_compliance_score: float = Field(ge=0.0, le=1.0, default=1.0)
    
    # Technical metrics
    response_time_ms: float
    visual_citation_count: int
    agent_coordination_efficiency: float = Field(ge=0.0, le=1.0)
    
    # Overall assessment
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    
    @model_validator(mode='after')
    def calculate_overall_score(self):
        """Calculate overall quality score from component metrics"""
        components = [
            self.information_completeness or 0.8,
            self.accuracy_confidence or 0.8,
            self.relevance_score or 0.8,
            self.clarity_score or 0.8,
            self.actionability_score or 0.8,
            self.safety_compliance_score or 1.0
        ]
        self.overall_quality_score = sum(components) / len(components)
        return self

class AgentPerformanceTracker(BaseModel):
    """Track individual agent performance for optimization"""
    
    agent_type: AgentType
    total_queries_handled: int = 0
    average_confidence: float = 0.0
    average_response_time: float = 0.0
    
    # Success metrics
    successful_responses: int = 0
    user_satisfaction_score: Optional[float] = None
    safety_compliance_rate: float = 1.0
    
    # Performance trends
    recent_performance_scores: List[float] = Field(default_factory=list, max_items=50)
    optimization_opportunities: List[str] = Field(default_factory=list)
    
    def update_performance(self, quality_score: float, response_time: float):
        """Update performance metrics with new data"""
        self.total_queries_handled += 1
        self.recent_performance_scores.append(quality_score)
        
        # Update averages
        self.average_confidence = sum(self.recent_performance_scores) / len(self.recent_performance_scores)
        self.average_response_time = (self.average_response_time * (self.total_queries_handled - 1) + response_time) / self.total_queries_handled

# ===============================================================================
# RESPONSE FACTORY AND UTILITIES
# ===============================================================================

class QSRResponseFactory:
    """Factory for creating appropriate QSR response types"""
    
    @staticmethod
    def create_response(
        agent_type: AgentType,
        base_response_data: Dict[str, Any],
        visual_citations: List[EnhancedVisualCitation] = None,
        equipment_context: EquipmentContext = None
    ) -> EnhancedQSRResponse:
        """Create appropriate response type based on agent"""
        
        # Prepare visual citation collection
        citation_collection = VisualCitationCollection()
        if visual_citations:
            citation_collection.citations = visual_citations
            citation_collection.safety_critical = any(c.safety_level in ["high", "critical"] for c in visual_citations)
        
        # Common fields
        common_fields = {
            **base_response_data,
            "visual_citations": citation_collection,
            "equipment_context": equipment_context,
            "primary_agent": agent_type
        }
        
        # Create specialized response based on agent type
        if agent_type == AgentType.EQUIPMENT:
            return EquipmentResponse(**common_fields)
        elif agent_type == AgentType.PROCEDURE:
            return ProcedureResponse(**common_fields)
        elif agent_type == AgentType.SAFETY:
            return SafetyResponse(**common_fields)
        elif agent_type == AgentType.MAINTENANCE:
            return MaintenanceResponse(**common_fields)
        else:
            return EnhancedQSRResponse(**common_fields)

# ===============================================================================
# ENHANCED CONVERSATION CONTEXT
# ===============================================================================

class EnhancedConversationContext(ConversationContext):
    """Enhanced conversation context with multi-agent and visual citation tracking"""
    
    # Visual citation history
    visual_citation_history: List[str] = Field(default_factory=list)  # citation_ids
    most_accessed_citations: Dict[str, int] = Field(default_factory=dict)
    
    # Equipment context enhancement
    equipment_history: ConversationEquipmentHistory = Field(default_factory=ConversationEquipmentHistory)
    equipment_expertise_indicators: Dict[str, float] = Field(default_factory=dict)
    
    # Multi-agent tracking
    agent_usage_history: Dict[str, int] = Field(default_factory=dict)
    preferred_coordination_strategy: AgentCoordinationStrategy = AgentCoordinationStrategy.SINGLE_AGENT
    
    # Performance optimization
    response_quality_trend: List[float] = Field(default_factory=list, max_items=20)
    user_satisfaction_indicators: Dict[str, float] = Field(default_factory=dict)
    
    def update_agent_usage(self, agent_type: AgentType):
        """Track agent usage for optimization"""
        agent_key = agent_type.value
        self.agent_usage_history[agent_key] = self.agent_usage_history.get(agent_key, 0) + 1
    
    def add_visual_citation_access(self, citation_id: str):
        """Track visual citation access for relevance optimization"""
        self.visual_citation_history.append(citation_id)
        self.most_accessed_citations[citation_id] = self.most_accessed_citations.get(citation_id, 0) + 1
    
    def get_preferred_agent(self) -> AgentType:
        """Determine preferred agent based on usage history"""
        if not self.agent_usage_history:
            return AgentType.GENERAL
        
        most_used = max(self.agent_usage_history.items(), key=lambda x: x[1])
        return AgentType(most_used[0])

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Enhanced response models
    "EnhancedQSRResponse",
    "EquipmentResponse", 
    "ProcedureResponse",
    "SafetyResponse",
    "MaintenanceResponse",
    
    # Visual citation models
    "EnhancedVisualCitation",
    "VisualCitationCollection",
    "VisualCitationType",
    "VisualCitationSource",
    
    # Equipment and context models
    "EquipmentContext",
    "ConversationEquipmentHistory",
    "EnhancedConversationContext",
    
    # Performance and validation
    "ResponseQualityMetrics",
    "AgentPerformanceTracker", 
    "QSRResponseMetadata",
    
    # Utilities
    "QSRResponseFactory"
]