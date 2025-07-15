"""
Agent Tool Integration for PydanticAI Multi-Agent System
======================================================

Integrates QSR-specific PydanticAI tools with the existing multi-agent architecture
while preserving all existing functionality and services.

This module provides the bridge between:
- PydanticAI Agent instances with tools
- Existing QSR services (MultiModalCitationService, VoiceGraphService, etc.)
- Enhanced QSR response models
- Conversation context management

Author: Generated with Memex (https://memex.tech)
"""

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Callable, Union
import logging
import asyncio
import time
from datetime import datetime

# Import existing services and models
try:
    from voice_agent import (
        VoiceResponse, ConversationContext, AgentType, 
        SpecializedAgentResponse, VoiceState, ConversationIntent
    )
    from models.enhanced_qsr_models import (
        EnhancedQSRResponse, QSRResponseFactory, EnhancedVisualCitation,
        VisualCitationCollection, EquipmentContext
    )
    from tools.qsr_pydantic_tools import (
        VisualCitationTool, GraphRAGEquipmentTool, ProcedureNavigationTool,
        SafetyValidationTool, ContextEnhancementTool, QSRToolContext,
        VisualCitationQuery, GraphRAGQuery, ProcedureNavigationQuery,
        SafetyValidationQuery, ContextEnhancementQuery
    )
    
    # Import existing services
    from services.multimodal_citation_service import MultiModalCitationService
    from services.voice_graph_service import VoiceGraphService
    from services.neo4j_service import Neo4jService
    from services.enhanced_citation_service import EnhancedCitationService
    
    INTEGRATION_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Agent tool integration dependencies loaded successfully")
    
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Some integration dependencies not available: {e}")
    INTEGRATION_AVAILABLE = False

# ===============================================================================
# TOOL-ENHANCED AGENT CONTEXT
# ===============================================================================

class ToolEnhancedAgentContext(BaseModel):
    """Enhanced agent context that includes tool capabilities"""
    
    # Agent identification
    agent_type: AgentType
    agent_name: str
    session_id: str
    
    # Tool context
    tool_context: QSRToolContext
    available_tools: Dict[str, Any] = Field(default_factory=dict)
    tool_usage_history: Dict[str, int] = Field(default_factory=dict)
    
    # Performance tracking
    tool_call_count: int = 0
    total_tool_time_ms: float = 0.0
    successful_tool_calls: int = 0
    
    # Conversation integration
    conversation_context: Optional[ConversationContext] = None
    last_tool_results: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

# ===============================================================================
# AGENT TOOL COORDINATOR
# ===============================================================================

