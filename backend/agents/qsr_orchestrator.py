#!/usr/bin/env python3
"""
QSR Agent Orchestrator - Phase 2 Implementation
===============================================

Intelligent routing system that selects the most appropriate specialist agent
for each query. Coordinates between equipment, safety, operations, and training
specialists while maintaining context awareness.

Features:
- Query classification and intelligent routing
- Context-aware agent selection
- Seamless handoffs between specialists
- Performance monitoring and optimization
- Fallback to base agent when needed

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior, ModelRetry
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic import BaseModel, Field

# Import shared types
from .types import AgentType, QueryClassification, OrchestratorResponse

# Import specialist agents
try:
    from .qsr_base_agent import QSRBaseAgent as QSRAgent, QSRContext, QSRResponse
    from .equipment_agent import EquipmentSpecialistAgent as EquipmentAgent, EquipmentContext
    from .safety_agent import SafetySpecialistAgent as SafetyAgent, SafetyContext  
    from .operations_agent import OperationsSpecialistAgent as OperationsAgent, OperationsContext
    from .training_agent import TrainingSpecialistAgent as TrainingAgent, TrainingContext
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from agents.qsr_base_agent import QSRBaseAgent as QSRAgent, QSRContext, QSRResponse
    from agents.equipment_agent import EquipmentSpecialistAgent as EquipmentAgent, EquipmentContext
    from agents.safety_agent import SafetySpecialistAgent as SafetyAgent, SafetyContext  
    from agents.operations_agent import OperationsSpecialistAgent as OperationsAgent, OperationsContext
    from agents.training_agent import TrainingSpecialistAgent as TrainingAgent, TrainingContext





@dataclass
class QSROrchestrator:
    """
    Intelligent agent orchestrator for QSR operations.
    
    Routes queries to appropriate specialist agents based on content analysis,
    maintains context across agent handoffs, and optimizes performance.
    """
    
    # Core configuration
    model: str = "openai:gpt-4o"
    enable_fallback: bool = True
    enable_handoffs: bool = True
    performance_tracking: bool = True
    
    # Performance metrics
    query_count: int = field(default=0)
    classification_accuracy: float = field(default=0.0)
    average_response_time: float = field(default=0.0)
    agent_usage_stats: Dict[str, int] = field(default_factory=dict)
    
    # Agent instances (initialized lazily)
    _agents: Dict[AgentType, Union[QSRAgent, EquipmentAgent, SafetyAgent, OperationsAgent, TrainingAgent]] = field(default_factory=dict)
    _classifier: Optional[Agent] = None
    _initialized: bool = field(default=False)
    
    def __post_init__(self):
        """Initialize logging"""
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> None:
        """Initialize all agents asynchronously"""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing QSR Agent Orchestrator...")
            
            # Initialize classifier agent
            self._classifier = Agent(
                model=self.model,
                system_prompt=self._get_classifier_prompt(),
                retries=2
            )
            
            # Initialize specialist agents
            self._agents[AgentType.BASE] = await self._create_base_agent()
            self._agents[AgentType.EQUIPMENT] = await self._create_equipment_agent()
            self._agents[AgentType.SAFETY] = await self._create_safety_agent()
            self._agents[AgentType.OPERATIONS] = await self._create_operations_agent()
            self._agents[AgentType.TRAINING] = await self._create_training_agent()
            
            # Initialize usage stats
            for agent_type in AgentType:
                self.agent_usage_stats[agent_type.value] = 0
                
            self._initialized = True
            self.logger.info("QSR Agent Orchestrator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def _create_base_agent(self) -> QSRAgent:
        """Create base QSR agent"""
        from agents.qsr_base_agent import create_qsr_agent_async
        return await create_qsr_agent_async()
    
    async def _create_equipment_agent(self) -> EquipmentAgent:
        """Create equipment specialist agent"""
        if hasattr(EquipmentAgent, 'create'):
            return await EquipmentAgent.create()
        else:
            return EquipmentAgent()
    
    async def _create_safety_agent(self) -> SafetyAgent:
        """Create safety specialist agent"""
        if hasattr(SafetyAgent, 'create'):
            return await SafetyAgent.create()
        else:
            return SafetyAgent()
    
    async def _create_operations_agent(self) -> OperationsAgent:
        """Create operations specialist agent"""
        if hasattr(OperationsAgent, 'create'):
            return await OperationsAgent.create()
        else:
            return OperationsAgent()
    
    async def _create_training_agent(self) -> TrainingAgent:
        """Create training specialist agent"""
        if hasattr(TrainingAgent, 'create'):
            return await TrainingAgent.create()
        else:
            return TrainingAgent()
    
    def _get_classifier_prompt(self) -> str:
        """Get the system prompt for query classification"""
        return """You are a QSR Query Classifier that analyzes user queries and determines which specialist agent should handle them.

