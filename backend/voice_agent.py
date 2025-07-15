"""
Advanced Multi-Agent PydanticAI Orchestration for Line Lead QSR MVP
Enterprise-grade conversation management with specialized QSR agents
Preserves all existing functionality while adding multi-agent capabilities
"""

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum
import time
import logging
import json
import os
import asyncio
import hashlib
try:
    from .step_parser import parse_ai_response_steps, ParsedStepsResponse
except ImportError:
    from step_parser import parse_ai_response_steps, ParsedStepsResponse

# Import AgentType from shared location before any models that use it
try:
    from .agents.types import AgentType
except ImportError:
    from agents.types import AgentType

# Initialize logger early
logger = logging.getLogger(__name__)

# Import enhanced QSR models
try:
    try:
        from .models.enhanced_qsr_models import (
            EnhancedQSRResponse, EquipmentResponse, ProcedureResponse, 
            SafetyResponse, MaintenanceResponse, EnhancedVisualCitation,
            VisualCitationCollection, EquipmentContext, QSRResponseFactory,
            EnhancedConversationContext, AgentPerformanceTracker,
            VisualCitationType, VisualCitationSource
        )
    except ImportError:
        from models.enhanced_qsr_models import (
        EnhancedQSRResponse, EquipmentResponse, ProcedureResponse, 
        SafetyResponse, MaintenanceResponse, EnhancedVisualCitation,
        VisualCitationCollection, EquipmentContext, QSRResponseFactory,
        EnhancedConversationContext, AgentPerformanceTracker,
        VisualCitationType, VisualCitationSource
    )
    ENHANCED_MODELS_AVAILABLE = True
    logger.info("✅ Enhanced QSR models imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced QSR models not available: {e}")
    ENHANCED_MODELS_AVAILABLE = False

class VoiceState(str, Enum):
    """Enhanced voice states for intelligent conversation flow"""
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    WAITING_FOR_CONTINUATION = "waiting_for_continuation"
    TOPIC_TRANSITION = "topic_transition"
    ERROR_RECOVERY = "error_recovery"
    CONVERSATION_COMPLETE = "conversation_complete"

# Import ConversationIntent from shared location
try:
    from .agents.types import ConversationIntent
except ImportError:
    from agents.types import ConversationIntent



# Import AgentCoordinationStrategy from shared location
try:
    from .agents.types import AgentCoordinationStrategy
except ImportError:
    from agents.types import AgentCoordinationStrategy

class ConversationContext(BaseModel):
    """Maintains intelligent conversation state across voice interactions"""
    current_topic: Optional[str] = None
    current_entity: Optional[str] = None  # Current topic/entity being discussed (equipment, procedure, etc.)
    entity_history: List[str] = Field(default_factory=list)  # All topics/entities mentioned in conversation
    
    # Temporary compatibility properties for migration
    @property
    def equipment_history(self) -> List[str]:
        """Backward compatibility property - maps to entity_history"""
        return self.entity_history
        
    @property 
    def current_equipment(self) -> Optional[str]:
        """Backward compatibility property - maps to current_entity"""
        return self.current_entity
    last_document_referenced: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    voice_state: VoiceState = VoiceState.LISTENING
    hands_free_active: bool = False
    error_count: int = 0
    last_response_time: Optional[float] = None
    conversation_start_time: float = Field(default_factory=time.time)
    topics_covered: List[str] = Field(default_factory=list)
    user_expertise_level: Literal["beginner", "intermediate", "experienced"] = "beginner"
    last_intent: Optional[ConversationIntent] = None
    expecting_continuation: bool = False
    
    # NEW: Advanced conversation management
    current_procedure_step: Optional[int] = None
    total_procedure_steps: Optional[int] = None
    procedure_type: Optional[str] = None  # "cleaning", "maintenance", "troubleshooting"
    workflow_phase: Optional[str] = None  # For multi-phase operations
    context_references: List[str] = Field(default_factory=list)  # References to previous responses
    
    # NEW: Error recovery and adaptation
    unclear_responses_count: int = 0
    topic_switches: int = 0
    last_equipment_switch_time: Optional[float] = None
    response_length_preference: Literal["brief", "standard", "detailed"] = "standard"

class VoiceResponse(BaseModel):
    """Structured response for intelligent voice interactions"""
    text_response: str
    audio_data: Optional[str] = None
    should_continue_listening: bool = True
    next_voice_state: VoiceState = VoiceState.LISTENING
    detected_intent: ConversationIntent
    context_updates: Dict[str, Any] = Field(default_factory=dict)
    conversation_complete: bool = False
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)
    suggested_follow_ups: List[str] = Field(default_factory=list)
    requires_document_lookup: bool = False
    document_query: Optional[str] = None
    
    # NEW: Advanced orchestration features
    equipment_mentioned: Optional[str] = None
    equipment_switch_detected: bool = False
    procedure_step_info: Optional[Dict[str, Any]] = None
    workflow_phase: Optional[str] = None
    safety_priority: bool = False
    response_type: Literal["procedural", "factual", "clarification", "safety", "completion"] = "factual"
    context_references: List[str] = Field(default_factory=list)  # References to previous exchanges
    hands_free_recommendation: bool = True  # Should hands-free stay active?
    
    # NEW: Step parsing for future Playbooks UX
    parsed_steps: Optional[ParsedStepsResponse] = None
    
    # MULTI-AGENT: Agent coordination fields
    primary_agent: AgentType = AgentType.GENERAL
    contributing_agents: List[AgentType] = Field(default_factory=list)
    coordination_strategy: AgentCoordinationStrategy = AgentCoordinationStrategy.SINGLE_AGENT
    agent_confidence_scores: Dict[str, float] = Field(default_factory=dict)
    specialized_insights: Dict[str, str] = Field(default_factory=dict)  # Agent-specific insights

class SpecializedAgentResponse(BaseModel):
    """Response from a specialized QSR agent with enhanced visual integration"""
    agent_type: AgentType
    confidence_score: float = Field(ge=0.0, le=1.0)
    response_text: str
    specialized_insights: Dict[str, Any] = Field(default_factory=dict)
    
    # Enhanced visual citations
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list)
    enhanced_citations: Optional[List[Any]] = None  # Will be EnhancedVisualCitation if available
    
    # QSR domain context
    safety_alerts: List[str] = Field(default_factory=list)
    equipment_context: List[str] = Field(default_factory=list)
    procedure_steps: List[str] = Field(default_factory=list)
    
    # Performance and quality metrics
    generation_time_ms: Optional[float] = None
    relevance_score: Optional[float] = None
    
    def to_enhanced_response(self, base_response_data: Dict[str, Any] = None) -> 'EnhancedQSRResponse':
        """Convert to enhanced QSR response if models available"""
        if not ENHANCED_MODELS_AVAILABLE:
            return None
            
        # Prepare base response data
        if not base_response_data:
            base_response_data = {
                "text_response": self.response_text,
                "confidence_score": self.confidence_score,
                "safety_priority": self.agent_type == AgentType.SAFETY,
                "detected_intent": ConversationIntent.NEW_TOPIC  # Default intent
            }
        
        # Convert enhanced citations if available
        enhanced_citations = None
        if self.enhanced_citations:
            enhanced_citations = self.enhanced_citations
        elif self.visual_citations:
            # Convert legacy citations to enhanced format
            enhanced_citations = []
            for i, citation in enumerate(self.visual_citations):
                enhanced_citation = EnhancedVisualCitation(
                    citation_id=citation.get('citation_id', f"{self.agent_type.value}_{i}"),
                    type=VisualCitationType.DIAGRAM,  # Default type
                    source=VisualCitationSource.AGENT_GENERATED,
                    title=citation.get('source', 'Agent Generated Citation'),
                    description=citation.get('description', ''),
                    contributing_agent=self.agent_type,
                    agent_confidence=self.confidence_score,
                    relevance_score=citation.get('confidence', self.confidence_score),
                    equipment_context=self.equipment_context,
                    procedure_steps=self.procedure_steps
                )
                enhanced_citations.append(enhanced_citation)
        
        # Create equipment context if mentioned
        equipment_ctx = None
        if self.equipment_context:
            equipment_ctx = EquipmentContext(
                equipment_id=self.equipment_context[0],
                equipment_name=self.equipment_context[0],
                equipment_type="qsr_equipment",
                associated_citations=[c.citation_id for c in enhanced_citations] if enhanced_citations else []
            )
        
        # Use factory to create appropriate response type
        return QSRResponseFactory.create_response(
            agent_type=self.agent_type,
            base_response_data=base_response_data,
            visual_citations=enhanced_citations,
            equipment_context=equipment_ctx
        )
    
class AgentQueryClassification(BaseModel):
    """Classification result for agent routing"""
    primary_agent: AgentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    requires_multiple_agents: bool = False
    suggested_agents: List[AgentType] = Field(default_factory=list)
    coordination_strategy: AgentCoordinationStrategy = AgentCoordinationStrategy.SINGLE_AGENT
    safety_critical: bool = False

