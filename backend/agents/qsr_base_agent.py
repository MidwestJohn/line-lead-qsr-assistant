#!/usr/bin/env python3
"""
QSR Base Agent - Phase 1 Implementation
=======================================

Core PydanticAI Agent implementation for QSR functionality.
Replaces custom OpenAI integration with official PydanticAI patterns.

Features:
- Official PydanticAI Agent with QSR system prompt
- Structured response handling
- Context-aware processing
- Error handling with PydanticAI exceptions

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior, ModelRetry
from pydantic_ai.messages import ModelMessage
from pydantic import BaseModel, Field

# QSR-specific system prompt
QSR_SYSTEM_PROMPT = """You are an expert QSR (Quick Service Restaurant) assistant with comprehensive knowledge of:

**EQUIPMENT EXPERTISE:**
- Taylor ice cream machines (maintenance, troubleshooting, cleaning)
- Vulcan fryers (operation, temperature control, safety)
- Hobart mixers (operation, maintenance, troubleshooting)
- Traulsen refrigeration (temperature management, maintenance)
- General restaurant equipment diagnostics

**SAFETY PROTOCOLS:**
- Food safety and HACCP compliance
- Kitchen safety procedures
- Emergency response protocols
- Burn treatment and first aid
- Fire safety and evacuation procedures
- Incident reporting and documentation

**OPERATIONAL PROCEDURES:**
- Opening and closing procedures
- Shift management and transitions
- Quality control processes
- Customer service protocols
- Inventory management systems
- Cash handling procedures

**TRAINING & DEVELOPMENT:**
- New employee onboarding
- Skill development programs
- Performance evaluation
- Compliance training
- Certification tracking

**RESPONSE GUIDELINES:**
1. Always prioritize safety in your responses
2. Provide clear, step-by-step instructions
3. Reference specific equipment manuals when applicable
4. Include safety warnings for potentially dangerous procedures
5. Suggest when to seek professional help or escalate
6. Use numbered lists for complex procedures
7. Provide context for why procedures are important

**EMERGENCY SITUATIONS:**
For safety emergencies, always:
- Provide immediate action steps
- Emphasize safety first
- Suggest when to call emergency services
- Include follow-up procedures
- Document incident requirements

**CITATION FORMAT:**
When referencing manuals or procedures, use this format:
- [Equipment Manual: Page X] or [Safety Protocol: Section Y]
- Be specific about document sources
- Include relevant page numbers or section references

