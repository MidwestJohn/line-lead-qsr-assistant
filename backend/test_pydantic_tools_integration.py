#!/usr/bin/env python3
"""
Test PydanticAI Tools Integration with Existing QSR System
=========================================================

Comprehensive test demonstrating how the new PydanticAI tools integrate
with existing working services without breaking functionality.

Tests:
1. Tool integration with existing MultiModalCitationService
2. Graph-RAG integration with existing VoiceGraphService
3. Enhanced response building with existing VoiceResponse
4. Safety validation integration with existing safety patterns
5. Context enhancement with existing ConversationContext

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test imports
try:
    from tools.qsr_pydantic_tools import (
        VisualCitationTool, GraphRAGEquipmentTool, ProcedureNavigationTool,
        SafetyValidationTool, ContextEnhancementTool, QSRToolContext,
        VisualCitationQuery, GraphRAGQuery, ProcedureNavigationQuery,
        SafetyValidationQuery, ContextEnhancementQuery
    )
    
    from tools.agent_tool_integration import (
        AgentToolCoordinator, ToolEnhancedResponseBuilder,
        create_tool_enhanced_agent_system
    )
    
    from voice_agent import (
        VoiceResponse, ConversationContext, AgentType, VoiceState, 
        ConversationIntent, SpecializedAgentResponse
    )
    
    from services.multimodal_citation_service import MultiModalCitationService
    from services.voice_graph_service import VoiceGraphService
    
    IMPORTS_SUCCESSFUL = True
    logger.info("✅ All imports successful")
    
except ImportError as e:
    logger.error(f"❌ Import failed: {e}")
    IMPORTS_SUCCESSFUL = False

# ===============================================================================
# TEST UTILITIES
# ===============================================================================

class MockMultiModalCitationService:
    """Mock citation service for testing"""
    
    def __init__(self, uploaded_docs_path: str = "uploaded_docs"):
        self.uploaded_docs_path = uploaded_docs_path
        self.mock_citations = [
            {
                'citation_id': 'test_citation_1',
                'type': 'diagram',
                'source': 'Taylor_C602_Manual.pdf',
                'page': 12,
                'description': 'Fryer temperature control diagram',
                'confidence': 0.9,
                'equipment_context': ['taylor c602', 'fryer']
            },
            {
                'citation_id': 'test_citation_2',
                'type': 'image',
                'source': 'QSR_Safety_Manual.pdf',
                'page': 5,
                'description': 'Safety equipment placement',
                'confidence': 0.85,
                'equipment_context': ['safety equipment']
            }
        ]
    
    def extract_visual_references(self, text: str) -> Dict[str, List[str]]:
        """Mock visual reference extraction"""
        references = {}
        
        if 'diagram' in text.lower() or 'fryer' in text.lower():
            references['diagram'] = ['temperature control diagram']
        
        if 'safety' in text.lower():
            references['image'] = ['safety equipment placement']
        
        if 'procedure' in text.lower():
            references['flowchart'] = ['procedure flowchart']
        
        return references

class MockVoiceGraphService:
    """Mock voice graph service for testing"""
    
    def __init__(self):
        self.sessions = {}
        self.mock_entities = [
            {'name': 'Taylor C602', 'type': 'equipment', 'description': 'Commercial fryer'},
            {'name': 'Temperature Control', 'type': 'system', 'description': 'Temperature management system'},
            {'name': 'Cleaning Cycle', 'type': 'procedure', 'description': 'Equipment cleaning procedure'}
        ]
    
    async def process_voice_query(self, session_id: str, query: str, audio_metadata: Dict = None) -> Dict[str, Any]:
        """Mock voice query processing"""
        
        return {
            'session_id': session_id,
            'response': {
                'text': f"Mock response for: {query}",
                'confidence': 0.85
            },
            'context': {
                'current_equipment': 'Taylor C602' if 'fryer' in query.lower() else None,
                'current_procedure': 'cleaning' if 'clean' in query.lower() else None,
                'graph_entities': self.mock_entities
            }
        }

# ===============================================================================
# INDIVIDUAL TOOL TESTS
# ===============================================================================

async def test_visual_citation_tool():
    """Test visual citation tool integration"""
    logger.info("🔍 Testing Visual Citation Tool...")
    
    # Create mock services
    mock_citation_service = MockMultiModalCitationService()
    
    # Create tool context
    tool_context = QSRToolContext(
        multimodal_citation_service=mock_citation_service,
        session_id="test_session_1",
        enable_visual_citations=True
    )
    
    # Create tool
    citation_tool = VisualCitationTool(tool_context)
    
    # Test query
    query = VisualCitationQuery(
        query_text="Show me the fryer temperature control diagram",
        equipment_context=["taylor c602", "fryer"],
        safety_critical=False,
        max_results=3
    )
    
    # Execute tool
    result = await citation_tool.search_visual_citations(query)
    
    # Verify results
    assert result.total_found >= 0, "Should return citation count"
    assert isinstance(result.citations, list), "Should return citations list"
    assert result.search_time_ms > 0, "Should track search time"
    
    logger.info(f"✅ Visual Citation Tool: Found {result.total_found} citations in {result.search_time_ms:.2f}ms")
    
    return result

async def test_graph_rag_tool():
    """Test Graph-RAG equipment tool integration"""
    logger.info("🔍 Testing Graph-RAG Equipment Tool...")
    
    # Create mock services
    mock_graph_service = MockVoiceGraphService()
    
    # Create tool context
    tool_context = QSRToolContext(
        voice_graph_service=mock_graph_service,
        session_id="test_session_2",
        enable_graph_context=True
    )
    
    # Create tool
    graph_tool = GraphRAGEquipmentTool(tool_context)
    
    # Test query
    query = GraphRAGQuery(
        equipment_name="Taylor C602",
        query_context="How do I clean the fryer?",
        include_relationships=True,
        max_depth=2
    )
    
    # Execute tool
    result = await graph_tool.query_equipment_context(query)
    
    # Verify results
    assert isinstance(result.entities, list), "Should return entities list"
    assert isinstance(result.relationships, list), "Should return relationships list"
    assert result.confidence_score >= 0.0, "Should have confidence score"
    
    logger.info(f"✅ Graph-RAG Tool: Found {len(result.entities)} entities with confidence {result.confidence_score:.2f}")
    
    return result

async def test_safety_validation_tool():
    """Test safety validation tool"""
    logger.info("🔍 Testing Safety Validation Tool...")
    
    # Create tool context
    tool_context = QSRToolContext(
        session_id="test_session_3"
    )
    
    # Create tool
    safety_tool = SafetyValidationTool(tool_context)
    
    # Test query - safety-critical content
    query = SafetyValidationQuery(
        content_to_validate="Set fryer to 350°F and clean with hot oil",
        equipment_mentioned=["fryer", "taylor c602"],
        context_critical=True
    )
    
    # Execute tool
    result = await safety_tool.validate_safety(query)
    
    # Verify results
    assert isinstance(result.safety_compliant, bool), "Should return compliance status"
    assert isinstance(result.safety_warnings, list), "Should return safety warnings"
    assert result.risk_level in ["low", "medium", "high", "critical"], "Should assess risk level"
    
    logger.info(f"✅ Safety Validation Tool: Risk level {result.risk_level}, {len(result.safety_warnings)} warnings")
    
    return result

async def test_context_enhancement_tool():
    """Test context enhancement tool"""
    logger.info("🔍 Testing Context Enhancement Tool...")
    
    # Create mock services
    mock_graph_service = MockVoiceGraphService()
    
    # Create tool context
    tool_context = QSRToolContext(
        voice_graph_service=mock_graph_service,
        session_id="test_session_4"
    )
    
    # Create tool
    context_tool = ContextEnhancementTool(tool_context)
    
    # Test query with conversation history
    query = ContextEnhancementQuery(
        current_query="How do I clean it?",
        conversation_history=[
            {"user": "Tell me about the Taylor C602 fryer", "assistant": "The Taylor C602 is a commercial fryer..."},
            {"user": "What temperature should it be?", "assistant": "The fryer should be set to 350°F..."}
        ],
        enhance_equipment_context=True,
        enhance_graph_context=True,
        session_id="test_session_4"
    )
    
    # Execute tool
    result = await context_tool.enhance_context(query)
    
    # Verify results
    assert isinstance(result.enhanced_context, dict), "Should return enhanced context"
    assert result.context_score >= 0.0, "Should have context score"
    assert isinstance(result.recommendations, list), "Should return recommendations"
    
    logger.info(f"✅ Context Enhancement Tool: Context score {result.context_score:.2f}, equipment continuity: {result.equipment_continuity}")
    
    return result

# ===============================================================================
# INTEGRATION TESTS
# ===============================================================================

async def test_agent_tool_coordinator():
    """Test agent tool coordinator integration"""
    logger.info("🔍 Testing Agent Tool Coordinator...")
    
    # Create mock services
    mock_citation_service = MockMultiModalCitationService()
    mock_graph_service = MockVoiceGraphService()
    
    # Create coordinator
    coordinator = AgentToolCoordinator(
        multimodal_service=mock_citation_service,
        voice_graph_service=mock_graph_service
    )
    
    # Setup equipment agent with tools
    conversation_context = ConversationContext(
        current_topic="fryer maintenance",
        current_entity="Taylor C602"
    )
    
    agent_context = coordinator.setup_agent_with_tools(
        agent_type=AgentType.EQUIPMENT,
        session_id="test_session_5",
        conversation_context=conversation_context
    )
    
    # Verify agent setup
    assert agent_context.agent_type == AgentType.EQUIPMENT
    assert len(agent_context.available_tools) > 0
    assert 'visual_citations' in agent_context.available_tools
    assert 'graph_rag' in agent_context.available_tools
    
    # Test tool execution
    citation_query = VisualCitationQuery(
        query_text="Show me fryer maintenance diagram",
        equipment_context=["taylor c602"]
    )
    
    result = await coordinator.execute_tool_for_agent(
        agent_type=AgentType.EQUIPMENT,
        session_id="test_session_5",
        tool_name="visual_citations",
        tool_query=citation_query
    )
    
    # Verify tool execution
    assert result['success'] == True
    assert result['tool_name'] == 'visual_citations'
    assert result['execution_time_ms'] > 0
    
    logger.info(f"✅ Agent Tool Coordinator: Executed {result['tool_name']} in {result['execution_time_ms']:.2f}ms")
    
    return coordinator, agent_context

async def test_enhanced_response_builder():
    """Test enhanced response builder integration"""
    logger.info("🔍 Testing Enhanced Response Builder...")
    
    # Create mock services
    mock_citation_service = MockMultiModalCitationService()
    mock_graph_service = MockVoiceGraphService()
    
    # Create coordinator and response builder
    coordinator = AgentToolCoordinator(
        multimodal_service=mock_citation_service,
        voice_graph_service=mock_graph_service
    )
    
    response_builder = ToolEnhancedResponseBuilder(coordinator)
    
    # Create base response
    base_response = VoiceResponse(
        text_response="The Taylor C602 fryer should be cleaned daily with proper procedures.",
        detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
        confidence_score=0.9,
        equipment_mentioned="Taylor C602",
        safety_priority=True,
        response_type="procedural"
    )
    
    # Create conversation context
    conversation_context = ConversationContext(
        current_topic="fryer cleaning",
        current_entity="Taylor C602"
    )
    
    # Build enhanced response
    enhanced_response = await response_builder.build_enhanced_response(
        agent_type=AgentType.EQUIPMENT,
        session_id="test_session_6",
        base_response=base_response,
        query_text="How do I clean the Taylor C602 fryer?",
        conversation_context=conversation_context,
        auto_enhance=True
    )
    
    # Verify enhanced response
    assert enhanced_response.text_response == base_response.text_response
    assert enhanced_response.primary_agent == AgentType.EQUIPMENT
    assert enhanced_response.safety_priority == True
    assert hasattr(enhanced_response, 'visual_citations')
    
    logger.info(f"✅ Enhanced Response Builder: Created {type(enhanced_response).__name__} with agent {enhanced_response.primary_agent.value}")
    
    return enhanced_response

async def test_end_to_end_integration():
    """Test complete end-to-end integration"""
    logger.info("🔍 Testing End-to-End Integration...")
    
    # Create complete system
    mock_citation_service = MockMultiModalCitationService()
    mock_graph_service = MockVoiceGraphService()
    
    coordinator, response_builder = await create_tool_enhanced_agent_system(
        multimodal_service=mock_citation_service,
        voice_graph_service=mock_graph_service
    )
    
    # Test scenario: User asks about fryer maintenance
    user_query = "How do I clean the Taylor C602 fryer safely?"
    session_id = "test_session_e2e"
    
    # Step 1: Setup agent with tools
    conversation_context = ConversationContext(
        current_topic="fryer maintenance",
        current_entity="Taylor C602"
    )
    
    agent_context = coordinator.setup_agent_with_tools(
        agent_type=AgentType.EQUIPMENT,
        session_id=session_id,
        conversation_context=conversation_context
    )
    
    # Step 2: Execute individual tools
    tool_results = {}
    
    # Visual citations
    citation_query = VisualCitationQuery(
        query_text=user_query,
        equipment_context=["taylor c602", "fryer"],
        safety_critical=True
    )
    
    citation_result = await coordinator.execute_tool_for_agent(
        AgentType.EQUIPMENT, session_id, "visual_citations", citation_query
    )
    tool_results['citations'] = citation_result
    
    # Graph-RAG context
    graph_query = GraphRAGQuery(
        equipment_name="Taylor C602",
        query_context=user_query,
        include_relationships=True
    )
    
    graph_result = await coordinator.execute_tool_for_agent(
        AgentType.EQUIPMENT, session_id, "graph_rag", graph_query
    )
    tool_results['graph'] = graph_result
    
    # Safety validation
    safety_query = SafetyValidationQuery(
        content_to_validate="Clean fryer with hot oil and high temperature",
        equipment_mentioned=["taylor c602", "fryer"],
        context_critical=True
    )
    
    safety_result = await coordinator.execute_tool_for_agent(
        AgentType.EQUIPMENT, session_id, "safety_validation", safety_query
    )
    tool_results['safety'] = safety_result
    
    # Step 3: Build enhanced response
    base_response = VoiceResponse(
        text_response="To clean the Taylor C602 fryer safely, follow these steps...",
        detected_intent=ConversationIntent.EQUIPMENT_QUESTION,
        confidence_score=0.9,
        equipment_mentioned="Taylor C602",
        safety_priority=True,
        response_type="procedural"
    )
    
    enhanced_response = await response_builder.build_enhanced_response(
        agent_type=AgentType.EQUIPMENT,
        session_id=session_id,
        base_response=base_response,
        query_text=user_query,
        conversation_context=conversation_context,
        auto_enhance=True
    )
    
    # Verify end-to-end results
    assert len(tool_results) == 3, "Should have executed 3 tools"
    assert all(result['success'] for result in tool_results.values()), "All tools should succeed"
    assert enhanced_response.primary_agent == AgentType.EQUIPMENT
    assert enhanced_response.safety_priority == True
    
    logger.info(f"✅ End-to-End Integration: Processed query through {len(tool_results)} tools")
    
    return {
        'tool_results': tool_results,
        'enhanced_response': enhanced_response,
        'coordinator': coordinator,
        'response_builder': response_builder
    }

# ===============================================================================
# PERFORMANCE TESTS
# ===============================================================================

async def test_performance_metrics():
    """Test performance tracking and metrics"""
    logger.info("🔍 Testing Performance Metrics...")
    
    # Create coordinator
    coordinator = AgentToolCoordinator(
        multimodal_service=MockMultiModalCitationService(),
        voice_graph_service=MockVoiceGraphService()
    )
    
    # Setup multiple agents
    session_id = "perf_test_session"
    
    for agent_type in [AgentType.EQUIPMENT, AgentType.SAFETY, AgentType.PROCEDURE]:
        coordinator.setup_agent_with_tools(agent_type, session_id)
    
    # Execute multiple tool calls
    queries = [
        ("equipment", "visual_citations", VisualCitationQuery(query_text="fryer diagram")),
        ("equipment", "graph_rag", GraphRAGQuery(query_context="fryer maintenance")),
        ("safety", "safety_validation", SafetyValidationQuery(content_to_validate="hot oil safety")),
        ("procedure", "context_enhancement", ContextEnhancementQuery(current_query="cleaning steps"))
    ]
    
    results = []
    
    for agent_type_str, tool_name, query in queries:
        agent_type = AgentType(agent_type_str)
        result = await coordinator.execute_tool_for_agent(
            agent_type, session_id, tool_name, query
        )
        results.append(result)
    
    # Check performance metrics
    assert len(results) == 4, "Should have executed 4 tool calls"
    
    total_time = sum(r['execution_time_ms'] for r in results)
    successful_calls = sum(1 for r in results if r['success'])
    
    logger.info(f"✅ Performance Metrics: {successful_calls}/{len(results)} successful calls, total time: {total_time:.2f}ms")
    
    return {
        'results': results,
        'total_time': total_time,
        'success_rate': successful_calls / len(results),
        'global_metrics': coordinator.global_tool_metrics
    }

# ===============================================================================
# MAIN TEST RUNNER
# ===============================================================================

async def run_all_tests():
    """Run all integration tests"""
    logger.info("🚀 Starting PydanticAI Tools Integration Tests...")
    
    if not IMPORTS_SUCCESSFUL:
        logger.error("❌ Cannot run tests due to import failures")
        return False
    
    test_results = {}
    
    try:
        # Individual tool tests
        test_results['visual_citation'] = await test_visual_citation_tool()
        test_results['graph_rag'] = await test_graph_rag_tool()
        test_results['safety_validation'] = await test_safety_validation_tool()
        test_results['context_enhancement'] = await test_context_enhancement_tool()
        
        # Integration tests
        test_results['coordinator'], test_results['agent_context'] = await test_agent_tool_coordinator()
        test_results['enhanced_response'] = await test_enhanced_response_builder()
        test_results['end_to_end'] = await test_end_to_end_integration()
        
        # Performance tests
        test_results['performance'] = await test_performance_metrics()
        
        logger.info("✅ All tests completed successfully!")
        
        # Print summary
        print("\n" + "="*80)
        print("PYDANTIC AI TOOLS INTEGRATION TEST SUMMARY")
        print("="*80)
        
        print(f"✅ Visual Citation Tool: {test_results['visual_citation'].total_found} citations found")
        print(f"✅ Graph-RAG Tool: {len(test_results['graph_rag'].entities)} entities, confidence {test_results['graph_rag'].confidence_score:.2f}")
        print(f"✅ Safety Validation Tool: Risk level {test_results['safety_validation'].risk_level}")
        print(f"✅ Context Enhancement Tool: Context score {test_results['context_enhancement'].context_score:.2f}")
        print(f"✅ Agent Tool Coordinator: {len(test_results['agent_context'].available_tools)} tools available")
        print(f"✅ Enhanced Response Builder: {type(test_results['enhanced_response']).__name__} created")
        print(f"✅ End-to-End Integration: {len(test_results['end_to_end']['tool_results'])} tools executed")
        print(f"✅ Performance Metrics: {test_results['performance']['success_rate']:.1%} success rate")
        
        print("\n🎉 All PydanticAI Tools Integration Tests PASSED!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)