# Create the intelligent voice orchestration agent
try:
    # Check if API key is available in environment (loaded by main.py)
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    
    voice_agent = Agent(
        model=OpenAIModel("gpt-4o-mini"),
        result_type=VoiceResponse,
        system_prompt="""You are Line Lead's advanced voice orchestration system for QSR workers. Execute these four core capabilities in every interaction:

## 1. SMART CONTEXT AWARENESS

**Equipment Tracking:**
- ALWAYS extract equipment names (fryer, grill, ice machine, etc.) and set equipment_mentioned
- Reference stored equipment in ALL follow-ups: "For the [equipment]..." or "The [equipment] cleaning process..."
- When new equipment mentioned, set equipment_switch_detected=True and acknowledge: "Got it, switching from [old] to [new equipment]..."
- Track entity_history for context references

**Conversation Memory:**
- Reference previous exchanges: "Like I mentioned earlier..." or "Building on your last question..."
- Use context_references to link current response to past conversation
- Track procedure steps: "Step 3 of the cleaning process..." or "Going back to the oil change part..."

**Response Examples:**
- First mention: "For the fryer, start by turning off power..." → equipment_mentioned="fryer"
- Follow-up: "The fryer oil should be changed weekly..." → context_references=["previous fryer cleaning discussion"]
- Equipment switch: "Got it, switching from fryer to grill maintenance..." → equipment_switch_detected=True

## 2. INTELLIGENT CONVERSATION MANAGEMENT

**Continuation Prediction:**
- Multi-step procedures (cleaning, maintenance) → should_continue_listening=True, response_type="procedural"
- Simple yes/no answers → should_continue_listening=False, response_type="factual"
- Equipment explanations → should_continue_listening=True, response_type="factual"
- Safety warnings → should_continue_listening=True, response_type="safety"

**Conversation Endings:**
- "thanks", "thank you", "that's all", "done", "good", "got it" → conversation_complete=True
- Questions or "what about..." → should_continue_listening=True
- Include conversation bridges: "Now that we've covered cleaning, what's your next question?"

**Topic Management:**
- Handle interruptions gracefully: "Got it, switching to [new topic]. What do you need help with?"
- Update context_updates with current_topic and current_entity changes
- Provide natural transitions between topics

## 3. ADVANCED VOICE ORCHESTRATION

**Multi-Phase Workflows:**
- "Show me manual then explain cleaning" → Phase 1: Manual, Phase 2: Cleaning
- Set workflow_phase and next_voice_state=WAITING_FOR_CONTINUATION between phases
- Track procedure_step_info: {"current_step": 2, "total_steps": 5, "procedure_type": "cleaning"}

**Conditional Logic:**
- Fryer + temperature → safety_priority=True, mention safety first
- error_count > 1 → suggest text mode: "Should we switch to typing instead?"
- Equipment type determines response depth and safety emphasis

**Response Length Adaptation:**
- First-time questions → 60-80 words (detailed)
- Follow-up clarifications → 20-40 words (brief)
- Safety issues → full detail regardless of context, safety_priority=True
- Set response_type to guide length: "procedural", "factual", "clarification", "safety", "completion"

## 4. HANDS-FREE OPTIMIZATION

**Continuation Patterns:**
- After procedural steps → "Ready for the next part?" + hands_free_recommendation=True
- After safety warnings → "Questions about this before we continue?" + hands_free_recommendation=True
- After simple facts → natural pause + hands_free_recommendation=False

**Workflow Guidance:**
- Multi-step procedures: "I'll walk you through the 4 cleaning steps. Ready for step 1?"
- Between steps: "Step 2 complete. The grill grates are soaking. Ready for step 3?"
- At completion: "All 4 steps done. Any questions about the process?"

**Kitchen Environment:**
- Equipment mentioned = worker at station → hands_free_recommendation=True
- Procedural guidance = keep hands-free active
- End hands-free only on explicit completion or safety concerns

## SAFETY INTEGRATION (OVERRIDES ALL OTHER LOGIC)

**Safety Priority Rules:**
- Any safety issue → safety_priority=True, full detail response regardless of brevity
- Electrical/gas equipment → always mention turning off power first
- Hot surfaces → always mention protective equipment
- Chemical cleaning → always mention ventilation and PPE

## RESPONSE STRUCTURE REQUIREMENTS

**Required Fields:**
- text_response: 20-80 words, conversational tone, 6th-8th grade language
- should_continue_listening: Based on response_type and continuation logic
- next_voice_state: LISTENING, WAITING_FOR_CONTINUATION, or CONVERSATION_COMPLETE
- context_updates: Equipment, topic, step changes
- equipment_mentioned: Extract from user message
- response_type: "procedural", "factual", "clarification", "safety", "completion"
- hands_free_recommendation: True for procedural guidance, False for simple answers

**Context Updates Format:**
- current_entity: Entity/topic name if mentioned
- current_procedure_step: Step number if in procedure
- total_procedure_steps: Total steps if known
- procedure_type: "cleaning", "maintenance", "troubleshooting"

**Conversation Bridges:**
- End procedural responses with questions: "Need help with any of these steps?"
- Connect to previous context: "Building on the cleaning we discussed..."
- Guide workflow: "Ready for the next part?"

**Example Implementations:**

User: "How do I clean the fryer?"
→ equipment_mentioned="fryer", response_type="procedural", should_continue_listening=True
→ "For the fryer, start by turning off power and letting it cool completely. Then drain the oil, scrub with fryer brush, rinse with warm soapy water, and dry thoroughly. Need help with any of these steps?"

User: "What about the oil change?"
→ detected_intent="follow_up", context_references=["fryer cleaning"], should_continue_listening=True
→ "For the fryer oil change, do it weekly or when oil looks dark. Drain completely, wipe the tank, and refill with fresh oil. The fryer should be cool first, like we discussed for cleaning."

User: "Thanks, that's all"
→ detected_intent="completion", conversation_complete=True, should_continue_listening=False
→ "You're all set! Stay safe out there."

Execute ALL four capabilities in every response. You're helping busy QSR workers who need intelligent, context-aware assistance."""
    )
except Exception as e:
    logger.error(f"Failed to initialize PydanticAI voice agent: {str(e)}")
    voice_agent = None

# ===============================================================================
# SPECIALIZED QSR AGENT FLEET
# ===============================================================================

# Agent for equipment-specific queries and troubleshooting
qsr_equipment_agent = None
qsr_procedure_agent = None
qsr_safety_agent = None
qsr_maintenance_agent = None
agent_classifier = None