You have access to comprehensive equipment manuals, safety protocols, and operational procedures through integrated document search. Always strive to provide accurate, actionable, and safe guidance.
"""

@dataclass
class QSRContext:
    """Context for QSR agent operations"""
    conversation_id: str
    user_location: Optional[str] = None
    equipment_context: Optional[Dict[str, Any]] = None
    safety_alerts: List[str] = None
    previous_queries: List[str] = None
    
    def __post_init__(self):
        if self.safety_alerts is None:
            self.safety_alerts = []
        if self.previous_queries is None:
            self.previous_queries = []

class QSRResponse(BaseModel):
    """Structured response from QSR agent"""
    response: str
    response_type: str = Field(default="general", description="Type of response: general, equipment, safety, operations, training")
    confidence: float = Field(default=0.8, description="Confidence score for the response")
    safety_alerts: List[str] = Field(default_factory=list, description="Any safety alerts or warnings")
    equipment_references: List[str] = Field(default_factory=list, description="Referenced equipment")
    citations: List[str] = Field(default_factory=list, description="Document citations")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    escalation_required: bool = Field(default=False, description="Whether escalation is needed")
    
    class Config:
        exclude_none = False

class QSRBaseAgent:
    """
    Base QSR Agent using PydanticAI patterns
    
    This replaces the custom OpenAI integration with official PydanticAI Agent
    while maintaining all QSR-specific functionality.
    """
    
    def __init__(self, model: str = None):
        # Use environment variable or default to GPT-4o
        model = model or os.getenv("QSR_MODEL", "openai:gpt-4o")
        
        # Initialize PydanticAI Agent with QSR system prompt
        # PydanticAI automatically handles OPENAI_API_KEY environment variable
        self.agent = Agent(
            model=model,
            system_prompt=QSR_SYSTEM_PROMPT,
            retries=3
        )
        
        # Agent metadata
        self.agent_id = "qsr_base_agent"
        self.version = "1.0.0"
        self.created_at = datetime.now()
        
        # Performance tracking
        self.query_count = 0
        self.total_response_time = 0.0
        self.error_count = 0
    
    async def process_query(
        self, 
        query: str, 
        context: QSRContext,
        message_history: List[ModelMessage] = None
    ) -> QSRResponse:
        """
        Process a QSR query using PydanticAI Agent
        
        Args:
            query: User query
            context: QSR context information
            message_history: Previous conversation messages
            
        Returns:
            QSRResponse with structured response data
        """
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Enhance query with context
            enhanced_query = self._enhance_query_with_context(query, context)
            
            # Run PydanticAI Agent
            result = await self.agent.run(
                enhanced_query,
                message_history=message_history or []
            )
            
            # Process response
            response_data = self._process_response(result.data, query, context)
            
            # Update performance metrics
            self.query_count += 1
            self.total_response_time += asyncio.get_event_loop().time() - start_time
            
            return response_data
            
        except UnexpectedModelBehavior as e:
            self.error_count += 1
            return QSRResponse(
                response=f"I encountered an unexpected issue processing your request. Please try rephrasing your question.",
                response_type="error",
                confidence=0.0,
                escalation_required=True
            )
            
        except ModelRetry as e:
            self.error_count += 1
            return QSRResponse(
                response=f"I'm having trouble processing your request right now. Please try again in a moment.",
                response_type="error",
                confidence=0.0,
                escalation_required=False
            )
            
        except Exception as e:
            self.error_count += 1
            return QSRResponse(
                response=f"I'm experiencing technical difficulties. Please contact support if this continues.",
                response_type="error",
                confidence=0.0,
                escalation_required=True
            )
    
    async def process_query_stream(
        self,
        query: str,
        context: QSRContext,
        message_history: List[ModelMessage] = None
    ):
        """
        Process a QSR query with streaming response using PydanticAI patterns
        
        Args:
            query: User query
            context: QSR context information
            message_history: Previous conversation messages
            
        Yields:
            Streaming response chunks
        """
        
        try:
            # Enhance query with context
            enhanced_query = self._enhance_query_with_context(query, context)
            
            # Use PydanticAI streaming
            async with self.agent.run_stream(
                enhanced_query,
                message_history=message_history or []
            ) as result:
                
                complete_response = ""
                
                async for text_chunk in result.stream(debounce_by=0.01):
                    complete_response += text_chunk
                    
                    # Yield chunk with QSR formatting
                    yield {
                        "chunk": text_chunk,
                        "complete_response": complete_response,
                        "timestamp": datetime.now().isoformat(),
                        "agent_id": self.agent_id,
                        "done": False
                    }
                
                # Process final response for metadata
                final_response = self._process_response(complete_response, query, context)
                
                # Yield final metadata
                yield {
                    "chunk": "",
                    "complete_response": complete_response,
                    "timestamp": datetime.now().isoformat(),
                    "agent_id": self.agent_id,
                    "done": True,
                    "metadata": {
                        "response_type": final_response.response_type,
                        "confidence": final_response.confidence,
                        "safety_alerts": final_response.safety_alerts,
                        "equipment_references": final_response.equipment_references,
                        "citations": final_response.citations,
                        "follow_up_suggestions": final_response.follow_up_suggestions,
                        "escalation_required": final_response.escalation_required
                    }
                }
                
                # Update performance metrics
                self.query_count += 1
                
        except Exception as e:
            # Handle streaming errors
            yield {
                "chunk": "",
                "complete_response": f"Error processing request: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "done": True,
                "error": str(e)
            }
    
    def _enhance_query_with_context(self, query: str, context: QSRContext) -> str:
        """Enhance query with context information"""
        
        enhanced_parts = [query]
        
        # Add conversation context
        if context.conversation_id:
            enhanced_parts.append(f"\nConversation ID: {context.conversation_id}")
        
        # Add equipment context
        if context.equipment_context:
            equipment_info = []
            for equipment, details in context.equipment_context.items():
                equipment_info.append(f"- {equipment}: {details}")
            if equipment_info:
                enhanced_parts.append(f"\nEquipment Context:\n" + "\n".join(equipment_info))
        
        # Add safety context
        if context.safety_alerts:
            enhanced_parts.append(f"\nActive Safety Alerts: {', '.join(context.safety_alerts)}")
        
        # Add previous query context
        if context.previous_queries:
            recent_queries = context.previous_queries[-3:]  # Last 3 queries
            enhanced_parts.append(f"\nRecent queries: {', '.join(recent_queries)}")
        
        # Add location context
        if context.user_location:
            enhanced_parts.append(f"\nLocation: {context.user_location}")
        
        return "\n".join(enhanced_parts)
    
    def _process_response(self, response_text: str, original_query: str, context: QSRContext) -> QSRResponse:
        """Process raw response into structured QSRResponse"""
        
        # Determine response type
        response_type = self._classify_response_type(response_text, original_query)
        
        # Extract safety alerts
        safety_alerts = self._extract_safety_alerts(response_text)
        
        # Extract equipment references
        equipment_references = self._extract_equipment_references(response_text)
        
        # Extract citations
        citations = self._extract_citations(response_text)
        
        # Generate follow-up suggestions
        follow_up_suggestions = self._generate_follow_up_suggestions(response_text, response_type)
        
        # Determine if escalation is required
        escalation_required = self._requires_escalation(response_text, safety_alerts)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(response_text, response_type)
        
        return QSRResponse(
            response=response_text,
            response_type=response_type,
            confidence=confidence,
            safety_alerts=safety_alerts,
            equipment_references=equipment_references,
            citations=citations,
            follow_up_suggestions=follow_up_suggestions,
            escalation_required=escalation_required
        )
    
    def _classify_response_type(self, response: str, query: str) -> str:
        """Classify the type of response"""
        
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Safety-related keywords
        safety_keywords = ["safety", "emergency", "danger", "warning", "hazard", "accident", "injury", "fire", "burn"]
        if any(keyword in response_lower or keyword in query_lower for keyword in safety_keywords):
            return "safety"
        
        # Equipment-related keywords
        equipment_keywords = ["taylor", "vulcan", "hobart", "traulsen", "machine", "equipment", "maintenance", "repair"]
        if any(keyword in response_lower or keyword in query_lower for keyword in equipment_keywords):
            return "equipment"
        
        # Training-related keywords
        training_keywords = ["training", "learn", "teach", "onboard", "skill", "certification", "assessment"]
        if any(keyword in response_lower or keyword in query_lower for keyword in training_keywords):
            return "training"
        
        # Operations-related keywords
        operations_keywords = ["procedure", "process", "opening", "closing", "shift", "inventory", "quality"]
        if any(keyword in response_lower or keyword in query_lower for keyword in operations_keywords):
            return "operations"
        
        return "general"
    
    def _extract_safety_alerts(self, response: str) -> List[str]:
        """Extract safety alerts from response"""
        
        alerts = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["warning", "danger", "caution", "alert", "hazard"]):
                alerts.append(line.strip())
        
        return alerts
    
    def _extract_equipment_references(self, response: str) -> List[str]:
        """Extract equipment references from response"""
        
        equipment_brands = ["taylor", "vulcan", "hobart", "traulsen", "rational", "cleveland"]
        references = []
        
        response_lower = response.lower()
        for brand in equipment_brands:
            if brand in response_lower:
                references.append(brand.title())
        
        return list(set(references))  # Remove duplicates
    
    def _extract_citations(self, response: str) -> List[str]:
        """Extract citations from response"""
        
        citations = []
        
        # Look for citation patterns [Manual: Page X] or [Protocol: Section Y]
        import re
        citation_pattern = r'\[(.*?)\]'
        matches = re.findall(citation_pattern, response)
        
        for match in matches:
            if any(keyword in match.lower() for keyword in ["manual", "protocol", "procedure", "page", "section"]):
                citations.append(match)
        
        return citations
    
    def _generate_follow_up_suggestions(self, response: str, response_type: str) -> List[str]:
        """Generate follow-up suggestions based on response type"""
        
        suggestions = []
        
        if response_type == "equipment":
            suggestions.extend([
                "Would you like maintenance schedule information?",
                "Do you need troubleshooting steps for specific issues?",
                "Are there any safety precautions I should explain?"
            ])
        
        elif response_type == "safety":
            suggestions.extend([
                "Do you need emergency contact information?",
                "Would you like training materials for your team?",
                "Should I explain incident reporting procedures?"
            ])
        
        elif response_type == "operations":
            suggestions.extend([
                "Would you like detailed procedures for your location?",
                "Do you need training materials for staff?",
                "Are there specific quality standards to review?"
            ])
        
        elif response_type == "training":
            suggestions.extend([
                "Would you like assessment materials?",
                "Do you need certification tracking help?",
                "Should I provide additional learning resources?"
            ])
        
        else:
            suggestions.extend([
                "Do you need more specific information?",
                "Would you like me to explain any procedures?",
                "Are there related topics you'd like to explore?"
            ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _requires_escalation(self, response: str, safety_alerts: List[str]) -> bool:
        """Determine if escalation is required"""
        
        # Escalate if there are safety alerts
        if safety_alerts:
            return True
        
        # Escalate for emergency keywords
        emergency_keywords = ["emergency", "call 911", "immediate", "urgent", "critical"]
        response_lower = response.lower()
        
        return any(keyword in response_lower for keyword in emergency_keywords)
    
    def _calculate_confidence(self, response: str, response_type: str) -> float:
        """Calculate confidence score for response"""
        
        # Base confidence
        confidence = 0.8
        
        # Increase confidence for structured responses
        if any(marker in response for marker in ["1.", "2.", "3.", "•", "-"]):
            confidence += 0.1
        
        # Increase confidence for citations
        if "[" in response and "]" in response:
            confidence += 0.1
        
        # Adjust for response type
        if response_type == "safety":
            confidence += 0.05  # Safety responses are typically more confident
        
        # Ensure confidence is within valid range
        return min(1.0, max(0.0, confidence))
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        
        avg_response_time = self.total_response_time / self.query_count if self.query_count > 0 else 0
        
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "query_count": self.query_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.query_count if self.query_count > 0 else 0,
            "average_response_time": avg_response_time,
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "model": str(self.agent.model)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the agent"""
        
        try:
            # Test basic functionality
            test_result = await self.agent.run("Test query")
            
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "model": str(self.agent.model),
                "test_successful": True,
                "performance_metrics": self.get_performance_metrics(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "model": str(self.agent.model),
                "test_successful": False,
                "error": str(e),
                "performance_metrics": self.get_performance_metrics(),
                "timestamp": datetime.now().isoformat()
            }

