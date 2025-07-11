import os
import logging
from typing import Dict, List, Any, Optional
import json
import asyncio
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class VoiceContext:
    session_id: str
    current_equipment: Optional[str]
    current_procedure: Optional[str]
    conversation_history: List[Dict[str, Any]]
    graph_entities: List[str]
    last_updated: datetime

class VoiceGraphService:
    def __init__(self):
        self.use_graph_context = os.getenv('USE_GRAPH_CONTEXT', 'false').lower() == 'true'
        self.sessions: Dict[str, VoiceContext] = {}
        self.rag_service = None
        
    def set_rag_service(self, rag_service):
        """Inject RAG service dependency."""
        self.rag_service = rag_service
    
    async def create_voice_session(self, session_id: str) -> VoiceContext:
        """Create new voice session with graph context."""
        context = VoiceContext(
            session_id=session_id,
            current_equipment=None,
            current_procedure=None,
            conversation_history=[],
            graph_entities=[],
            last_updated=datetime.now()
        )
        
        self.sessions[session_id] = context
        logger.info(f"Created voice session: {session_id}")
        return context
    
    async def process_voice_query(self, session_id: str, query: str, audio_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process voice query with graph context persistence."""
        # Get or create session
        if session_id not in self.sessions:
            await self.create_voice_session(session_id)
        
        context = self.sessions[session_id]
        
        try:
            # Add query to conversation history
            context.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "user_voice",
                "content": query,
                "audio_metadata": audio_metadata
            })
            
            # Extract equipment/procedure context from query
            equipment_context = await self._extract_equipment_context(query, context)
            
            # Update session context BEFORE generating response
            context.last_updated = datetime.now()
            if equipment_context.get("equipment"):
                context.current_equipment = equipment_context["equipment"]
            if equipment_context.get("procedure"):
                context.current_procedure = equipment_context["procedure"]
            
            # Query knowledge graph for relevant context
            graph_context = await self._get_graph_context(query, context)
            
            # Generate response with updated context
            response = await self._generate_contextual_response(query, context, graph_context)
            
            # Add response to history
            context.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "assistant_voice",
                "content": response["text"],
                "context_used": graph_context,
                "equipment": context.current_equipment,
                "procedure": context.current_procedure
            })
            
            return {
                "session_id": session_id,
                "response": response,
                "context": {
                    "current_equipment": context.current_equipment,
                    "current_procedure": context.current_procedure,
                    "graph_entities": context.graph_entities[-5:]  # Last 5 entities
                },
                "audio_ready": True
            }
            
        except Exception as e:
            logger.error(f"Voice query processing failed: {e}")
            # Fallback to basic response
            return await self._fallback_voice_response(query, session_id)
    
    async def _extract_equipment_context(self, query: str, context: VoiceContext) -> Dict[str, Any]:
        """Extract equipment and procedure context from voice query."""
        # Define QSR equipment patterns
        equipment_patterns = {
            "fryer": ["fryer", "deep fryer", "oil", "frying"],
            "grill": ["grill", "griddle", "burger", "patty"],
            "ice_cream_machine": ["ice cream", "soft serve", "frozen", "ice cream machine"],
            "coffee_machine": ["coffee", "espresso", "latte", "cappuccino"],
            "oven": ["oven", "bake", "pizza", "convection"],
            "freezer": ["freezer", "frozen", "temperature", "cold storage"]
        }
        
        procedure_patterns = {
            "cleaning": ["clean", "wash", "sanitize", "disinfect"],
            "maintenance": ["maintain", "service", "repair", "fix"],
            "troubleshooting": ["problem", "issue", "not working", "broken", "error"],
            "operation": ["how to use", "operate", "start", "turn on"]
        }
        
        query_lower = query.lower()
        
        # Detect equipment
        detected_equipment = None
        for equipment, keywords in equipment_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_equipment = equipment
                break
        
        # Detect procedure
        detected_procedure = None
        for procedure, keywords in procedure_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_procedure = procedure
                break
        
        # Use context if not explicitly mentioned
        if not detected_equipment and context.current_equipment:
            detected_equipment = context.current_equipment
        
        if not detected_procedure and context.current_procedure:
            detected_procedure = context.current_procedure
        
        return {
            "equipment": detected_equipment,
            "procedure": detected_procedure,
            "confidence": 0.8 if detected_equipment and detected_procedure else 0.5
        }
    
    async def _get_graph_context(self, query: str, context: VoiceContext) -> Dict[str, Any]:
        """Retrieve relevant context from knowledge graph."""
        if not self.use_graph_context or not self.rag_service or not self.rag_service.initialized:
            return {"source": "none", "entities": [], "relationships": []}
        
        try:
            # Build context-aware query
            contextual_query = self._build_contextual_query(query, context)
            
            # Query knowledge graph
            graph_result = await self.rag_service.search(contextual_query, mode="local")
            
            # Extract entities and relationships mentioned
            entities = self._extract_mentioned_entities(graph_result.get("response", ""))
            
            # Update session entities
            context.graph_entities.extend(entities)
            context.graph_entities = context.graph_entities[-20:]  # Keep last 20
            
            return {
                "source": "knowledge_graph",
                "query_used": contextual_query,
                "entities": entities,
                "relationships": graph_result.get("relationships", []),
                "raw_result": graph_result
            }
            
        except Exception as e:
            logger.error(f"Graph context retrieval failed: {e}")
            return {"source": "error", "error": str(e)}
    
    def _build_contextual_query(self, query: str, context: VoiceContext) -> str:
        """Build context-aware query for knowledge graph."""
        contextual_parts = [query]
        
        if context.current_equipment:
            contextual_parts.append(f"equipment: {context.current_equipment}")
        
        if context.current_procedure:
            contextual_parts.append(f"procedure: {context.current_procedure}")
        
        # Add recent conversation context
        recent_messages = context.conversation_history[-3:]  # Last 3 messages
        if recent_messages:
            recent_context = " ".join([msg["content"] for msg in recent_messages if msg["type"] == "user_voice"])
            if recent_context:
                contextual_parts.append(f"recent context: {recent_context}")
        
        return " | ".join(contextual_parts)
    
    def _extract_mentioned_entities(self, response: str) -> List[str]:
        """Extract equipment/procedure entities mentioned in response."""
        # Simple entity extraction - in production, use NER
        entities = []
        response_lower = response.lower()
        
        equipment_terms = ["fryer", "grill", "ice cream machine", "coffee machine", "oven", "freezer"]
        procedure_terms = ["cleaning", "maintenance", "troubleshooting", "operation"]
        
        for term in equipment_terms + procedure_terms:
            if term in response_lower:
                entities.append(term)
        
        return list(set(entities))
    
    async def _generate_contextual_response(self, query: str, context: VoiceContext, graph_context: Dict) -> Dict[str, Any]:
        """Generate response using graph context."""
        if self.rag_service and self.rag_service.initialized:
            # Use RAG-powered response
            rag_result = await self.rag_service.search(query, mode="hybrid")
            response_text = rag_result.get("response", "I'm not sure about that.")
        else:
            # Fallback to context-aware template response
            response_text = self._generate_template_response(query, context)
        
        # Enhance response with voice-specific formatting
        voice_response = self._format_for_voice(response_text, context)
        
        return {
            "text": voice_response,
            "formatted_for_voice": True,
            "includes_context": bool(graph_context.get("entities")),
            "citations": self._extract_citations(response_text),
            "suggested_actions": self._generate_voice_actions(context)
        }
    
    def _format_for_voice(self, text: str, context: VoiceContext) -> str:
        """Format response optimally for voice output."""
        # Convert numbered lists to voice-friendly format
        voice_text = text.replace("1.", "First,").replace("2.", "Second,").replace("3.", "Third,")
        voice_text = voice_text.replace("4.", "Fourth,").replace("5.", "Fifth,")
        
        # Add equipment context if relevant
        if context.current_equipment:
            equipment_name = context.current_equipment.replace("_", " ")
            if equipment_name not in voice_text.lower():
                voice_text = f"For your {equipment_name}: {voice_text}"
        
        # Add pause indicators for complex instructions
        voice_text = voice_text.replace(". ", ". ... ")
        
        return voice_text
    
    def _extract_citations(self, text: str) -> List[Dict[str, str]]:
        """Extract document/page citations from response."""
        # Simple citation extraction - enhance based on your manual format
        citations = []
        if "manual" in text.lower():
            citations.append({"type": "manual", "reference": "equipment manual"})
        if "page" in text.lower():
            citations.append({"type": "page", "reference": "manual page reference"})
        return citations
    
    def _generate_voice_actions(self, context: VoiceContext) -> List[str]:
        """Generate suggested voice commands for current context."""
        actions = ["Ask me another question", "Say 'help' for more options"]
        
        if context.current_equipment:
            actions.append(f"Ask about {context.current_equipment} maintenance")
            actions.append("Say 'next step' to continue")
        
        if context.current_procedure:
            actions.append(f"Ask for {context.current_procedure} details")
        
        return actions[:3]  # Limit to 3 suggestions
    
    def _generate_template_response(self, query: str, context: VoiceContext) -> str:
        """Generate template response when RAG unavailable."""
        equipment = context.current_equipment or "equipment"
        equipment_display = equipment.replace("_", " ") if equipment else "equipment"
        procedure = context.current_procedure or "maintenance"
        
        templates = {
            "cleaning": f"For {equipment_display} cleaning, first ensure the equipment is turned off and cooled down. Then follow the cleaning procedure in your manual.",
            "maintenance": f"For {equipment_display} maintenance, check the schedule in your manual and follow the step-by-step procedure.",
            "troubleshooting": f"For {equipment_display} issues, first check the common problems section in your manual, then follow the troubleshooting steps.",
            "operation": f"To operate your {equipment_display}, refer to the operation section in your manual for detailed instructions."
        }
        
        return templates.get(procedure, f"Please check your {equipment_display} manual for detailed instructions about: {query}")
    
    async def _fallback_voice_response(self, query: str, session_id: str) -> Dict[str, Any]:
        """Fallback response when main processing fails."""
        return {
            "session_id": session_id,
            "response": {
                "text": "I'm having trouble accessing the knowledge base right now. Please check your equipment manual or try asking your question differently.",
                "formatted_for_voice": True,
                "includes_context": False,
                "citations": [],
                "suggested_actions": ["Try rephrasing your question", "Check equipment manual"]
            },
            "context": {"fallback_used": True},
            "audio_ready": True
        }
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of voice session for debugging."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        context = self.sessions[session_id]
        return {
            "session_id": session_id,
            "created": context.conversation_history[0]["timestamp"] if context.conversation_history else None,
            "last_updated": context.last_updated.isoformat(),
            "current_equipment": context.current_equipment,
            "current_procedure": context.current_procedure,
            "conversation_turns": len(context.conversation_history),
            "entities_mentioned": list(set(context.graph_entities)),
            "recent_queries": [msg["content"] for msg in context.conversation_history[-3:] if msg["type"] == "user_voice"]
        }

# Global instance
voice_graph_service = VoiceGraphService()