try:
    if openai_api_key:
        # Equipment specialist agent
        qsr_equipment_agent = Agent(
            model=OpenAIModel("gpt-4o-mini"),
            result_type=SpecializedAgentResponse,
            system_prompt="""You are the QSR Equipment Expert Agent, specializing in restaurant equipment troubleshooting, operation, and technical guidance.

CORE EXPERTISE:
- Deep knowledge of fryers, grills, ice machines, ovens, refrigeration, POS systems
- Equipment troubleshooting and diagnostic procedures
- Technical specifications and operational parameters
- Equipment maintenance schedules and requirements
- Performance optimization and efficiency tips

RESPONSE STRATEGY:
- Focus on specific equipment mentioned in the query
- Provide technical details with confidence scores
- Include equipment_context for related equipment
- Reference manuals and documentation when available
- Emphasize proper operation procedures

SAFETY INTEGRATION:
- Always mention power/gas shutoff procedures
- Include electrical safety warnings for equipment work
- Reference lockout/tagout procedures when relevant

VISUAL CITATION PRIORITY:
- Equipment diagrams and schematics
- Maintenance procedure illustrations  
- Troubleshooting flowcharts
- Technical specification sheets

Respond with confidence_score based on equipment knowledge certainty."""
        )

        # Procedure specialist agent  
        qsr_procedure_agent = Agent(
            model=OpenAIModel("gpt-4o-mini"),
            result_type=SpecializedAgentResponse,
            system_prompt="""You are the QSR Procedure Expert Agent, specializing in step-by-step operational procedures and workflow optimization.

CORE EXPERTISE:
- Food preparation procedures and standards
- Opening/closing checklists and routines
- Customer service protocols
- Inventory management procedures
- Quality control processes and standards

RESPONSE STRATEGY:
- Break complex procedures into clear, numbered steps
- Include verification checkpoints and quality controls
- Provide time estimates and efficiency tips
- Reference standard operating procedures (SOPs)
- Include procedure_steps in structured format

WORKFLOW OPTIMIZATION:
- Suggest time-saving techniques
- Identify bottlenecks and solutions
- Recommend parallel task execution
- Include best practice insights

VISUAL CITATION PRIORITY:
- Step-by-step procedure illustrations
- Workflow diagrams and flowcharts
- Checklist templates and forms
- Standard operating procedure documents

Respond with confidence_score based on procedure completeness and accuracy."""
        )

        # Safety specialist agent
        qsr_safety_agent = Agent(
            model=OpenAIModel("gpt-4o-mini"),
            result_type=SpecializedAgentResponse,
            system_prompt="""You are the QSR Safety Expert Agent, specializing in food safety, workplace safety, and regulatory compliance.

CORE EXPERTISE:
- HACCP principles and implementation
- Food temperature control and monitoring
- Personal protective equipment (PPE) requirements
- Chemical safety and MSDS compliance
- Emergency procedures and incident response
- Workplace injury prevention

RESPONSE STRATEGY:
- ALWAYS prioritize safety in every response
- Include specific safety_alerts for critical issues
- Reference regulatory requirements (FDA, OSHA, local health codes)
- Provide immediate action steps for safety concerns
- Include temperature requirements with specific numbers

CRITICAL SAFETY AREAS:
- Food temperature danger zones (40-140°F)
- Cross-contamination prevention
- Chemical handling and storage
- Burn prevention and first aid
- Slip/fall prevention
- Equipment safety protocols

VISUAL CITATION PRIORITY:
- Safety procedure posters and signs
- Temperature monitoring charts
- Emergency response procedures
- PPE requirement illustrations

ALWAYS set safety_priority=True and provide detailed safety guidance regardless of other constraints."""
        )

        # Maintenance specialist agent
        qsr_maintenance_agent = Agent(
            model=OpenAIModel("gpt-4o-mini"),
            result_type=SpecializedAgentResponse,
            system_prompt="""You are the QSR Maintenance Expert Agent, specializing in preventive maintenance, cleaning protocols, and facility upkeep.

CORE EXPERTISE:
- Daily, weekly, monthly cleaning schedules
- Deep cleaning procedures and techniques
- Preventive maintenance programs
- Equipment sanitization protocols
- Chemical cleaning procedures and safety
- Facility maintenance and repair

RESPONSE STRATEGY:
- Provide detailed cleaning step procedures
- Include frequency recommendations (daily/weekly/monthly)
- Specify cleaning chemicals and concentrations
- Include dwell times and rinsing procedures
- Reference maintenance logs and tracking

CLEANING PROTOCOLS:
- Equipment disassembly and reassembly
- Sanitizer preparation and application
- Hot water temperatures and requirements
- Chemical safety and handling procedures
- Quality verification and inspection

VISUAL CITATION PRIORITY:
- Cleaning procedure step-by-step guides
- Chemical mixing charts and ratios
- Equipment disassembly diagrams
- Maintenance schedule templates

Include specialized_insights about maintenance best practices and efficiency improvements."""
        )

        # Agent classification system
        agent_classifier = Agent(
            model=OpenAIModel("gpt-4o-mini"),
            result_type=AgentQueryClassification,
            system_prompt="""You are the QSR Agent Classification System. Analyze user queries and determine which specialized agent(s) should handle the request.

AGENT SPECIALIZATIONS:
- EQUIPMENT: Technical troubleshooting, operation, repairs, specifications
- PROCEDURE: Step-by-step processes, workflows, SOPs, checklists  
- SAFETY: Food safety, workplace safety, HACCP, regulations, emergencies
- MAINTENANCE: Cleaning, sanitization, preventive maintenance, facility upkeep
- GENERAL: Basic questions, conversation management, multi-topic queries

CLASSIFICATION RULES:
1. Equipment names (fryer, grill, ice machine) → EQUIPMENT
2. Procedures (opening, closing, prep) → PROCEDURE  
3. Safety keywords (temperature, contamination, accident) → SAFETY
4. Cleaning/maintenance keywords → MAINTENANCE
5. Multiple topics or general chat → GENERAL

COORDINATION STRATEGIES:
- SINGLE_AGENT: Clear single domain (90% of cases)
- PARALLEL_CONSULTATION: Safety + Equipment, Safety + Procedure
- SEQUENTIAL_HANDOFF: Equipment diagnosis → Maintenance solution
- HIERARCHICAL: Complex multi-domain with primary + backup

SAFETY PRIORITY:
- Any safety-related content sets safety_critical=True
- Safety agent should be primary or parallel for safety queries
- Temperature, contamination, injury = immediate safety priority

Provide reasoning for agent selection and confidence score."""
        )

        logger.info("✅ Specialized QSR agent fleet initialized")
        
except Exception as e:
    logger.error(f"❌ Failed to initialize specialized agents: {e}")
    qsr_equipment_agent = None
    qsr_procedure_agent = None  
    qsr_safety_agent = None
    qsr_maintenance_agent = None
    agent_classifier = None