# Global agent instance (lazy-loaded)
_qsr_base_agent = None

def get_qsr_base_agent() -> QSRBaseAgent:
    """Get or create the global QSR base agent instance"""
    global _qsr_base_agent
    if _qsr_base_agent is None:
        _qsr_base_agent = QSRBaseAgent()
    return _qsr_base_agent

# For backward compatibility
qsr_base_agent = get_qsr_base_agent()

# Factory function for creating agents
def create_qsr_agent(model: str = None) -> QSRBaseAgent:
    """Factory function to create QSR agents"""
    return QSRBaseAgent(model=model)

# Async factory function
async def create_qsr_agent_async(model: str = None) -> QSRBaseAgent:
    """Async factory function to create QSR agents"""
    agent = QSRBaseAgent(model=model)
    
    # Perform health check
    health_status = await agent.health_check()
    
    if health_status["status"] != "healthy":
        raise Exception(f"Agent health check failed: {health_status.get('error', 'Unknown error')}")
    
    return agent

if __name__ == "__main__":
    # Test the agent
    async def test_agent():
        agent = await create_qsr_agent_async()
        
        context = QSRContext(
            conversation_id="test_conversation",
            equipment_context={"Taylor Ice Cream Machine": "Model C712"}
        )
        
        # Test standard query
        response = await agent.process_query(
            "How do I clean the Taylor ice cream machine?",
            context
        )
        
        print("Standard Response:")
        print(f"Response: {response.response}")
        print(f"Type: {response.response_type}")
        print(f"Confidence: {response.confidence}")
        print(f"Safety Alerts: {response.safety_alerts}")
        print(f"Equipment References: {response.equipment_references}")
        print()
        
        # Test streaming query
        print("Streaming Response:")
        async for chunk in agent.process_query_stream(
            "What are the safety procedures for handling hot oil?",
            context
        ):
            if chunk["done"]:
                print(f"Final metadata: {chunk.get('metadata', {})}")
            else:
                print(f"Chunk: {chunk['chunk']}", end="")
        
        print()
        print("Performance Metrics:")
        print(agent.get_performance_metrics())
    
    asyncio.run(test_agent())