**AGENT TYPES:**

1. **EQUIPMENT** - Handle when query involves:
   - Specific equipment (Taylor, Vulcan, Hobart, Traulsen)
   - Error codes, diagnostics, troubleshooting
   - Maintenance, repairs, calibration
   - Equipment operation instructions

2. **SAFETY** - Handle when query involves:
   - Emergency situations or incidents
   - Food safety, HACCP, health codes
   - Injury, accidents, hazards
   - Safety protocols and procedures
   - Urgent safety concerns

3. **OPERATIONS** - Handle when query involves:
   - Opening/closing procedures
   - Shift management, scheduling
   - Inventory, ordering, quality control
   - Customer service procedures
   - Daily operational workflows

4. **TRAINING** - Handle when query involves:
   - Employee training, onboarding
   - Skill development, certifications
   - Performance coaching
   - Learning assessments
   - Training procedures and materials

5. **BASE** - Use as fallback for:
   - General QSR questions
   - Multi-domain queries
   - Complex queries spanning multiple areas
   - When classification is uncertain

**CLASSIFICATION RULES:**
- Prioritize SAFETY for any urgent or safety-critical content
- Use primary/secondary agents for complex queries
- Set confidence based on keyword clarity
- Mark urgency as "high" for safety/emergency content
- Provide clear reasoning for decisions

Respond with structured classification data only."""

    async def classify_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> QueryClassification:
        """Classify a query to determine appropriate agent"""
        try:
            # Prepare classification prompt
            classification_prompt = f"""
Query: "{query}"

Context: {context or {}}

Classify this query and respond with a JSON object containing:
- primary_agent: The main agent type to handle this query
- secondary_agent: Optional secondary agent for complex queries  
- confidence: Float 0.0-1.0 confidence in classification
- keywords: List of key terms that influenced the decision
- urgency: "low", "normal", or "high" based on content urgency
- reasoning: Brief explanation of the classification decision

