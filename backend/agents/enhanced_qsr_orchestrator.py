#!/usr/bin/env python3
"""
Enhanced QSR Orchestrator with Ragie Integration
===============================================

Intelligent routing system with Ragie-powered specialist agents.
Combines the clean orchestration architecture with enhanced knowledge retrieval.

Features:
- Query classification with Ragie context awareness
- Ragie-enhanced specialist agents coordination
- Context preservation across agent handoffs
- Visual citation aggregation from multiple agents
- Performance monitoring and optimization

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior, ModelRetry
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic import BaseModel, Field

# Import shared types and enhanced agents
from .types import AgentType, QueryClassification, OrchestratorResponse
from .enhanced_qsr_base_agent import EnhancedQSRAgent, QSRResponse, QSRRunContext
from services.enhanced_ragie_service import enhanced_ragie_service, QSRContext

logger = logging.getLogger(__name__)

@dataclass
class EnhancedOrchestratorContext:
    """Enhanced context for orchestrator with Ragie integration"""
    conversation_id: str
    query_history: List[str] = field(default_factory=list)
    agent_usage_history: List[AgentType] = field(default_factory=list)
    equipment_context: Optional[str] = None
    procedure_context: Optional[str] = None
    safety_level: Optional[str] = None
    accumulated_citations: List[Dict[str, Any]] = field(default_factory=list)

class EnhancedQSROrchestrator:
    """Enhanced QSR Agent Orchestrator with Ragie knowledge integration"""
    
    def __init__(self):
        """Initialize enhanced orchestrator"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._agents: Dict[AgentType, Any] = {}
        self._initialized = False
        self.agent_usage_stats = {}
        self.contexts: Dict[str, EnhancedOrchestratorContext] = {}
        
        # Performance tracking
        self.response_times = []
        self.success_rate = {"successful": 0, "failed": 0}
        
        # Query classifier with Ragie awareness
        self._classifier = Agent(
            'openai:gpt-4o-mini',
            result_type=str,
            system_prompt=self._get_enhanced_classifier_prompt(),
            retries=2
        )
    
    async def initialize(self):
        """Initialize all enhanced agents with Ragie integration"""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Enhanced QSR Orchestrator with Ragie integration...")
            
            # Initialize enhanced base agent
            from .enhanced_qsr_base_agent import get_enhanced_qsr_agent
            self._agents[AgentType.BASE] = await get_enhanced_qsr_agent()
            
            # Create enhanced specialist agents (for now, use base agent)
            # In a full implementation, these would be specialized versions
            self._agents[AgentType.EQUIPMENT] = await get_enhanced_qsr_agent()
            self._agents[AgentType.SAFETY] = await get_enhanced_qsr_agent()
            self._agents[AgentType.OPERATIONS] = await get_enhanced_qsr_agent()
            self._agents[AgentType.TRAINING] = await get_enhanced_qsr_agent()
            
            # Initialize usage stats
            for agent_type in AgentType:
                self.agent_usage_stats[agent_type.value] = 0
                
            self._initialized = True
            self.logger.info("✅ Enhanced QSR Orchestrator initialized with Ragie integration")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced orchestrator: {e}")
            raise
    
    async def handle_query(
        self,
        query: str,
        conversation_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> OrchestratorResponse:
        """Handle query with enhanced Ragie integration"""
        start_time = datetime.now()
        
        try:
            # Ensure initialization
            if not self._initialized:
                await self.initialize()
            
            # Get or create conversation context
            if conversation_id not in self.contexts:
                self.contexts[conversation_id] = EnhancedOrchestratorContext(
                    conversation_id=conversation_id
                )
            
            conv_context = self.contexts[conversation_id]
            conv_context.query_history.append(query)
            
            self.logger.info(f"🎯 Enhanced orchestrator processing: {query[:100]}...")
            
            # Step 1: Classify query with Ragie context awareness
            classification = await self._classify_query_with_ragie_context(query, conv_context)
            
            # Step 2: Select and configure appropriate agent
            selected_agent_type = classification.primary_agent
            selected_agent = self._agents[selected_agent_type]
            
            # Step 3: Update context from classification (check if attributes exist)
            if hasattr(classification, 'equipment_mentioned') and classification.equipment_mentioned:
                conv_context.equipment_context = classification.equipment_mentioned[0]
            if hasattr(classification, 'procedure_detected') and classification.procedure_detected:
                conv_context.procedure_context = classification.procedure_detected
            if hasattr(classification, 'safety_critical') and classification.safety_critical:
                conv_context.safety_level = "high"
            
            # Step 4: Process query with enhanced agent
            response = await selected_agent.process_query(
                query=query,
                conversation_id=conversation_id,
                equipment_context=conv_context.equipment_context,
                procedure_context=conv_context.procedure_context
            )
            
            # Step 5: Aggregate visual citations
            conv_context.accumulated_citations.extend(response.visual_citations)
            
            # Step 6: Update usage stats
            self.agent_usage_stats[selected_agent_type.value] += 1
            conv_context.agent_usage_history.append(selected_agent_type)
            
            # Step 7: Calculate performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.response_times.append(processing_time)
            self.success_rate["successful"] += 1
            
            # Step 8: Create orchestrator response
            orchestrator_response = OrchestratorResponse(
                response=response.response,
                agent_used=selected_agent_type,
                classification=classification,
                performance_metrics={
                    "processing_time": processing_time,
                    "confidence": response.confidence_score,
                    "ragie_enhanced": response.ragie_enhanced,
                    "citation_count": len(response.visual_citations),
                    "query_length": len(query),
                    "conversation_length": len(conv_context.query_history),
                    "visual_citations": response.visual_citations,
                    "context_updates": {
                        "equipment_context": conv_context.equipment_context,
                        "procedure_context": conv_context.procedure_context,
                        "safety_level": conv_context.safety_level
                    }
                },
                context_preserved=True,
                handoff_occurred=False
            )
            
            self.logger.info(f"✅ Enhanced orchestrator completed in {processing_time:.2f}s with {len(response.visual_citations)} citations")
            return orchestrator_response
            
        except Exception as e:
            self.logger.error(f"Enhanced orchestrator error: {e}")
            self.success_rate["failed"] += 1
            
            # Fallback response with proper structure
            fallback_classification = QueryClassification(
                primary_agent=AgentType.BASE,
                confidence=0.2,
                reasoning="Error fallback"
            )
            
            return OrchestratorResponse(
                response="I encountered an issue processing your request. Please try rephrasing your question.",
                agent_used=AgentType.BASE,
                classification=fallback_classification,
                performance_metrics={
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "error": str(e)
                },
                context_preserved=False,
                handoff_occurred=False
            )
    
    async def _classify_query_with_ragie_context(
        self, 
        query: str, 
        conv_context: EnhancedOrchestratorContext
    ) -> QueryClassification:
        """Enhanced query classification with Ragie context awareness"""
        try:
            # Get Ragie context hints
            ragie_hints = await self._get_ragie_classification_hints(query)
            
            classification_prompt = f"""
Query: "{query}"

Conversation Context:
- Previous queries: {conv_context.query_history[-3:] if len(conv_context.query_history) > 1 else "None"}
- Equipment context: {conv_context.equipment_context or "None"}
- Procedure context: {conv_context.procedure_context or "None"}
- Previous agents used: {[a.value for a in conv_context.agent_usage_history[-3:]] if conv_context.agent_usage_history else "None"}

Ragie Knowledge Hints:
{ragie_hints}

Classify this query for optimal agent routing. Respond with JSON:
{{
    "primary_agent": "base|equipment|safety|operations|training",
    "confidence": 0.0-1.0,
    "equipment_mentioned": ["equipment1", "equipment2"],
    "procedure_detected": "cleaning|maintenance|troubleshooting|setup|safety|operations",
    "safety_critical": true/false,
    "urgency": "low|normal|high",
    "reasoning": "Brief explanation"
}}
"""

            result = await self._classifier.run(classification_prompt)
            
            # Parse classification
            import json
            try:
                # Handle potential JSON formatting issues
                result_text = result.data.strip()
                if not result_text.startswith('{'):
                    # If response doesn't start with JSON, extract JSON part
                    import re
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                    if json_match:
                        result_text = json_match.group()
                    else:
                        raise ValueError("No JSON found in response")
                
                classification_data = json.loads(result_text)
                
                # Handle potential enum value issues
                if isinstance(classification_data.get('primary_agent'), str):
                    # Fix agent value format issues
                    agent_value = classification_data['primary_agent'].split('|')[0].strip()
                    classification_data['primary_agent'] = agent_value
                
                classification = QueryClassification(**classification_data)
                return classification
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Classification parsing failed: {e}, using fallback")
                return self._fallback_classification(query, ragie_hints)
                
        except Exception as e:
            self.logger.error(f"Enhanced classification error: {e}")
            return self._fallback_classification(query)
    
    async def _get_ragie_classification_hints(self, query: str) -> str:
        """Get classification hints from Ragie knowledge"""
        try:
            # Quick Ragie search for classification hints
            qsr_context = enhanced_ragie_service._detect_qsr_context(query)
            
            hints = []
            if qsr_context.equipment_type:
                hints.append(f"Equipment detected: {qsr_context.equipment_type}")
            if qsr_context.procedure_type:
                hints.append(f"Procedure type: {qsr_context.procedure_type}")
            if qsr_context.safety_level:
                hints.append(f"Safety level: {qsr_context.safety_level}")
            
            return "; ".join(hints) if hints else "No specific QSR context detected"
            
        except Exception as e:
            self.logger.warning(f"Failed to get Ragie hints: {e}")
            return "Ragie hints unavailable"
    
    def _fallback_classification(self, query: str, ragie_hints: str = "") -> QueryClassification:
        """Fallback classification using keyword matching"""
        query_lower = query.lower()
        
        # Safety keywords (highest priority)
        if any(word in query_lower for word in ["emergency", "danger", "fire", "burn", "injury", "safety"]):
            return QueryClassification(
                primary_agent=AgentType.SAFETY,
                confidence=0.8,
                safety_critical=True,
                urgency="high",
                reasoning="Safety-related keywords detected"
            )
        
        # Equipment keywords
        equipment_keywords = ["fryer", "grill", "oven", "ice", "machine", "taylor", "grote", "mixer"]
        if any(word in query_lower for word in equipment_keywords):
            return QueryClassification(
                primary_agent=AgentType.EQUIPMENT,
                confidence=0.7,
                equipment_mentioned=[word for word in equipment_keywords if word in query_lower],
                reasoning="Equipment keywords detected"
            )
        
        # Operations keywords
        if any(word in query_lower for word in ["opening", "closing", "procedure", "operation", "shift"]):
            return QueryClassification(
                primary_agent=AgentType.OPERATIONS,
                confidence=0.6,
                procedure_detected="operations",
                reasoning="Operations keywords detected"
            )
        
        # Training keywords
        if any(word in query_lower for word in ["training", "learn", "how to", "teach", "guide"]):
            return QueryClassification(
                primary_agent=AgentType.TRAINING,
                confidence=0.6,
                reasoning="Training keywords detected"
            )
        
        # Default to base agent
        return QueryClassification(
            primary_agent=AgentType.BASE,
            confidence=0.5,
            reasoning="No specific keywords detected, using base agent"
        )
    
    def _get_enhanced_classifier_prompt(self) -> str:
        """Enhanced classifier prompt with Ragie awareness"""
        return """You are an intelligent query classifier for a QSR (Quick Service Restaurant) assistant system with access to comprehensive equipment manuals, safety protocols, and operational procedures.

Your task is to analyze queries and route them to the most appropriate specialist agent:

**EQUIPMENT AGENT**: Technical equipment issues, troubleshooting, maintenance
- Keywords: fryer, grill, oven, ice machine, mixer, Taylor, Grote, Vulcan, Hobart
- Examples: "fryer temperature issues", "ice machine maintenance", "mixer troubleshooting"

**SAFETY AGENT**: Safety protocols, emergency procedures, compliance
- Keywords: safety, danger, emergency, fire, burn, injury, HACCP, compliance
- Examples: "fire safety procedures", "burn treatment", "safety training"

**OPERATIONS AGENT**: Daily operations, procedures, shift management
- Keywords: opening, closing, shift, procedure, operation, workflow
- Examples: "opening procedures", "shift handoff", "daily operations"

**TRAINING AGENT**: Learning, guidance, step-by-step instructions
- Keywords: training, learn, how to, teach, guide, instruction
- Examples: "how to clean equipment", "training new employees"

**BASE AGENT**: General questions, complex queries requiring multiple specialties

Consider:
1. Conversation context and previous agent usage
2. Ragie knowledge hints about equipment and procedures
3. Safety criticality and urgency levels
4. User intent and expected response type

Respond with structured classification data only."""

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics"""
        total_requests = self.success_rate["successful"] + self.success_rate["failed"]
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "total_requests": total_requests,
            "success_rate": self.success_rate["successful"] / max(total_requests, 1),
            "average_response_time": avg_response_time,
            "agent_usage": self.agent_usage_stats,
            "ragie_integration": "active",
            "conversations_active": len(self.contexts)
        }

# Global enhanced orchestrator instance
enhanced_qsr_orchestrator = None

async def get_enhanced_qsr_orchestrator() -> EnhancedQSROrchestrator:
    """Get or create global enhanced orchestrator instance"""
    global enhanced_qsr_orchestrator
    if enhanced_qsr_orchestrator is None:
        enhanced_qsr_orchestrator = EnhancedQSROrchestrator()
        await enhanced_qsr_orchestrator.initialize()
    return enhanced_qsr_orchestrator