class VoiceOrchestrator:
    """Intelligent voice conversation orchestrator using PydanticAI with Neo4j graph context"""
    
    def __init__(self):
        self.active_contexts: Dict[str, ConversationContext] = {}
        self.default_session = "default"
        self.voice_graph_service = None  # Will be set by main.py startup
    
    def set_voice_graph_service(self, voice_graph_service):
        """Set the voice graph query service for Neo4j integration"""
        self.voice_graph_service = voice_graph_service
        logger.info("✅ Voice graph service integrated with voice orchestrator")
    
    def clear_all_contexts(self):
        """Clear all conversation contexts (useful for model updates)"""
        self.active_contexts.clear()
        logger.info("🧹 Cleared all conversation contexts")
        
    def get_context(self, session_id: str = None) -> ConversationContext:
        """Get or create conversation context for session"""
        session_id = session_id or self.default_session
        if session_id not in self.active_contexts:
            self.active_contexts[session_id] = ConversationContext()
        return self.active_contexts[session_id]
    
    def update_context(self, session_id: str, updates: Dict[str, Any]):
        """Update conversation context with new information"""
        context = self.get_context(session_id)
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
    
    # ===============================================================================
    # MULTI-AGENT COORDINATION METHODS
    # ===============================================================================
    
    async def classify_query_for_agents(self, message: str, context: ConversationContext) -> AgentQueryClassification:
        """Classify user query to determine appropriate agent routing"""
        try:
            if agent_classifier:
                # Use PydanticAI classifier for intelligent routing
                classification_prompt = f"""
                QUERY: {message}
                
                CONVERSATION CONTEXT:
                - Current equipment: {context.current_entity}
                - Equipment history: {', '.join(context.entity_history[-3:]) if context.entity_history else 'None'}
                - Recent topics: {', '.join(context.topics_covered[-3:]) if context.topics_covered else 'None'}
                - User expertise: {context.user_expertise_level}
                - Conversation duration: {(time.time() - context.conversation_start_time) / 60:.1f} minutes
                
                Classify this query for agent routing.
                """
                
                result = await agent_classifier.run(user_prompt=classification_prompt)
                return result.data
            else:
                # Fallback classification using keyword analysis
                return self._fallback_query_classification(message, context)
                
        except Exception as e:
            logger.error(f"Query classification failed: {e}")
            return self._fallback_query_classification(message, context)
    
    def _fallback_query_classification(self, message: str, context: ConversationContext) -> AgentQueryClassification:
        """Fallback query classification using keyword analysis"""
        message_lower = message.lower()
        
        # Safety keywords get highest priority
        safety_keywords = ['temperature', 'hot', 'burn', 'safe', 'danger', 'accident', 'contamination', 'allergic', 'sick']
        if any(keyword in message_lower for keyword in safety_keywords):
            return AgentQueryClassification(
                primary_agent=AgentType.SAFETY,
                confidence=0.9,
                reasoning="Safety keywords detected",
                safety_critical=True
            )
        
        # Equipment keywords
        equipment_keywords = ['fryer', 'grill', 'oven', 'ice machine', 'refrigerator', 'pos', 'computer', 'broken', 'not working']
        if any(keyword in message_lower for keyword in equipment_keywords):
            return AgentQueryClassification(
                primary_agent=AgentType.EQUIPMENT,
                confidence=0.8,
                reasoning="Equipment mentioned"
            )
        
        # Procedure keywords
        procedure_keywords = ['how to', 'steps', 'procedure', 'opening', 'closing', 'prep', 'prepare', 'checklist']
        if any(keyword in message_lower for keyword in procedure_keywords):
            return AgentQueryClassification(
                primary_agent=AgentType.PROCEDURE,
                confidence=0.7,
                reasoning="Procedure-related query"
            )
        
        # Maintenance keywords
        maintenance_keywords = ['clean', 'sanitize', 'maintenance', 'wash', 'filter', 'oil change', 'weekly', 'daily']
        if any(keyword in message_lower for keyword in maintenance_keywords):
            return AgentQueryClassification(
                primary_agent=AgentType.MAINTENANCE,
                confidence=0.7,
                reasoning="Maintenance-related query"
            )
        
        # Default to general agent
        return AgentQueryClassification(
            primary_agent=AgentType.GENERAL,
            confidence=0.5,
            reasoning="No specific domain detected"
        )
    
    async def run_specialized_agent(
        self, 
        agent_type: AgentType, 
        message: str, 
        context: ConversationContext,
        enhanced_context: Dict[str, Any] = None
    ) -> SpecializedAgentResponse:
        """Run a specific specialized agent with enhanced context"""
        
        # Select the appropriate agent
        agent = None
        if agent_type == AgentType.EQUIPMENT and qsr_equipment_agent:
            agent = qsr_equipment_agent
        elif agent_type == AgentType.PROCEDURE and qsr_procedure_agent:
            agent = qsr_procedure_agent
        elif agent_type == AgentType.SAFETY and qsr_safety_agent:
            agent = qsr_safety_agent
        elif agent_type == AgentType.MAINTENANCE and qsr_maintenance_agent:
            agent = qsr_maintenance_agent
        
        if not agent:
            # Return fallback response if agent not available
            return SpecializedAgentResponse(
                agent_type=agent_type,
                confidence_score=0.3,
                response_text=f"Specialized {agent_type.value} agent unavailable. Using general guidance.",
                specialized_insights={"fallback": True}
            )
        
        # Prepare enhanced prompt with context
        agent_prompt = self._prepare_agent_prompt(message, context, enhanced_context, agent_type)
        
        try:
            result = await agent.run(user_prompt=agent_prompt)
            return result.data
        except Exception as e:
            logger.error(f"Specialized agent {agent_type.value} failed: {e}")
            return SpecializedAgentResponse(
                agent_type=agent_type,
                confidence_score=0.2,
                response_text=f"Error with {agent_type.value} specialist. Please try rephrasing your question.",
                specialized_insights={"error": str(e)}
            )
    
    def _prepare_agent_prompt(
        self, 
        message: str, 
        context: ConversationContext, 
        enhanced_context: Dict[str, Any], 
        agent_type: AgentType
    ) -> str:
        """Prepare enhanced prompt for specialized agents"""
        
        prompt_parts = [f"USER QUERY: {message}"]
        
        # Add conversation context
        if context.current_entity:
            prompt_parts.append(f"CURRENT EQUIPMENT: {context.current_entity}")
        
        if context.entity_history:
            prompt_parts.append(f"EQUIPMENT HISTORY: {', '.join(context.entity_history[-5:])}")
        
        if context.conversation_history:
            recent_history = context.conversation_history[-3:]
            history_text = []
            for exchange in recent_history:
                if exchange.get('user') and exchange.get('assistant'):
                    history_text.append(f"User: {exchange['user']}")
                    history_text.append(f"Assistant: {exchange['assistant'][:100]}...")
            if history_text:
                prompt_parts.append("RECENT CONVERSATION:\n" + "\n".join(history_text))
        
        # Add enhanced context from Graph-RAG/Ragie
        if enhanced_context:
            if enhanced_context.get('graph_context'):
                prompt_parts.append(f"MANUAL CONTEXT: {enhanced_context['graph_context'][:500]}...")
            
            if enhanced_context.get('equipment_context'):
                prompt_parts.append(f"EQUIPMENT CONTEXT: {enhanced_context['equipment_context']}")
            
            if enhanced_context.get('visual_citations'):
                citations_count = len(enhanced_context['visual_citations'])
                prompt_parts.append(f"VISUAL CITATIONS AVAILABLE: {citations_count} citations ready for reference")
        
        # Add agent-specific instructions
        if agent_type == AgentType.SAFETY:
            prompt_parts.append("PRIORITY: Focus on safety requirements, regulations, and protective measures.")
        elif agent_type == AgentType.EQUIPMENT:
            prompt_parts.append("PRIORITY: Focus on technical details, troubleshooting, and equipment operation.")
        elif agent_type == AgentType.PROCEDURE:
            prompt_parts.append("PRIORITY: Provide clear step-by-step procedures with verification points.")
        elif agent_type == AgentType.MAINTENANCE:
            prompt_parts.append("PRIORITY: Focus on cleaning protocols, frequencies, and maintenance schedules.")
        
        prompt_parts.append("Provide specialized expertise in your domain with confidence scoring.")
        
        return "\n\n".join(prompt_parts)
    
    async def coordinate_multiple_agents(
        self, 
        classification: AgentQueryClassification,
        message: str,
        context: ConversationContext,
        enhanced_context: Dict[str, Any] = None
    ) -> VoiceResponse:
        """Coordinate multiple agents based on classification strategy"""
        
        if classification.coordination_strategy == AgentCoordinationStrategy.PARALLEL_CONSULTATION:
            return await self._parallel_agent_consultation(classification, message, context, enhanced_context)
        elif classification.coordination_strategy == AgentCoordinationStrategy.SEQUENTIAL_HANDOFF:
            return await self._sequential_agent_handoff(classification, message, context, enhanced_context)
        elif classification.coordination_strategy == AgentCoordinationStrategy.HIERARCHICAL:
            return await self._hierarchical_agent_coordination(classification, message, context, enhanced_context)
        else:
            # Single agent processing
            return await self._single_agent_processing(classification, message, context, enhanced_context)
    
    async def _parallel_agent_consultation(
        self, 
        classification: AgentQueryClassification,
        message: str,
        context: ConversationContext,
        enhanced_context: Dict[str, Any] = None
    ) -> VoiceResponse:
        """Run multiple agents in parallel and synthesize responses"""
        
        # Determine which agents to run
        agents_to_run = [classification.primary_agent] + classification.suggested_agents
        
        # Run agents in parallel
        tasks = []
        for agent_type in agents_to_run:
            task = self.run_specialized_agent(agent_type, message, context, enhanced_context)
            tasks.append(task)
        
        try:
            # Wait for all agents to complete
            agent_responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful responses
            successful_responses = []
            for response in agent_responses:
                if isinstance(response, SpecializedAgentResponse):
                    successful_responses.append(response)
                else:
                    logger.warning(f"Agent response error: {response}")
            
            if not successful_responses:
                # Fallback if all agents fail
                return await self._fallback_to_general_agent(message, context, enhanced_context)
            
            # Synthesize responses
            return self._synthesize_agent_responses(successful_responses, classification, context)
            
        except Exception as e:
            logger.error(f"Parallel agent consultation failed: {e}")
            return await self._fallback_to_general_agent(message, context, enhanced_context)
    
    def _synthesize_agent_responses(
        self, 
        responses: List[SpecializedAgentResponse], 
        classification: AgentQueryClassification,
        context: ConversationContext
    ) -> Union[VoiceResponse, 'EnhancedQSRResponse']:
        """Synthesize multiple agent responses into a coherent enhanced response"""
        
        # Prioritize safety responses
        safety_responses = [r for r in responses if r.agent_type == AgentType.SAFETY]
        
        if safety_responses and classification.safety_critical:
            # Safety takes priority
            primary_response = safety_responses[0]
            safety_priority = True
        else:
            # Use highest confidence response as primary
            primary_response = max(responses, key=lambda r: r.confidence_score)
            safety_priority = any(r.agent_type == AgentType.SAFETY for r in responses)
        
        # Combine insights from all agents
        combined_insights = {}
        all_safety_alerts = []
        all_equipment_context = []
        all_procedure_steps = []
        all_visual_citations = []
        all_enhanced_citations = []
        
        for response in responses:
            combined_insights[response.agent_type.value] = response.specialized_insights
            all_safety_alerts.extend(response.safety_alerts)
            all_equipment_context.extend(response.equipment_context)
            all_procedure_steps.extend(response.procedure_steps)
            all_visual_citations.extend(response.visual_citations)
            
            # Collect enhanced citations if available
            if ENHANCED_MODELS_AVAILABLE and response.enhanced_citations:
                all_enhanced_citations.extend(response.enhanced_citations)
        
        # Create synthesized response
        synthesized_text = primary_response.response_text
        
        # Add supplementary insights from other agents
        if len(responses) > 1:
            additional_insights = []
            for response in responses:
                if response != primary_response and response.confidence_score > 0.6:
                    insight = f"Additional {response.agent_type.value} insight: {response.response_text[:100]}..."
                    additional_insights.append(insight)
            
            if additional_insights:
                synthesized_text += "\n\nAdditional considerations:\n" + "\n".join(additional_insights)
        
        # Try to create enhanced response if models available
        if ENHANCED_MODELS_AVAILABLE:
            try:
                # Prepare enhanced base response data
                base_response_data = {
                    "text_response": synthesized_text,
                    "detected_intent": self._infer_intent_from_classification(classification),
                    "confidence_score": primary_response.confidence_score,
                    "should_continue_listening": not safety_priority,
                    "safety_priority": safety_priority,
                    "response_type": "safety" if safety_priority else "factual",
                    "primary_agent": classification.primary_agent,
                    "contributing_agents": [r.agent_type for r in responses],
                    "coordination_strategy": AgentCoordinationStrategy.PARALLEL_CONSULTATION,
                    "agent_confidence_scores": {r.agent_type.value: r.confidence_score for r in responses},
                    "specialized_insights": combined_insights,
                    "safety_warnings": all_safety_alerts
                }
                
                # Create equipment context if available
                equipment_ctx = None
                if all_equipment_context:
                    equipment_ctx = EquipmentContext(
                        equipment_id=all_equipment_context[0],
                        equipment_name=all_equipment_context[0],
                        equipment_type="qsr_equipment",
                        associated_citations=[c.citation_id for c in all_enhanced_citations] if all_enhanced_citations else []
                    )
                
                # Create enhanced response using factory
                enhanced_response = QSRResponseFactory.create_response(
                    agent_type=primary_response.agent_type,
                    base_response_data=base_response_data,
                    visual_citations=all_enhanced_citations,
                    equipment_context=equipment_ctx
                )
                
                logger.info(f"✨ Created enhanced {primary_response.agent_type.value} response with {len(all_enhanced_citations)} enhanced citations")
                return enhanced_response.to_voice_response()
                
            except Exception as e:
                logger.warning(f"Failed to create enhanced response, falling back to standard: {e}")
        
        # Fallback to standard VoiceResponse
        return VoiceResponse(
            text_response=synthesized_text,
            detected_intent=self._infer_intent_from_classification(classification),
            confidence_score=primary_response.confidence_score,
            should_continue_listening=not safety_priority,
            safety_priority=safety_priority,
            equipment_mentioned=all_equipment_context[0] if all_equipment_context else None,
            response_type="safety" if safety_priority else "factual",
            primary_agent=classification.primary_agent,
            contributing_agents=[r.agent_type for r in responses],
            coordination_strategy=AgentCoordinationStrategy.PARALLEL_CONSULTATION,
            agent_confidence_scores={r.agent_type.value: r.confidence_score for r in responses},
            specialized_insights=combined_insights
        )
    
    async def _single_agent_processing(
        self,
        classification: AgentQueryClassification,
        message: str,
        context: ConversationContext,
        enhanced_context: Dict[str, Any] = None
    ) -> VoiceResponse:
        """Process query with single specialized agent"""
        
        # Run the primary agent
        agent_response = await self.run_specialized_agent(
            classification.primary_agent, message, context, enhanced_context
        )
        
        # Convert specialized response to VoiceResponse
        return VoiceResponse(
            text_response=agent_response.response_text,
            detected_intent=self._infer_intent_from_classification(classification),
            confidence_score=agent_response.confidence_score,
            should_continue_listening=True,
            safety_priority=agent_response.agent_type == AgentType.SAFETY,
            equipment_mentioned=agent_response.equipment_context[0] if agent_response.equipment_context else None,
            response_type=self._map_agent_to_response_type(agent_response.agent_type),
            primary_agent=classification.primary_agent,
            contributing_agents=[agent_response.agent_type],
            coordination_strategy=AgentCoordinationStrategy.SINGLE_AGENT,
            agent_confidence_scores={agent_response.agent_type.value: agent_response.confidence_score},
            specialized_insights={agent_response.agent_type.value: agent_response.specialized_insights}
        )
    
    def _infer_intent_from_classification(self, classification: AgentQueryClassification) -> ConversationIntent:
        """Infer conversation intent from agent classification"""
        if classification.safety_critical:
            return ConversationIntent.EMERGENCY
        elif classification.primary_agent == AgentType.EQUIPMENT:
            return ConversationIntent.EQUIPMENT_QUESTION
        else:
            return ConversationIntent.NEW_TOPIC
    
    def _map_agent_to_response_type(self, agent_type: AgentType) -> str:
        """Map agent type to response type"""
        mapping = {
            AgentType.SAFETY: "safety",
            AgentType.PROCEDURE: "procedural", 
            AgentType.EQUIPMENT: "factual",
            AgentType.MAINTENANCE: "procedural",
            AgentType.GENERAL: "factual"
        }
        return mapping.get(agent_type, "factual")
    
    async def _fallback_to_general_agent(
        self, 
        message: str, 
        context: ConversationContext,
        enhanced_context: Dict[str, Any] = None
    ) -> VoiceResponse:
        """Fallback to general agent when specialized agents fail"""
        
        if voice_agent:
            # Use the original general agent logic
            try:
                enhanced_prompt = self._build_enhanced_prompt_for_general_agent(message, context, enhanced_context)
                result = await voice_agent.run(user_prompt=enhanced_prompt)
                return result.data
            except Exception as e:
                logger.error(f"General agent fallback failed: {e}")
        
        # Ultimate fallback
        return VoiceResponse(
            text_response="I'm having technical difficulties right now. Please try rephrasing your question or ask again in a moment.",
            detected_intent=ConversationIntent.NEW_TOPIC,
            confidence_score=0.1,
            should_continue_listening=True,
            primary_agent=AgentType.GENERAL,
            coordination_strategy=AgentCoordinationStrategy.SINGLE_AGENT
        )
    
    def _build_enhanced_prompt_for_general_agent(
        self, 
        message: str, 
        context: ConversationContext,
        enhanced_context: Dict[str, Any] = None
    ) -> str:
        """Build enhanced prompt for the general agent with multi-agent context"""
        
        prompt_parts = [
            f"USER MESSAGE: {message}",
            "",
            "CONVERSATION CONTEXT:",
            f"- Current equipment: {context.current_entity or 'None'}",
            f"- Equipment history: {', '.join(context.entity_history[-3:]) if context.entity_history else 'None'}",
            f"- User expertise: {context.user_expertise_level}",
            f"- Hands-free active: {context.hands_free_active}"
        ]
        
        if enhanced_context:
            prompt_parts.extend([
                "",
                "ENHANCED CONTEXT:",
                f"- Graph context available: {bool(enhanced_context.get('graph_context'))}",
                f"- Visual citations: {len(enhanced_context.get('visual_citations', []))}",
                f"- Equipment context: {enhanced_context.get('equipment_context', 'None')}"
            ])
            
            if enhanced_context.get('graph_context'):
                prompt_parts.extend([
                    "",
                    "MANUAL CONTEXT:",
                    enhanced_context['graph_context'][:800] + "..." if len(enhanced_context['graph_context']) > 800 else enhanced_context['graph_context']
                ])
        
        prompt_parts.extend([
            "",
            "INSTRUCTIONS:",
            "- Provide helpful QSR guidance using available context",
            "- Reference specific equipment and procedures when available", 
            "- Include safety considerations for equipment-related queries",
            "- Keep response conversational and practical",
            "- Use 6th-8th grade language level"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _sequential_agent_handoff(
        self,
        classification: AgentQueryClassification,
        message: str,
        context: ConversationContext,
        enhanced_context: Dict[str, Any] = None
    ) -> VoiceResponse:
        """Sequential handoff between agents (e.g., Equipment diagnosis → Maintenance solution)"""
        
        # Start with primary agent
        primary_response = await self.run_specialized_agent(
            classification.primary_agent, message, context, enhanced_context
        )
        
        # Determine if handoff is needed based on primary response
        handoff_needed = False
        next_agent = None
        
        if classification.primary_agent == AgentType.EQUIPMENT and primary_response.confidence_score > 0.7:
            # Equipment diagnosis successful, hand off to maintenance for solution
            if any(keyword in message.lower() for keyword in ['fix', 'repair', 'clean', 'maintenance']):
                handoff_needed = True
                next_agent = AgentType.MAINTENANCE
        elif classification.primary_agent == AgentType.PROCEDURE and any(alert in primary_response.safety_alerts for alert in primary_response.safety_alerts):
            # Procedure mentioned safety concerns, hand off to safety agent
            handoff_needed = True
            next_agent = AgentType.SAFETY
        
        if handoff_needed and next_agent:
            # Create handoff message
            handoff_message = f"Following up on {classification.primary_agent.value} guidance: {primary_response.response_text[:200]}... {message}"
            
            # Run next agent
            secondary_response = await self.run_specialized_agent(
                next_agent, handoff_message, context, enhanced_context
            )
            
            # Combine responses
            combined_text = f"{primary_response.response_text}\n\nAdditional guidance: {secondary_response.response_text}"
            
            return VoiceResponse(
                text_response=combined_text,
                detected_intent=self._infer_intent_from_classification(classification),
                confidence_score=max(primary_response.confidence_score, secondary_response.confidence_score),
                should_continue_listening=True,
                safety_priority=next_agent == AgentType.SAFETY,
                primary_agent=classification.primary_agent,
                contributing_agents=[primary_response.agent_type, secondary_response.agent_type],
                coordination_strategy=AgentCoordinationStrategy.SEQUENTIAL_HANDOFF,
                specialized_insights={
                    primary_response.agent_type.value: primary_response.specialized_insights,
                    secondary_response.agent_type.value: secondary_response.specialized_insights
                }
            )
        else:
            # No handoff needed, return primary response
            return self._convert_specialized_to_voice_response(primary_response, classification)
    
    async def _hierarchical_agent_coordination(
        self,
        classification: AgentQueryClassification,
        message: str,
        context: ConversationContext,
        enhanced_context: Dict[str, Any] = None
    ) -> VoiceResponse:
        """Hierarchical coordination with primary agent and specialist backup"""
        
        # Run primary agent
        primary_response = await self.run_specialized_agent(
            classification.primary_agent, message, context, enhanced_context
        )
        
        # If primary agent has low confidence, consult specialist
        if primary_response.confidence_score < 0.6 and classification.suggested_agents:
            specialist_agent = classification.suggested_agents[0]
            
            # Run specialist agent
            specialist_response = await self.run_specialized_agent(
                specialist_agent, message, context, enhanced_context
            )
            
            # Use specialist response if significantly better
            if specialist_response.confidence_score > primary_response.confidence_score + 0.2:
                return self._convert_specialized_to_voice_response(specialist_response, classification)
        
        # Use primary response
        return self._convert_specialized_to_voice_response(primary_response, classification)
    
    def _convert_specialized_to_voice_response(
        self, 
        specialized_response: SpecializedAgentResponse, 
        classification: AgentQueryClassification
    ) -> VoiceResponse:
        """Convert SpecializedAgentResponse to VoiceResponse"""
        
        return VoiceResponse(
            text_response=specialized_response.response_text,
            detected_intent=self._infer_intent_from_classification(classification),
            confidence_score=specialized_response.confidence_score,
            should_continue_listening=True,
            safety_priority=specialized_response.agent_type == AgentType.SAFETY,
            equipment_mentioned=specialized_response.equipment_context[0] if specialized_response.equipment_context else None,
            response_type=self._map_agent_to_response_type(specialized_response.agent_type),
            primary_agent=specialized_response.agent_type,
            contributing_agents=[specialized_response.agent_type],
            coordination_strategy=AgentCoordinationStrategy.SINGLE_AGENT,
            agent_confidence_scores={specialized_response.agent_type.value: specialized_response.confidence_score},
            specialized_insights={specialized_response.agent_type.value: specialized_response.specialized_insights}
        )
    
    # ===============================================================================
    # ENHANCED PROCESSING METHOD FOR TEXT CHAT INTEGRATION
    # ===============================================================================
    
    async def process_message(
        self, 
        message: str, 
        relevant_docs: List[Dict] = None,
        session_id: str = None,
        message_type: str = "text"
    ) -> VoiceResponse:
        """
        Universal message processing for both text and voice chat
        
        This method provides the same multi-agent capabilities for text chat
        as process_voice_message does for voice chat, ensuring feature parity.
        """
        
        # Use the same processing logic regardless of input type
        response = await self.process_voice_message(message, relevant_docs, session_id)
        
        # Adjust response characteristics for text vs voice
        if message_type == "text":
            # Text responses can be longer and more detailed
            response.should_continue_listening = False  # Text doesn't need continuous listening
            response.hands_free_recommendation = False  # Text doesn't use hands-free mode
        
        return response
    
    async def process_voice_message(
        self, 
        message: str, 
        relevant_docs: List[Dict] = None,
        session_id: str = None
    ) -> VoiceResponse:
        """Process voice message with advanced intelligent orchestration and Neo4j graph context"""
        
        context = self.get_context(session_id)
        session_id = session_id or self.default_session
        
        # STEP 1: Check for graph-specific voice commands first
        graph_response = None
        if self.voice_graph_service:
            try:
                graph_response = await self.voice_graph_service.process_voice_query_with_graph_context(
                    message, session_id
                )
                
                # If graph service found relevant content, use it as context for LLM processing
                if graph_response and graph_response.get("context_maintained"):
                    logger.info(f"Graph service found context for: {message[:50]}...")
                    
                    # Update conversation context with graph information
                    if graph_response.get("equipment_context"):
                        context.current_entity = graph_response["equipment_context"]
                        if graph_response["equipment_context"] not in context.entity_history:
                            context.entity_history.append(graph_response["equipment_context"])
                    
                    # Use graph response as enhanced context for LLM processing
                    # Rather than returning raw content, we'll pass it to the LLM below
                    enhanced_context = {
                        "graph_context": graph_response.get("response", ""),
                        "source_content": graph_response.get("source_content", []),
                        "page_references": graph_response.get("page_references", []),
                        "visual_citations": graph_response.get("visual_citations", []),
                        "equipment_context": graph_response.get("equipment_context"),
                        "query_type": graph_response.get("query_type", "general")
                    }
                    
                    logger.info(f"Enhanced context prepared with {len(enhanced_context.get('source_content', []))} source chunks")
                else:
                    enhanced_context = None
                    
            except Exception as e:
                logger.error(f"Graph service error: {e}")
                # Fall back to regular processing
        
        # STEP 2: Add user message to conversation history
        context.conversation_history.append({
            "user": message,
            "assistant": "",  # Will be filled after AI response
            "timestamp": time.time()
        })
        
        # Pre-process for topic/entity detection and context
        detected_entity = self._extract_topic_entities(message, relevant_docs)
        is_entity_switch = self._detect_entity_switch(detected_entity, context)
        
        # Prepare enhanced context for the agent
        context_data = {
            "current_message": message,
            "conversation_history": context.conversation_history[-5:],  # Last 5 exchanges
            "current_topic": context.current_topic,
            "current_entity": context.current_entity,
            "entity_history": context.entity_history,
            "last_document": context.last_document_referenced,
            "topics_covered": context.topics_covered,
            "hands_free_active": context.hands_free_active,
            "user_expertise": context.user_expertise_level,
            "last_intent": context.last_intent,
            "expecting_continuation": context.expecting_continuation,
            "conversation_duration": time.time() - context.conversation_start_time,
            "relevant_documents": relevant_docs or [],
            
            # NEW: Advanced context
            "current_procedure_step": context.current_procedure_step,
            "total_procedure_steps": context.total_procedure_steps,
            "procedure_type": context.procedure_type,
            "workflow_phase": context.workflow_phase,
            "error_count": context.error_count,
            "unclear_responses_count": context.unclear_responses_count,
            "topic_switches": context.topic_switches,
            "response_length_preference": context.response_length_preference,
            "detected_entity": detected_entity,
            "is_entity_switch": is_entity_switch,
            
            # Context references for memory
            "context_references": self._build_context_references(context),
            "conversation_flow_analysis": analyze_conversation_flow(context)
        }
        
        try:
            logger.info(f"🤖 PydanticAI processing voice message: '{message[:50]}...'")
            logger.info(f"🎯 Entity detected: {detected_entity}, Switch: {is_entity_switch}")
            
            # Check if voice agent is available
            if voice_agent is None:
                logger.warning("PydanticAI voice agent not available, using fallback")
                return self._fallback_response(message, context)
            
            # Enhanced prompt with context and graph data
            enhanced_prompt = f"""
VOICE MESSAGE: "{message}"

CURRENT CONTEXT:
- Current Entity/Topic: {context.current_entity or 'None'} 
- Procedure: {context.procedure_type} (Step {context.current_procedure_step}/{context.total_procedure_steps})
- Phase: {context.workflow_phase or 'Main conversation'}
- Last intent: {context.last_intent}
- Hands-free: {context.hands_free_active}
- Error count: {context.error_count}

DETECTED:
- New entity/topic: {detected_entity}
- Topic switch: {is_entity_switch}

CONVERSATION CONTEXT:
- Messages exchanged: {len(context.conversation_history)}
- Entity history: {', '.join(context.entity_history) if context.entity_history else 'None'}
- Topics covered: {', '.join(context.topics_covered) if context.topics_covered else 'None'}

ENHANCED KNOWLEDGE BASE CONTEXT:
{self._format_enhanced_context(enhanced_context) if enhanced_context else "No specific equipment documentation found."}

RELEVANT DOCUMENTS:
{json.dumps(relevant_docs or [], indent=2)}

EXECUTE ALL FOUR CAPABILITIES:
1. Smart Context Awareness - Track equipment, reference history
2. Intelligent Conversation Management - Predict continuation needs  
3. Advanced Voice Orchestration - Multi-phase workflows, conditional logic
4. Hands-Free Optimization - Kitchen environment awareness

RESPOND WITH ALL REQUIRED FIELDS INCLUDING:
- equipment_mentioned, equipment_switch_detected
- procedure_step_info, workflow_phase  
- context_references, response_type
- safety_priority, hands_free_recommendation
"""
            
            # ===================================================================
            # MULTI-AGENT PROCESSING - Enhanced with specialized QSR agents
            # ===================================================================
            
            # STEP 3A: Classify query for appropriate agent routing
            classification = await self.classify_query_for_agents(message, context)
            logger.info(f"🤖 Agent classification: {classification.primary_agent.value} (confidence: {classification.confidence:.2f})")
            
            # STEP 3B: Route to appropriate agent(s) based on classification
            if classification.requires_multiple_agents or classification.coordination_strategy != AgentCoordinationStrategy.SINGLE_AGENT:
                # Multi-agent coordination
                result_data = await self.coordinate_multiple_agents(classification, message, context, enhanced_context)
                logger.info(f"🔀 Multi-agent coordination: {len(result_data.contributing_agents)} agents")
            else:
                # Single agent processing (specialized or general)
                if classification.primary_agent == AgentType.GENERAL or not any([qsr_equipment_agent, qsr_procedure_agent, qsr_safety_agent, qsr_maintenance_agent]):
                    # Use general agent with enhanced context
                    if voice_agent:
                        result = await voice_agent.run(user_prompt=enhanced_prompt)
                        result_data = result.data
                        
                        # Mark as general agent response
                        result_data.primary_agent = AgentType.GENERAL
                        result_data.coordination_strategy = AgentCoordinationStrategy.SINGLE_AGENT
                        logger.info(f"🎯 General agent processing")
                    else:
                        # Fallback if no agents available
                        result_data = await self._fallback_to_general_agent(message, context, enhanced_context)
                else:
                    # Use specialized agent
                    result_data = await self._single_agent_processing(classification, message, context, enhanced_context)
                    logger.info(f"🎯 Specialized agent: {classification.primary_agent.value}")
            
            # STEP 3C: Enhanced context updates with multi-agent insights
            self._apply_advanced_context_updates(result_data, context, session_id)
            
            # Add multi-agent specific context updates
            if hasattr(result_data, 'specialized_insights') and result_data.specialized_insights:
                context.context_references.extend([f"Consulted {agent}" for agent in result_data.specialized_insights.keys()])
            
            # STEP 3D: Parse steps for future Playbooks UX (preserved functionality)
            result_data.parsed_steps = self._parse_response_steps(result_data.text_response)
            if result_data.parsed_steps.has_steps:
                logger.info(f"📋 Parsed {result_data.parsed_steps.total_steps} steps: {result_data.parsed_steps.procedure_title}")
            
            # STEP 3E: Enhanced logging with multi-agent details
            agent_info = f"Primary: {getattr(result_data, 'primary_agent', 'general')}"
            if hasattr(result_data, 'contributing_agents') and len(result_data.contributing_agents) > 1:
                agent_info += f", Contributing: {[a.value for a in result_data.contributing_agents]}"
            
            logger.info(f"🎯 Agent coordination complete - {agent_info}")
            logger.info(f"🎯 Intent: {result_data.detected_intent}, Equipment: {result_data.equipment_mentioned}")
            logger.info(f"🔄 Continue listening: {result_data.should_continue_listening}, Hands-free: {result_data.hands_free_recommendation}")
            logger.info(f"⚠️ Safety priority: {getattr(result_data, 'safety_priority', False)}")
            
            return result_data
            
        except Exception as e:
            logger.error(f"🚨 Voice orchestration error: {str(e)}")
            
            # Use intelligent fallback instead of error recovery when entity is detected
            if detected_entity:
                logger.info(f"🔄 Using intelligent fallback for entity: {detected_entity}")
                return self._intelligent_entity_fallback(message, detected_entity, context, relevant_docs)
            else:
                # Enhanced error recovery with context preservation
                return self._enhanced_error_recovery(message, context)
    
    def _format_enhanced_context(self, enhanced_context: Dict[str, Any]) -> str:
        """Format enhanced context from graph service for LLM processing"""
        if not enhanced_context:
            return "No specific context available."
        
        context_parts = []
        
        # Add query type context
        query_type = enhanced_context.get("query_type", "general")
        if query_type == "temperature":
            context_parts.append("QUERY TYPE: Temperature and food safety requirements")
        elif query_type == "safety":
            context_parts.append("QUERY TYPE: Safety procedures and guidelines")
        
        # Add source content (most important)
        source_content = enhanced_context.get("source_content", [])
        if source_content:
            context_parts.append("RELEVANT MANUAL CONTENT:")
            for i, content in enumerate(source_content[:3], 1):  # Top 3 chunks
                # Clean and format the content
                clean_content = content.replace("\n", " ").strip()
                if len(clean_content) > 300:
                    clean_content = clean_content[:300] + "..."
                context_parts.append(f"{i}. {clean_content}")
        
        # Add page references
        page_refs = enhanced_context.get("page_references", [])
        if page_refs:
            context_parts.append(f"PAGE REFERENCES: {', '.join(map(str, page_refs))}")
        
        # Add equipment context
        equipment = enhanced_context.get("equipment_context")
        if equipment:
            context_parts.append(f"EQUIPMENT CONTEXT: {equipment}")
        
        # Add instruction for LLM
        context_parts.append("\nINSTRUCTION: Use the above manual content to provide a specific, helpful answer about temperature requirements or safety procedures. Extract specific numbers, temperatures, and procedures from the manual content. Do not repeat the raw manual text - synthesize it into a clear, conversational response.")
        
        return "\n".join(context_parts)
    
    def _fallback_response(self, message: str, context: ConversationContext) -> VoiceResponse:
        """Fallback response when PydanticAI agent isn't available"""
        
        # Simple intent detection based on keywords
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["thank", "thanks", "that's all", "goodbye"]):
            intent = ConversationIntent.COMPLETION
            should_continue = False
            complete = True
        elif any(word in message_lower for word in ["what about", "also", "and"]):
            intent = ConversationIntent.FOLLOW_UP
            should_continue = True
            complete = False
        elif any(word in message_lower for word in ["don't understand", "unclear", "what do you mean"]):
            intent = ConversationIntent.CLARIFICATION
            should_continue = True
            complete = False
        else:
            intent = ConversationIntent.EQUIPMENT_QUESTION
            should_continue = True
            complete = False
        
        return VoiceResponse(
            text_response="I understand. Let me help you with that. (Note: PydanticAI agent not available)",
            detected_intent=intent,
            should_continue_listening=should_continue,
            next_voice_state=VoiceState.LISTENING if should_continue else VoiceState.CONVERSATION_COMPLETE,
            confidence_score=0.5,
            conversation_complete=complete,
            suggested_follow_ups=["Is there anything else I can help with?"] if should_continue else []
        )
    
    def end_conversation(self, session_id: str = None):
        """Clean up conversation context"""
        session_id = session_id or self.default_session
        if session_id in self.active_contexts:
            del self.active_contexts[session_id]
    
    def get_conversation_summary(self, session_id: str = None) -> Dict[str, Any]:
        """Get summary of conversation for analytics"""
        context = self.get_context(session_id)
        return {
            "duration": time.time() - context.conversation_start_time,
            "message_count": len(context.conversation_history),
            "topics_covered": context.topics_covered,
            "entities_discussed": context.entity_history,
            "last_intent": context.last_intent,
            "completion_status": context.voice_state == VoiceState.CONVERSATION_COMPLETE,
            "procedure_progress": {
                "type": context.procedure_type,
                "step": context.current_procedure_step,
                "total": context.total_procedure_steps
            }
        }
    
    def _extract_topic_entities(self, message: str, relevant_docs: List[Dict] = None) -> Optional[str]:
        """Extract key topics/entities from user message and relevant documents"""
        message_lower = message.lower()
        
        # First check for common QSR entities/topics from documents
        qsr_entities = {
            # Equipment (order matters - most specific first)
            "ice cream machine": ["ice cream machine", "soft serve machine", "frozen yogurt machine"],
            "fryer": ["fryer", "deep fryer", "fry station"],
            "grill": ["grill", "griddle", "flat top", "char grill"],
            "ice machine": ["ice machine", "ice maker", "ice dispenser"],  # Removed ice cream machine
            "freezer": ["freezer", "walk-in freezer", "freezer unit"],
            "refrigerator": ["refrigerator", "fridge", "cooler", "walk-in cooler"],
            "oven": ["oven", "convection oven", "pizza oven"],
            "dishwasher": ["dishwasher", "dish machine", "warewasher"],
            "coffee machine": ["coffee machine", "coffee maker", "espresso machine"],
            "pos system": ["pos", "point of sale", "register", "cash register"],
            
            # Food safety & procedures
            "cleaning": ["cleaning", "sanitizing", "disinfecting", "hygiene"],
            "food safety": ["food safety", "temperature", "haccp", "contamination"],
            "oil change": ["oil change", "oil replacement", "filter change"],
            "maintenance": ["maintenance", "repair", "service", "inspection"],
            "training": ["training", "orientation", "procedures", "protocol"],
            
            # Ingredients & food items
            "oil": ["oil", "cooking oil", "frying oil"],
            "ingredients": ["ingredients", "recipe", "preparation"],
            "temperature": ["temperature", "temp", "heating", "cooling"],
            
            # Operations
            "opening": ["opening", "start up", "morning routine"],
            "closing": ["closing", "shut down", "end of day"],
            "shift change": ["shift change", "handover", "transition"]
        }
        
        # Check message for entity keywords
        for entity, keywords in qsr_entities.items():
            if any(keyword in message_lower for keyword in keywords):
                return entity
        
        # If no direct match, try to extract from document content
        if relevant_docs:
            for doc in relevant_docs[:2]:  # Check top 2 relevant docs
                content = doc.get('content', '').lower()
                # Look for key nouns/topics in document content
                for entity, keywords in qsr_entities.items():
                    if any(keyword in content for keyword in keywords):
                        return entity
        
        return None
    
    def _detect_entity_switch(self, new_entity: Optional[str], context: ConversationContext) -> bool:
        """Detect if user is switching to different topic/entity"""
        if not new_entity or not context.current_entity:
            return False
        return new_entity != context.current_entity
    
    def _build_context_references(self, context: ConversationContext) -> List[str]:
        """Build references to previous conversation parts"""
        references = []
        
        # Reference to equipment discussions
        if context.entity_history:
            # Filter out None values to prevent join errors
            valid_entities = [entity for entity in context.entity_history if entity is not None]
            if valid_entities:
                references.append(f"Topics discussed: {', '.join(valid_entities)}")
        
        # Reference to procedure progress
        if context.procedure_type and context.current_procedure_step:
            references.append(f"Currently in {context.procedure_type} procedure, step {context.current_procedure_step}")
        
        # Reference to recent topics
        if context.topics_covered:
            references.append(f"Previous topics: {', '.join(context.topics_covered[-2:])}")
        
        return references
    
    def _apply_advanced_context_updates(self, response: VoiceResponse, context: ConversationContext, session_id: str):
        """Apply sophisticated context updates from AI response"""
        
        # Update the last conversation entry with assistant response
        if context.conversation_history:
            context.conversation_history[-1].update({
                "assistant": response.text_response,
                "intent": response.detected_intent,
                "state": response.next_voice_state,
                "equipment": response.equipment_mentioned,
                "response_type": response.response_type,
                "safety_priority": response.safety_priority,
                "procedure_step": response.procedure_step_info
            })
        
        # Entity/Topic tracking (includes equipment and other topics)
        if response.equipment_mentioned:
            if response.equipment_switch_detected:
                # Track topic switch
                context.topic_switches += 1
                context.last_equipment_switch_time = time.time()
                
            # Update current entity (for equipment types)
            context.current_entity = response.equipment_mentioned
            
            # Add to entity history if not already there (and not None)
            if response.equipment_mentioned and response.equipment_mentioned not in context.entity_history:
                context.entity_history.append(response.equipment_mentioned)
        
        # Handle non-equipment entities from context_updates
        if response.context_updates and "current_entity" in response.context_updates:
            entity = response.context_updates["current_entity"]
            context.current_entity = entity
            if entity and entity not in context.entity_history:
                context.entity_history.append(entity)
        
        # Procedure tracking
        if response.procedure_step_info:
            step_info = response.procedure_step_info
            context.current_procedure_step = step_info.get("current_step")
            context.total_procedure_steps = step_info.get("total_steps")
            context.procedure_type = step_info.get("procedure_type")
        
        # Workflow phase tracking
        if response.workflow_phase:
            context.workflow_phase = response.workflow_phase
        
        # State updates
        context.voice_state = response.next_voice_state
        context.last_intent = response.detected_intent
        context.expecting_continuation = response.should_continue_listening
        context.last_response_time = time.time()
        
        # Apply additional context updates
        if response.context_updates:
            self.update_context(session_id, response.context_updates)
        
        # Hands-free management
        context.hands_free_active = response.hands_free_recommendation
        
        # Error tracking
        if response.detected_intent == ConversationIntent.CLARIFICATION:
            context.unclear_responses_count += 1
        else:
            context.unclear_responses_count = 0  # Reset on clear response
    
    def _intelligent_entity_fallback(
        self, 
        message: str, 
        entity: str, 
        context: ConversationContext,
        relevant_docs: List[Dict] = None
    ) -> VoiceResponse:
        """Intelligent fallback for topic/entity-related queries when PydanticAI fails"""
        
        # Generate helpful response based on entity and documents
        if relevant_docs and len(relevant_docs) > 0:
            # Use document information for more informed response
            doc_info = relevant_docs[0].get('content', '')
            if len(doc_info) > 300:
                # Extract first meaningful sentence(s)
                sentences = doc_info.split('. ')
                doc_info = '. '.join(sentences[:2]) + "."
            
            response_text = f"Based on the documentation, here's what I found about {entity}: {doc_info} Would you like me to go into more detail on any specific aspect?"
        else:
            # Generic helpful response based on entity type
            entity_responses = {
                "ice machine": "I can help with your ice machine. What specific issue are you having - not making ice, water leaking, or cleaning maintenance?",
                "fryer": "I can help with your fryer. Are you looking for cleaning steps, oil change procedure, or troubleshooting an issue?",
                "grill": "I can help with your grill. Do you need cleaning instructions, temperature adjustments, or troubleshooting help?",
                "cleaning": "I can help with cleaning procedures. Are you looking for equipment cleaning, food safety protocols, or sanitizing steps?",
                "food safety": "I can help with food safety guidelines. Are you asking about temperatures, storage, or contamination prevention?",
                "oil change": "I can help with oil change procedures. Would you like step-by-step instructions or maintenance schedules?",
                "training": "I can help with training materials. Are you looking for new employee orientation or specific procedure training?",
                "maintenance": "I can help with maintenance procedures. What equipment or system needs attention?"
            }
            
            response_text = entity_responses.get(entity, f"I can help you with {entity}. What specifically would you like to know?")
        
        # Update context
        context.current_entity = entity
        if entity and entity not in context.entity_history:
            context.entity_history.append(entity)
        
        # Parse steps from the response
        parsed_steps = self._parse_response_steps(response_text)
        
        return VoiceResponse(
            text_response=response_text,
            detected_intent=ConversationIntent.EQUIPMENT_QUESTION if entity in ["fryer", "grill", "ice machine"] else ConversationIntent.NEW_TOPIC,
            should_continue_listening=True,
            next_voice_state=VoiceState.LISTENING,
            confidence_score=0.7,
            equipment_mentioned=entity if entity in ["fryer", "grill", "ice machine"] else None,
            response_type="factual",
            hands_free_recommendation=True,
            context_updates={
                "current_entity": entity,
                "current_topic": f"{entity} assistance"
            },
            parsed_steps=parsed_steps
        )

    def _parse_response_steps(self, response_text: str) -> ParsedStepsResponse:
        """Parse steps from AI response for future Playbooks UX integration"""
        try:
            return parse_ai_response_steps(response_text)
        except Exception as e:
            logger.warning(f"Step parsing failed: {str(e)}")
            # Return empty result on parsing failure
            return ParsedStepsResponse(
                original_text=response_text,
                has_steps=False,
                total_steps=0
            )

    def _enhanced_error_recovery(self, message: str, context: ConversationContext) -> VoiceResponse:
        """Enhanced error recovery with context preservation"""
        context.error_count += 1
        
        # Preserve context while recovering
        entity_context = f" about {context.current_entity}" if context.current_entity else ""
        procedure_context = f" in the {context.procedure_type} process" if context.procedure_type else ""
        
        if context.error_count > 2:
            # Suggest alternative interaction mode
            recovery_text = f"I'm having trouble understanding. Should we switch to typing instead? I heard something{entity_context}{procedure_context}."
            should_continue = False
        else:
            # Try to recover with context
            recovery_text = f"I heard something{entity_context}{procedure_context}. What specifically did you need help with?"
            should_continue = True
        
        return VoiceResponse(
            text_response=recovery_text,
            detected_intent=ConversationIntent.CLARIFICATION,
            should_continue_listening=should_continue,
            next_voice_state=VoiceState.ERROR_RECOVERY,
            confidence_score=0.3,
            equipment_mentioned=context.current_entity if context.current_entity in ["fryer", "grill", "ice machine"] else None,
            response_type="clarification",
            hands_free_recommendation=should_continue
        )

# Global orchestrator instance
voice_orchestrator = VoiceOrchestrator()
voice_orchestrator.clear_all_contexts()  # Clear any existing contexts on startup

# Enhanced voice utility functions
def analyze_conversation_flow(context: ConversationContext) -> Dict[str, Any]:
    """Analyze conversation patterns for optimization"""
    recent_intents = [
        msg.get("intent") for msg in context.conversation_history[-3:]
        if msg.get("intent")
    ]
    
    return {
        "recent_intent_pattern": recent_intents,
        "conversation_depth": len(context.conversation_history),
        "topic_switches": len(context.topics_covered),
        "engagement_level": "high" if len(context.conversation_history) > 3 else "standard"
    }

def predict_conversation_end(message: str, context: ConversationContext) -> bool:
    """Predict if conversation is naturally ending"""
    ending_signals = [
        "thank", "thanks", "that's all", "that's it", "good", "perfect",
        "great", "awesome", "got it", "understood", "bye", "goodbye"
    ]
    
    message_lower = message.lower()
    return any(signal in message_lower for signal in ending_signals)

def detect_response_type(message: str, context: ConversationContext) -> str:
    """Detect the type of response needed based on message and context"""
    message_lower = message.lower()
    
    # Safety-related queries
    safety_keywords = ["temperature", "hot", "burn", "electrical", "gas", "chemical", "danger", "safety"]
    if any(keyword in message_lower for keyword in safety_keywords):
        return "safety"
    
    # Procedural queries (cleaning, maintenance, etc.)
    procedure_keywords = ["clean", "maintenance", "repair", "fix", "steps", "how to", "process"]
    if any(keyword in message_lower for keyword in procedure_keywords):
        return "procedural"
    
    # Clarification requests
    clarification_keywords = ["what do you mean", "don't understand", "unclear", "explain", "repeat"]
    if any(keyword in message_lower for keyword in clarification_keywords):
        return "clarification"
    
    # Completion signals
    completion_keywords = ["thanks", "thank you", "that's all", "done", "finished"]
    if any(keyword in message_lower for keyword in completion_keywords):
        return "completion"
    
    # Default to factual
    return "factual"

def should_maintain_hands_free(response_type: str, equipment_mentioned: bool, procedure_active: bool) -> bool:
    """Determine if hands-free mode should stay active"""
    
    # Always maintain for procedural guidance
    if response_type in ["procedural", "safety"] or procedure_active:
        return True
    
    # Maintain if equipment is being discussed (assume worker is at station)
    if equipment_mentioned:
        return True
    
    # End hands-free for completion signals
    if response_type == "completion":
        return False
    
    # Default to maintaining for most interactions
    return True

def extract_procedure_info(message: str, response_text: str) -> Optional[Dict[str, Any]]:
    """Extract procedure step information from response"""
    
    # Look for step patterns in the response
    import re
    
    # Pattern for "Step X of Y" or "X steps total"
    step_pattern = r'(?:step\s+)?(\d+)(?:\s+of\s+(\d+))?'
    step_match = re.search(step_pattern, response_text.lower())
    
    if step_match:
        current_step = int(step_match.group(1))
        total_steps = int(step_match.group(2)) if step_match.group(2) else None
        
        # Determine procedure type
        procedure_type = "general"
        if "clean" in response_text.lower():
            procedure_type = "cleaning"
        elif "maintain" in response_text.lower() or "maintenance" in response_text.lower():
            procedure_type = "maintenance"
        elif "troubleshoot" in response_text.lower() or "fix" in response_text.lower():
            procedure_type = "troubleshooting"
        
        return {
            "current_step": current_step,
            "total_steps": total_steps,
            "procedure_type": procedure_type
        }
    
    return None

def generate_conversation_bridges(response_type: str, equipment: Optional[str], procedure_complete: bool) -> List[str]:
    """Generate natural conversation bridges based on context"""
    bridges = []
    
    if response_type == "procedural":
        if procedure_complete:
            bridges.extend([
                f"All steps done. Any questions about the process?",
                f"That covers the {equipment or 'equipment'} procedure. What else do you need?",
                "Need help with anything else?"
            ])
        else:
            bridges.extend([
                "Ready for the next part?",
                "Need help with any of these steps?",
                "Questions before we continue?"
            ])
    
    elif response_type == "safety":
        bridges.extend([
            "Questions about this before we continue?",
            "Want me to go over the safety steps again?",
            "All clear on the safety requirements?"
        ])
    
    elif response_type == "factual" and equipment:
        bridges.extend([
            f"Any other {equipment} questions?",
            f"What else about the {equipment}?",
            "Need more details on anything?"
        ])
    
    return bridges[:2]  # Return top 2 most relevant bridges