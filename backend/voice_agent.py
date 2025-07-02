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

# Create the intelligent voice orchestration agent
try:
    voice_agent = Agent(
        model=OpenAIModel("gpt-4o-mini"),
        result_type=VoiceResponse,
        system_prompt="""You are Line Lead's intelligent voice orchestration system for QSR workers.

CORE MISSION:
Provide world-class restaurant equipment assistance through natural, continuous voice conversations while maintaining context and intelligence across multiple exchanges.

CONVERSATION INTELLIGENCE:
- Analyze user intent: is this a new question, follow-up, clarification, or completion signal?
- Maintain context: reference previous messages, build on established topics
- Predict continuation: determine if user likely has more questions vs conversation ending
- Handle transitions: smoothly manage topic changes and multi-part questions
- Recover gracefully: when unclear, ask clarifying questions while staying helpful

VOICE OPTIMIZATION:
- Keep responses under 80 words for optimal TTS pronunciation
- Use numbered lists for multi-step processes (our chunking preserves these)
- Speak like a helpful coworker, not a corporate manual
- Use simple 6th-8th grade language appropriate for busy QSR workers
- Include natural conversation bridges ("Also..." "Next..." "By the way...")

STATE MANAGEMENT:
- should_continue_listening=True for follow-ups, multi-part answers
- should_continue_listening=False for complete answers where user likely satisfied
- conversation_complete=True only for clear ending signals ("thanks", "that's all", "goodbye")
- Set expecting_continuation=True when your response naturally leads to more questions

INTENT DETECTION:
- equipment_question: Direct equipment-related queries
- follow_up: "What about...", "How do I...", "Also..."
- new_topic: Clear topic changes
- clarification: "What do you mean...", "I don't understand..."
- completion: "Thanks", "that's it", "I'm good"
- emergency: Safety issues, equipment failures

DOCUMENT INTEGRATION:
- Set requires_document_lookup=True when specific manual info needed
- Provide document_query for precise information retrieval
- Reference document findings naturally in conversation

RESPONSE EXAMPLES:
User: "How do I clean the fryer?"
Response: Multi-step cleaning process + "Need help with any of these steps?"

User: "What about the oil change?"
Response: Oil change process + reference to previous cleaning context

User: "Thanks, that's all I needed"
Response: Brief acknowledgment + conversation_complete=True

Remember: You're helping busy restaurant workers who need quick, clear, actionable guidance."""
    )
except Exception as e:
    logger.error(f"Failed to initialize PydanticAI voice agent: {str(e)}")
    voice_agent = None

class VoiceOrchestrator:
    """Intelligent voice conversation orchestrator using PydanticAI"""
    
    def __init__(self):
        self.active_contexts: Dict[str, ConversationContext] = {}
        self.default_session = "default"
        
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
        """Process voice message with intelligent orchestration"""
        
        context = self.get_context(session_id)
        
        # Prepare context for the agent
        context_data = {
            "current_message": message,
            "conversation_history": context.conversation_history[-5:],  # Last 5 exchanges
            "current_topic": context.current_topic,
            "last_document": context.last_document_referenced,
            "topics_covered": context.topics_covered,
            "hands_free_active": context.hands_free_active,
            "user_expertise": context.user_expertise_level,
            "last_intent": context.last_intent,
            "expecting_continuation": context.expecting_continuation,
            "conversation_duration": time.time() - context.conversation_start_time,
            "relevant_documents": relevant_docs or []
        }
        
        try:
            logger.info(f"🤖 PydanticAI processing voice message: '{message[:50]}...'")
            
            # Check if voice agent is available
            if voice_agent is None:
                logger.warning("PydanticAI voice agent not available, using fallback")
                return self._fallback_response(message, context)
            
            # Run the intelligent voice agent
            result = await voice_agent.run(
                user_prompt=f"""
Process this voice message: "{message}"

Context: {json.dumps(context_data, indent=2)}

Provide an intelligent response with:
1. Appropriate text response for TTS
2. Intent detection and confidence
3. Next state determination
4. Context updates for conversation flow
5. Continuation prediction
""",
                message_history=context.conversation_history[-3:]  # Recent context
            )
            
            # Update conversation context
            context.conversation_history.append({
                "user": message,
                "assistant": result.data.text_response,
                "timestamp": time.time(),
                "intent": result.data.detected_intent,
                "state": result.data.next_voice_state
            })
            
            # Apply context updates
            if result.data.context_updates:
                self.update_context(session_id, result.data.context_updates)
            
            # Update conversation state
            context.voice_state = result.data.next_voice_state
            context.last_intent = result.data.detected_intent
            context.expecting_continuation = result.data.should_continue_listening
            context.last_response_time = time.time()
            
            # Track topics
            if result.data.detected_intent == ConversationIntent.NEW_TOPIC:
                if context.current_topic and context.current_topic not in context.topics_covered:
                    context.topics_covered.append(context.current_topic)
                context.current_topic = message[:50]  # First 50 chars as topic
            
            logger.info(f"🎯 Intent: {result.data.detected_intent}, Continue: {result.data.should_continue_listening}")
            
            return result.data
            
        except Exception as e:
            logger.error(f"🚨 Voice orchestration error: {str(e)}")
            
            # Fallback response with error recovery
            return VoiceResponse(
                text_response="I had trouble processing that. Could you try asking again?",
                detected_intent=ConversationIntent.ERROR_RECOVERY,
                should_continue_listening=True,
                next_voice_state=VoiceState.ERROR_RECOVERY,
                confidence_score=0.3
            )
    
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
            "last_intent": context.last_intent,
            "completion_status": context.voice_state == VoiceState.CONVERSATION_COMPLETE
        }

# Global orchestrator instance
voice_orchestrator = VoiceOrchestrator()

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