class AgentToolCoordinator:
    """
    Coordinates tool usage across multiple PydanticAI agents while preserving
    existing service functionality and conversation context.
    """
    
    def __init__(self, 
                 multimodal_service: Optional[MultiModalCitationService] = None,
                 voice_graph_service: Optional[VoiceGraphService] = None,
                 neo4j_service: Optional[Neo4jService] = None,
                 enhanced_citation_service: Optional[EnhancedCitationService] = None):
        
        self.logger = logging.getLogger(f"{__name__}.AgentToolCoordinator")
        
        # Store existing services
        self.services = {
            'multimodal': multimodal_service,
            'voice_graph': voice_graph_service,
            'neo4j': neo4j_service,
            'enhanced_citation': enhanced_citation_service
        }
        
        # Agent contexts by session
        self.agent_contexts: Dict[str, ToolEnhancedAgentContext] = {}
        
        # Global tool performance tracking
        self.global_tool_metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'average_response_time': 0.0,
            'tool_popularity': {}
        }
    
    def create_tool_context(self, 
                          session_id: str,
                          conversation_context: Optional[ConversationContext] = None,
                          uploaded_docs_path: str = "uploaded_docs") -> QSRToolContext:
        """Create tool context with existing services injected"""
        
        return QSRToolContext(
            multimodal_citation_service=self.services['multimodal'],
            voice_graph_service=self.services['voice_graph'],
            neo4j_service=self.services['neo4j'],
            enhanced_citation_service=self.services['enhanced_citation'],
            conversation_context=conversation_context,
            session_id=session_id,
            uploaded_docs_path=uploaded_docs_path,
            enable_visual_citations=True,
            enable_graph_context=True
        )
    
    def setup_agent_with_tools(self, 
                             agent_type: AgentType,
                             session_id: str,
                             conversation_context: Optional[ConversationContext] = None) -> ToolEnhancedAgentContext:
        """Setup agent with appropriate tools for its specialization"""
        
        # Create tool context
        tool_context = self.create_tool_context(session_id, conversation_context)
        
        # Create available tools based on agent type
        available_tools = self._create_tools_for_agent(agent_type, tool_context)
        
        # Create enhanced agent context
        agent_context = ToolEnhancedAgentContext(
            agent_type=agent_type,
            agent_name=f"{agent_type.value}_agent",
            session_id=session_id,
            tool_context=tool_context,
            available_tools=available_tools,
            conversation_context=conversation_context
        )
        
        # Store in session contexts
        context_key = f"{session_id}_{agent_type.value}"
        self.agent_contexts[context_key] = agent_context
        
        self.logger.info(f"Setup {agent_type.value} agent with {len(available_tools)} tools for session {session_id}")
        
        return agent_context
    
    def _create_tools_for_agent(self, agent_type: AgentType, tool_context: QSRToolContext) -> Dict[str, Any]:
        """Create appropriate tools for agent type"""
        
        tools = {}
        
        # Core tools for all agents
        tools['visual_citations'] = VisualCitationTool(tool_context)
        tools['context_enhancement'] = ContextEnhancementTool(tool_context)
        
        # Specialized tools by agent type
        if agent_type in [AgentType.EQUIPMENT, AgentType.GENERAL]:
            tools['graph_rag'] = GraphRAGEquipmentTool(tool_context)
        
        if agent_type in [AgentType.PROCEDURE, AgentType.MAINTENANCE, AgentType.GENERAL]:
            tools['procedure_navigation'] = ProcedureNavigationTool(tool_context)
        
        # Safety tool for safety-critical agents
        if agent_type in [AgentType.SAFETY, AgentType.EQUIPMENT, AgentType.PROCEDURE, AgentType.MAINTENANCE]:
            tools['safety_validation'] = SafetyValidationTool(tool_context)
        
        return tools
    
    async def execute_tool_for_agent(self,
                                   agent_type: AgentType,
                                   session_id: str,
                                   tool_name: str,
                                   tool_query: BaseModel,
                                   conversation_context: Optional[ConversationContext] = None) -> Dict[str, Any]:
        """Execute a specific tool for an agent with performance tracking"""
        
        start_time = time.time()
        context_key = f"{session_id}_{agent_type.value}"
        
        try:
            # Get or create agent context
            if context_key not in self.agent_contexts:
                self.setup_agent_with_tools(agent_type, session_id, conversation_context)
            
            agent_context = self.agent_contexts[context_key]
            
            # Check if tool is available for this agent
            if tool_name not in agent_context.available_tools:
                raise ValueError(f"Tool {tool_name} not available for {agent_type.value} agent")
            
            tool = agent_context.available_tools[tool_name]
            
            # Execute tool based on type
            result = await self._execute_specific_tool(tool, tool_name, tool_query)
            
            # Update performance metrics
            execution_time = (time.time() - start_time) * 1000
            await self._update_tool_metrics(agent_context, tool_name, execution_time, True)
            
            # Store results in agent context
            agent_context.last_tool_results[tool_name] = result
            
            self.logger.info(f"Successfully executed {tool_name} for {agent_type.value} agent in {execution_time:.2f}ms")
            
            return {
                'tool_name': tool_name,
                'result': result,
                'execution_time_ms': execution_time,
                'success': True
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Update metrics for failed call
            if context_key in self.agent_contexts:
                await self._update_tool_metrics(self.agent_contexts[context_key], tool_name, execution_time, False)
            
            self.logger.error(f"Tool execution failed for {tool_name} on {agent_type.value} agent: {e}")
            
            return {
                'tool_name': tool_name,
                'result': None,
                'execution_time_ms': execution_time,
                'success': False,
                'error': str(e)
            }
    
    async def _execute_specific_tool(self, tool: Any, tool_name: str, query: BaseModel) -> Any:
        """Execute a specific tool with its appropriate query"""
        
        if tool_name == 'visual_citations' and isinstance(tool, VisualCitationTool):
            return await tool.search_visual_citations(query)
        elif tool_name == 'graph_rag' and isinstance(tool, GraphRAGEquipmentTool):
            return await tool.query_equipment_context(query)
        elif tool_name == 'procedure_navigation' and isinstance(tool, ProcedureNavigationTool):
            return await tool.navigate_procedure(query)
        elif tool_name == 'safety_validation' and isinstance(tool, SafetyValidationTool):
            return await tool.validate_safety(query)
        elif tool_name == 'context_enhancement' and isinstance(tool, ContextEnhancementTool):
            return await tool.enhance_context(query)
        else:
            raise ValueError(f"Unknown tool type: {tool_name}")
    
    async def _update_tool_metrics(self, 
                                 agent_context: ToolEnhancedAgentContext,
                                 tool_name: str,
                                 execution_time: float,
                                 success: bool):
        """Update tool performance metrics"""
        
        # Update agent context metrics
        agent_context.tool_call_count += 1
        agent_context.total_tool_time_ms += execution_time
        
        if success:
            agent_context.successful_tool_calls += 1
        
        # Update tool usage history
        agent_context.tool_usage_history[tool_name] = agent_context.tool_usage_history.get(tool_name, 0) + 1
        
        # Update global metrics
        self.global_tool_metrics['total_calls'] += 1
        if success:
            self.global_tool_metrics['successful_calls'] += 1
        
        # Update average response time
        total_time = self.global_tool_metrics.get('total_time', 0.0) + execution_time
        self.global_tool_metrics['total_time'] = total_time
        self.global_tool_metrics['average_response_time'] = total_time / self.global_tool_metrics['total_calls']
        
        # Update tool popularity
        self.global_tool_metrics['tool_popularity'][tool_name] = self.global_tool_metrics['tool_popularity'].get(tool_name, 0) + 1

# ===============================================================================
# ENHANCED AGENT RESPONSE INTEGRATION
# ===============================================================================

class ToolEnhancedResponseBuilder:
    """
    Builds enhanced responses by integrating tool results with existing
    VoiceResponse and SpecializedAgentResponse structures.
    """
    
    def __init__(self, coordinator: AgentToolCoordinator):
        self.coordinator = coordinator
        self.logger = logging.getLogger(f"{__name__}.ToolEnhancedResponseBuilder")
    
    async def build_enhanced_response(self,
                                    agent_type: AgentType,
                                    session_id: str,
                                    base_response: Union[VoiceResponse, SpecializedAgentResponse],
                                    query_text: str,
                                    conversation_context: Optional[ConversationContext] = None,
                                    auto_enhance: bool = True) -> EnhancedQSRResponse:
        """Build enhanced response by integrating tool results with base response"""
        
        try:
            # Get agent context
            context_key = f"{session_id}_{agent_type.value}"
            if context_key not in self.coordinator.agent_contexts:
                self.coordinator.setup_agent_with_tools(agent_type, session_id, conversation_context)
            
            agent_context = self.coordinator.agent_contexts[context_key]
            
            # Prepare base response data
            base_response_data = self._extract_base_response_data(base_response)
            
            # Auto-enhance with tools if requested
            tool_results = {}
            if auto_enhance:
                tool_results = await self._auto_enhance_with_tools(
                    agent_context, query_text, base_response_data
                )
            
            # Integrate tool results
            enhanced_data = await self._integrate_tool_results(base_response_data, tool_results)
            
            # Create enhanced response using factory
            enhanced_response = QSRResponseFactory.create_response(
                agent_type=agent_type,
                base_response_data=enhanced_data,
                visual_citations=enhanced_data.get('enhanced_citations'),
                equipment_context=enhanced_data.get('equipment_context')
            )
            
            self.logger.info(f"Built enhanced response for {agent_type.value} with {len(tool_results)} tool integrations")
            
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"Enhanced response building failed: {e}")
            
            # Fallback: Convert base response to enhanced format
            return self._create_fallback_enhanced_response(agent_type, base_response)
    
    def _extract_base_response_data(self, base_response: Union[VoiceResponse, SpecializedAgentResponse]) -> Dict[str, Any]:
        """Extract data from base response for enhancement"""
        
        if isinstance(base_response, VoiceResponse):
            return {
                'text_response': base_response.text_response,
                'audio_data': base_response.audio_data,
                'should_continue_listening': base_response.should_continue_listening,
                'next_voice_state': base_response.next_voice_state,
                'detected_intent': base_response.detected_intent,
                'context_updates': base_response.context_updates,
                'conversation_complete': base_response.conversation_complete,
                'confidence_score': base_response.confidence_score,
                'suggested_follow_ups': base_response.suggested_follow_ups,
                'safety_priority': getattr(base_response, 'safety_priority', False),
                'response_type': getattr(base_response, 'response_type', 'factual'),
                'primary_agent': getattr(base_response, 'primary_agent', AgentType.GENERAL),
                'contributing_agents': getattr(base_response, 'contributing_agents', []),
                'coordination_strategy': getattr(base_response, 'coordination_strategy', 'single_agent'),
                'agent_confidence_scores': getattr(base_response, 'agent_confidence_scores', {}),
                'specialized_insights': getattr(base_response, 'specialized_insights', {})
            }
        
        elif isinstance(base_response, SpecializedAgentResponse):
            return {
                'text_response': base_response.response_text,
                'confidence_score': base_response.confidence_score,
                'primary_agent': base_response.agent_type,
                'specialized_insights': base_response.specialized_insights,
                'safety_priority': len(base_response.safety_alerts) > 0,
                'detected_intent': ConversationIntent.NEW_TOPIC,  # Default
                'should_continue_listening': True,
                'next_voice_state': VoiceState.LISTENING,
                'context_updates': {},
                'conversation_complete': False,
                'suggested_follow_ups': []
            }
        
        else:
            # Unknown response type - create minimal data
            return {
                'text_response': str(base_response),
                'confidence_score': 0.8,
                'detected_intent': ConversationIntent.NEW_TOPIC,
                'should_continue_listening': True,
                'next_voice_state': VoiceState.LISTENING,
                'context_updates': {},
                'conversation_complete': False,
                'suggested_follow_ups': []
            }
    
    async def _auto_enhance_with_tools(self,
                                     agent_context: ToolEnhancedAgentContext,
                                     query_text: str,
                                     base_response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically enhance response with appropriate tools"""
        
        tool_results = {}
        
        # Always try to enhance with visual citations
        if 'visual_citations' in agent_context.available_tools:
            try:
                citation_query = VisualCitationQuery(
                    query_text=query_text,
                    safety_critical=base_response_data.get('safety_priority', False),
                    max_results=5
                )
                
                citation_result = await self.coordinator.execute_tool_for_agent(
                    agent_context.agent_type,
                    agent_context.session_id,
                    'visual_citations',
                    citation_query,
                    agent_context.conversation_context
                )
                
                if citation_result['success']:
                    tool_results['visual_citations'] = citation_result['result']
                    
            except Exception as e:
                self.logger.warning(f"Visual citation enhancement failed: {e}")
        
        # Enhance with Graph-RAG for equipment-related queries
        if 'graph_rag' in agent_context.available_tools and self._is_equipment_query(query_text):
            try:
                graph_query = GraphRAGQuery(
                    query_context=query_text,
                    include_relationships=True,
                    max_depth=2
                )
                
                graph_result = await self.coordinator.execute_tool_for_agent(
                    agent_context.agent_type,
                    agent_context.session_id,
                    'graph_rag',
                    graph_query,
                    agent_context.conversation_context
                )
                
                if graph_result['success']:
                    tool_results['graph_rag'] = graph_result['result']
                    
            except Exception as e:
                self.logger.warning(f"Graph-RAG enhancement failed: {e}")
        
        # Enhance with safety validation for safety-critical content
        if 'safety_validation' in agent_context.available_tools and base_response_data.get('safety_priority', False):
            try:
                safety_query = SafetyValidationQuery(
                    content_to_validate=base_response_data['text_response'],
                    context_critical=True
                )
                
                safety_result = await self.coordinator.execute_tool_for_agent(
                    agent_context.agent_type,
                    agent_context.session_id,
                    'safety_validation',
                    safety_query,
                    agent_context.conversation_context
                )
                
                if safety_result['success']:
                    tool_results['safety_validation'] = safety_result['result']
                    
            except Exception as e:
                self.logger.warning(f"Safety validation enhancement failed: {e}")
        
        # Always enhance context
        if 'context_enhancement' in agent_context.available_tools:
            try:
                context_query = ContextEnhancementQuery(
                    current_query=query_text,
                    session_id=agent_context.session_id
                )
                
                context_result = await self.coordinator.execute_tool_for_agent(
                    agent_context.agent_type,
                    agent_context.session_id,
                    'context_enhancement',
                    context_query,
                    agent_context.conversation_context
                )
                
                if context_result['success']:
                    tool_results['context_enhancement'] = context_result['result']
                    
            except Exception as e:
                self.logger.warning(f"Context enhancement failed: {e}")
        
        return tool_results
    
    def _is_equipment_query(self, query_text: str) -> bool:
        """Check if query is equipment-related"""
        equipment_keywords = [
            'fryer', 'oven', 'grill', 'compressor', 'refrigerator',
            'freezer', 'equipment', 'machine', 'taylor', 'c602'
        ]
        
        query_lower = query_text.lower()
        return any(keyword in query_lower for keyword in equipment_keywords)
    
    async def _integrate_tool_results(self, base_data: Dict[str, Any], tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate tool results into base response data"""
        
        enhanced_data = base_data.copy()
        
        # Integrate visual citations
        if 'visual_citations' in tool_results:
            citation_result = tool_results['visual_citations']
            enhanced_data['visual_citations'] = citation_result.citations
            enhanced_data['enhanced_citations'] = citation_result.enhanced_citations
            enhanced_data['citation_count'] = citation_result.total_found
        
        # Integrate Graph-RAG context
        if 'graph_rag' in tool_results:
            graph_result = tool_results['graph_rag']
            enhanced_data['equipment_context'] = graph_result.equipment_context
            enhanced_data['graph_entities'] = graph_result.entities
            enhanced_data['graph_relationships'] = graph_result.relationships
        
        # Integrate safety validation
        if 'safety_validation' in tool_results:
            safety_result = tool_results['safety_validation']
            enhanced_data['safety_warnings'] = safety_result.safety_warnings
            enhanced_data['compliance_requirements'] = safety_result.compliance_requirements
            enhanced_data['safety_priority'] = not safety_result.safety_compliant
        
        # Integrate context enhancement
        if 'context_enhancement' in tool_results:
            context_result = tool_results['context_enhancement']
            enhanced_data['context_score'] = context_result.context_score
            enhanced_data['equipment_continuity'] = context_result.equipment_continuity
            enhanced_data['topic_continuity'] = context_result.topic_continuity
        
        return enhanced_data
    
    def _create_fallback_enhanced_response(self, agent_type: AgentType, base_response: Any) -> EnhancedQSRResponse:
        """Create fallback enhanced response when tool integration fails"""
        
        if hasattr(base_response, 'to_enhanced_response'):
            return base_response.to_enhanced_response()
        
        # Create minimal enhanced response
        return EnhancedQSRResponse(
            text_response=str(base_response),
            confidence_score=0.8,
            detected_intent=ConversationIntent.NEW_TOPIC,
            primary_agent=agent_type,
            should_continue_listening=True,
            next_voice_state=VoiceState.LISTENING,
            context_updates={},
            conversation_complete=False,
            suggested_follow_ups=[]
        )

# ===============================================================================
# INTEGRATION UTILITIES
# ===============================================================================

async def create_tool_enhanced_agent_system(
    multimodal_service: Optional[MultiModalCitationService] = None,
    voice_graph_service: Optional[VoiceGraphService] = None,
    neo4j_service: Optional[Neo4jService] = None,
    enhanced_citation_service: Optional[EnhancedCitationService] = None
) -> tuple[AgentToolCoordinator, ToolEnhancedResponseBuilder]:
    """Create complete tool-enhanced agent system with existing services"""
    
    # Create coordinator with existing services
    coordinator = AgentToolCoordinator(
        multimodal_service=multimodal_service,
        voice_graph_service=voice_graph_service,
        neo4j_service=neo4j_service,
        enhanced_citation_service=enhanced_citation_service
    )
    
    # Create response builder
    response_builder = ToolEnhancedResponseBuilder(coordinator)
    
    return coordinator, response_builder

def get_tool_enhanced_agent_capabilities() -> Dict[str, List[str]]:
    """Get mapping of agent types to their tool capabilities"""
    
    return {
        'equipment': ['visual_citations', 'graph_rag', 'safety_validation', 'context_enhancement'],
        'procedure': ['visual_citations', 'procedure_navigation', 'safety_validation', 'context_enhancement'],
        'safety': ['visual_citations', 'safety_validation', 'context_enhancement'],
        'maintenance': ['visual_citations', 'procedure_navigation', 'safety_validation', 'context_enhancement'],
        'general': ['visual_citations', 'graph_rag', 'procedure_navigation', 'context_enhancement']
    }

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Core integration classes
    "AgentToolCoordinator",
    "ToolEnhancedResponseBuilder",
    "ToolEnhancedAgentContext",
    
    # Utility functions
    "create_tool_enhanced_agent_system",
    "get_tool_enhanced_agent_capabilities"
]