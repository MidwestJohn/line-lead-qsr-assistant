"""
PydanticAI Voice Orchestration for Line Lead QSR MVP
Intelligent conversation management with context awareness and state orchestration
"""

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import time
import logging
import json
import os
from step_parser import parse_ai_response_steps, ParsedStepsResponse

logger = logging.getLogger(__name__)

class VoiceState(str, Enum):
    """Enhanced voice states for intelligent conversation flow"""
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    WAITING_FOR_CONTINUATION = "waiting_for_continuation"
    TOPIC_TRANSITION = "topic_transition"
    ERROR_RECOVERY = "error_recovery"
    CONVERSATION_COMPLETE = "conversation_complete"

class ConversationIntent(str, Enum):
    """Detected user intents for better response handling"""
    EQUIPMENT_QUESTION = "equipment_question"
    FOLLOW_UP = "follow_up"
    NEW_TOPIC = "new_topic"
    CLARIFICATION = "clarification"
    COMPLETION = "completion"
    EMERGENCY = "emergency"

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
                
                # If graph service handled the query completely, use its response
                if graph_response and graph_response.get("context_maintained") and graph_response.get("response"):
                    logger.info(f"Graph service handled query: {message[:50]}...")
                    
                    # Update conversation context with graph information
                    if graph_response.get("equipment_context"):
                        context.current_entity = graph_response["equipment_context"]
                        if graph_response["equipment_context"] not in context.entity_history:
                            context.entity_history.append(graph_response["equipment_context"])
                    
                    # Create VoiceResponse from graph response
                    graph_voice_response = VoiceResponse(
                        text_response=graph_response["response"],
                        detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
                        confidence_score=0.9,
                        should_continue_listening=True,
                        equipment_mentioned=graph_response.get("equipment_context"),
                        context_references=["neo4j_graph_context"],
                        response_type="factual"
                    )
                    
                    # Add to conversation history
                    context.conversation_history.append({
                        "user": message,
                        "assistant": graph_response["response"],
                        "timestamp": time.time(),
                        "source": "neo4j_graph"
                    })
                    
                    return graph_voice_response
                    
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
            
            # Enhanced prompt with context (avoiding complex conversation history that causes issues)
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
            
            # Run the enhanced voice agent (without message_history to avoid format issues)
            result = await voice_agent.run(
                user_prompt=enhanced_prompt
                # Note: Conversation history is included in the enhanced_prompt instead
            )
            
            # Enhanced context updates
            self._apply_advanced_context_updates(result.data, context, session_id)
            
            # NEW: Parse steps for future Playbooks UX
            result.data.parsed_steps = self._parse_response_steps(result.data.text_response)
            if result.data.parsed_steps.has_steps:
                logger.info(f"📋 Parsed {result.data.parsed_steps.total_steps} steps: {result.data.parsed_steps.procedure_title}")
            
            logger.info(f"🎯 Intent: {result.data.detected_intent}, Equipment: {result.data.equipment_mentioned}")
            logger.info(f"🔄 Continue listening: {result.data.should_continue_listening}, Hands-free: {result.data.hands_free_recommendation}")
            
            return result.data
            
        except Exception as e:
            logger.error(f"🚨 Voice orchestration error: {str(e)}")
            
            # Use intelligent fallback instead of error recovery when entity is detected
            if detected_entity:
                logger.info(f"🔄 Using intelligent fallback for entity: {detected_entity}")
                return self._intelligent_entity_fallback(message, detected_entity, context, relevant_docs)
            else:
                # Enhanced error recovery with context preservation
                return self._enhanced_error_recovery(message, context)
    
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