Respond with valid JSON only.
"""

            # Get classification from LLM
            result = await self._classifier.run(classification_prompt)
            
            # Parse the classification result
            import json
            try:
                classification_data = json.loads(result.data)
                classification = QueryClassification(**classification_data)
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Failed to parse classification: {e}")
                # Fallback classification
                classification = self._fallback_classification(query)
                
            return classification
            
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return self._fallback_classification(query)
    
    def _fallback_classification(self, query: str) -> QueryClassification:
        """Provide fallback classification using keyword matching"""
        query_lower = query.lower()
        
        # Safety keywords (highest priority)
        safety_keywords = ["emergency", "fire", "burn", "cut", "injury", "accident", "poison", "allergic", "hurt", "danger", "unsafe", "hazard"]
        if any(keyword in query_lower for keyword in safety_keywords):
            return QueryClassification(
                primary_agent=AgentType.SAFETY,
                confidence=0.8,
                keywords=[kw for kw in safety_keywords if kw in query_lower],
                urgency="high",
                reasoning="Fallback: Safety keywords detected"
            )
        
        # Equipment keywords
        equipment_keywords = ["taylor", "vulcan", "hobart", "traulsen", "machine", "equipment", "error", "e01", "e02", "diagnostic", "repair", "maintenance"]
        if any(keyword in query_lower for keyword in equipment_keywords):
            return QueryClassification(
                primary_agent=AgentType.EQUIPMENT,
                confidence=0.7,
                keywords=[kw for kw in equipment_keywords if kw in query_lower],
                urgency="normal",
                reasoning="Fallback: Equipment keywords detected"
            )
        
        # Operations keywords
        operations_keywords = ["opening", "closing", "procedure", "shift", "inventory", "quality", "customer", "service", "workflow"]
        if any(keyword in query_lower for keyword in operations_keywords):
            return QueryClassification(
                primary_agent=AgentType.OPERATIONS,
                confidence=0.7,
                keywords=[kw for kw in operations_keywords if kw in query_lower],
                urgency="normal",
                reasoning="Fallback: Operations keywords detected"
            )
        
        # Training keywords
        training_keywords = ["training", "onboarding", "teach", "learn", "certification", "skill", "coach", "assessment", "new employee"]
        if any(keyword in query_lower for keyword in training_keywords):
            return QueryClassification(
                primary_agent=AgentType.TRAINING,
                confidence=0.7,
                keywords=[kw for kw in training_keywords if kw in query_lower],
                urgency="normal",
                reasoning="Fallback: Training keywords detected"
            )
        
        # Default to base agent
        return QueryClassification(
            primary_agent=AgentType.BASE,
            confidence=0.5,
            keywords=[],
            urgency="normal",
            reasoning="Fallback: No specific keywords matched"
        )
    
    async def handle_query(
        self,
        query: str,
        conversation_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
        message_history: Optional[List[ModelMessage]] = None
    ) -> OrchestratorResponse:
        """Handle a query using the orchestrator"""
        
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        self.query_count += 1
        
        try:
            # Classify the query
            classification = await self.classify_query(query, context)
            
            # Get the appropriate agent
            agent = self._agents[classification.primary_agent]
            
            # Update usage stats
            self.agent_usage_stats[classification.primary_agent.value] += 1
            
            # Prepare context for the specialist agent
            specialist_context = self._prepare_specialist_context(
                classification.primary_agent, 
                context or {}
            )
            
            # Get response from specialist agent
            if classification.primary_agent == AgentType.BASE:
                # Convert context to QSRContext for base agent
                qsr_context = self._create_qsr_context_from_dict(specialist_context)
                response = await agent.process_query(
                    query=query,
                    context=qsr_context,
                    message_history=message_history or []
                )
            else:
                # Use the specialist method
                response = await self._call_specialist_method(
                    agent=agent,
                    query=query,
                    context=specialist_context,
                    message_history=message_history or []
                )
            
            # Calculate performance metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(response_time)
            
            return OrchestratorResponse(
                response=response.response if hasattr(response, 'response') else str(response),
                agent_used=classification.primary_agent,
                classification=classification,
                performance_metrics={
                    "response_time": response_time,
                    "query_count": self.query_count,
                    "agent_usage": self.agent_usage_stats.copy()
                },
                context_preserved=True,
                handoff_occurred=False
            )
            
        except Exception as e:
            self.logger.error(f"Error handling query: {e}")
            
            # Fallback to base agent
            if self.enable_fallback and classification.primary_agent != AgentType.BASE:
                try:
                    base_agent = self._agents[AgentType.BASE]
                    # Convert context to QSRContext for base agent
                    qsr_context = self._create_qsr_context_from_dict(context or {})
                    response = await base_agent.process_query(
                        query=query,
                        context=qsr_context,
                        message_history=message_history or []
                    )
                    
                    return OrchestratorResponse(
                        response=response.response,
                        agent_used=AgentType.BASE,
                        classification=classification,
                        performance_metrics={},
                        context_preserved=True,
                        handoff_occurred=True
                    )
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
            
            raise
    
    async def handle_query_stream(
        self,
        query: str,
        conversation_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
        message_history: Optional[List[ModelMessage]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle a query with streaming response using the orchestrator"""
        
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        self.query_count += 1
        
        try:
            # Classify the query
            classification = await self.classify_query(query, context)
            
            # Get the appropriate agent
            agent = self._agents[classification.primary_agent]
            
            # Update usage stats
            self.agent_usage_stats[classification.primary_agent.value] += 1
            
            # Prepare context for the specialist agent
            specialist_context = self._prepare_specialist_context(
                classification.primary_agent, 
                context or {}
            )
            
            # Stream response from specialist agent
            if classification.primary_agent == AgentType.BASE:
                async for chunk in agent.handle_query_stream(
                    query=query,
                    conversation_id=conversation_id,
                    context=specialist_context,
                    message_history=message_history or []
                ):
                    yield chunk
            else:
                # Use the specialist streaming method
                async for chunk in self._call_specialist_stream_method(
                    agent=agent,
                    query=query,
                    context=specialist_context,
                    message_history=message_history or []
                ):
                    yield chunk
            
            # Send final metadata chunk
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(response_time)
            
            yield {
                "chunk": "",
                "done": True,
                "metadata": {
                    "agent_used": classification.primary_agent.value,
                    "classification": classification.dict(),
                    "performance_metrics": {
                        "response_time": response_time,
                        "query_count": self.query_count,
                        "agent_usage": self.agent_usage_stats.copy()
                    },
                    "context_preserved": True,
                    "handoff_occurred": False
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in streaming query: {e}")
            
            # Fallback to base agent streaming
            if self.enable_fallback and classification.primary_agent != AgentType.BASE:
                try:
                    base_agent = self._agents[AgentType.BASE]
                    # Convert context to QSRContext for base agent
                    qsr_context = self._create_qsr_context_from_dict(context or {})
                    async for chunk in base_agent.process_query_stream(
                        query=query,
                        context=qsr_context,
                        message_history=message_history or []
                    ):
                        yield chunk
                except Exception as fallback_error:
                    self.logger.error(f"Streaming fallback failed: {fallback_error}")
                    yield {
                        "chunk": f"Error: {str(e)}",
                        "done": True,
                        "error": True
                    }
            else:
                yield {
                    "chunk": f"Error: {str(e)}",
                    "done": True,
                    "error": True
                }
    
    def _prepare_specialist_context(self, agent_type: AgentType, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context specific to the specialist agent type"""
        
        if agent_type == AgentType.EQUIPMENT:
            # Return a simple dict that can be converted by the agent
            return {
                "equipment_type": base_context.get("equipment_type", "unknown"),
                "model_number": base_context.get("model_number"),
                "error_codes": base_context.get("error_codes", []),
                "symptoms": base_context.get("symptoms", []),
                "last_maintenance": base_context.get("last_maintenance"),
                "location": base_context.get("location"),
                "urgency_level": base_context.get("urgency_level", "normal")
            }
            
        elif agent_type == AgentType.SAFETY:
            return SafetyContext(
                restaurant_info=base_context.get("restaurant_info", {}),
                current_incidents=base_context.get("safety_incidents", []),
                safety_training_status=base_context.get("training_status", {}),
                emergency_contacts=base_context.get("emergency_contacts", {}),
                user_role=base_context.get("user_role", "staff"),
                shift_info=base_context.get("shift_info", {}),
                timestamp=datetime.now()
            ).__dict__
            
        elif agent_type == AgentType.OPERATIONS:
            return OperationsContext(
                restaurant_info=base_context.get("restaurant_info", {}),
                current_shift=base_context.get("shift_info", {}),
                inventory_status=base_context.get("inventory", {}),
                staff_schedule=base_context.get("schedule", {}),
                quality_metrics=base_context.get("quality_data", {}),
                user_role=base_context.get("user_role", "staff"),
                timestamp=datetime.now()
            ).__dict__
            
        elif agent_type == AgentType.TRAINING:
            return TrainingContext(
                restaurant_info=base_context.get("restaurant_info", {}),
                employee_profile=base_context.get("employee_profile", {}),
                training_history=base_context.get("training_records", []),
                certification_status=base_context.get("certifications", {}),
                learning_preferences=base_context.get("learning_style", {}),
                user_role=base_context.get("user_role", "staff"),
                timestamp=datetime.now()
            ).__dict__
        
        # Base agent uses the original context
        return base_context
    
    def _create_qsr_context_from_dict(self, context_dict: Dict[str, Any]) -> QSRContext:
        """Convert dict context to QSRContext object"""
        return QSRContext(
            conversation_id=context_dict.get("conversation_id", "default"),
            user_location=context_dict.get("user_location"),
            equipment_context=context_dict.get("equipment_context", {}),
            safety_alerts=context_dict.get("safety_alerts", []),
            previous_queries=context_dict.get("previous_queries", [])
        )
    
    async def _call_specialist_method(
        self, 
        agent: Any, 
        query: str, 
        context: Dict[str, Any], 
        message_history: List[ModelMessage]
    ) -> Any:
        """Call the appropriate method on a specialist agent"""
        
        if hasattr(agent, 'handle_equipment_query'):
            return await agent.handle_equipment_query(query, context, message_history)
        elif hasattr(agent, 'handle_safety_query'):
            return await agent.handle_safety_query(query, context, message_history)
        elif hasattr(agent, 'handle_operations_query'):
            return await agent.handle_operations_query(query, context, message_history)
        elif hasattr(agent, 'handle_training_query'):
            return await agent.handle_training_query(query, context, message_history)
        else:
            # Fallback to base method if available
            if hasattr(agent, 'handle_query'):
                return await agent.handle_query(query, "default", context, message_history)
            else:
                raise ValueError(f"Agent {type(agent)} has no compatible query method")
    
    async def _call_specialist_stream_method(
        self, 
        agent: Any, 
        query: str, 
        context: Dict[str, Any], 
        message_history: List[ModelMessage]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Call the appropriate streaming method on a specialist agent"""
        
        if hasattr(agent, 'handle_equipment_query_stream'):
            async for chunk in agent.handle_equipment_query_stream(query, context, message_history):
                yield chunk
        elif hasattr(agent, 'handle_safety_query_stream'):
            async for chunk in agent.handle_safety_query_stream(query, context, message_history):
                yield chunk
        elif hasattr(agent, 'handle_operations_query_stream'):
            async for chunk in agent.handle_operations_query_stream(query, context, message_history):
                yield chunk
        elif hasattr(agent, 'handle_training_query_stream'):
            async for chunk in agent.handle_training_query_stream(query, context, message_history):
                yield chunk
        else:
            # Fallback to base streaming method if available
            if hasattr(agent, 'handle_query_stream'):
                async for chunk in agent.handle_query_stream(query, "default", context, message_history):
                    yield chunk
            else:
                raise ValueError(f"Agent {type(agent)} has no compatible streaming method")
    
    def _update_performance_metrics(self, response_time: float) -> None:
        """Update performance tracking metrics"""
        if not self.performance_tracking:
            return
            
        # Update average response time
        if self.query_count == 1:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                (self.average_response_time * (self.query_count - 1) + response_time) / 
                self.query_count
            )
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the orchestrator and all agents"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        health_status = {
            "orchestrator": {
                "status": "healthy",
                "initialized": self._initialized,
                "query_count": self.query_count,
                "average_response_time": self.average_response_time,
                "agent_usage_stats": self.agent_usage_stats.copy()
            },
            "agents": {}
        }
        
        # Check health of each agent
        for agent_type, agent in self._agents.items():
            try:
                if hasattr(agent, 'get_health_status'):
                    agent_health = await agent.get_health_status()
                else:
                    agent_health = {"status": "healthy", "method": "fallback"}
                
                health_status["agents"][agent_type.value] = agent_health
                
            except Exception as e:
                health_status["agents"][agent_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    @classmethod
    async def create(cls, **kwargs) -> 'QSROrchestrator':
        """Factory method to create and initialize orchestrator"""
        orchestrator = cls(**kwargs)
        await orchestrator.initialize()
        return orchestrator


# Global orchestrator cache for performance optimization
_orchestrator_cache = None
_cache_lock = asyncio.Lock()

async def get_cached_qsr_orchestrator(**kwargs) -> QSROrchestrator:
    """Get cached orchestrator instance for performance optimization"""
    global _orchestrator_cache
    
    async with _cache_lock:
        if _orchestrator_cache is None:
            logging.info("🚀 Creating and caching QSR orchestrator...")
            _orchestrator_cache = await QSROrchestrator.create(**kwargs)
            logging.info("✅ QSR orchestrator cached successfully")
        
        return _orchestrator_cache

# Factory function for easy instantiation
async def create_qsr_orchestrator(**kwargs) -> QSROrchestrator:
    """Create and initialize a QSR orchestrator instance"""
    return await get_cached_qsr_orchestrator(**kwargs)


if __name__ == "__main__":
    async def test_orchestrator():
        """Test the orchestrator with sample queries"""
        orchestrator = await create_qsr_orchestrator()
        
        test_queries = [
            "Taylor machine showing error E01",
            "Employee was burned by hot oil",
            "What's the opening procedure?",
            "How do I train a new employee?",
            "General QSR question"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            classification = await orchestrator.classify_query(query)
            print(f"Classification: {classification}")
            
            response = await orchestrator.handle_query(query)
            print(f"Response: {response.response[:100]}...")
            print(f"Agent Used: {response.agent_used}")
    
    asyncio.run(test_orchestrator())