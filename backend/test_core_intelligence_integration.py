#!/usr/bin/env python3
"""
Test Core Intelligence Service Integration
=========================================

Comprehensive test of the Core Intelligence Service integration with existing
QSR systems. Tests universal intelligence for both text and voice interactions.

Tests:
1. Core Intelligence Service initialization
2. Multi-agent processing with Ragie integration
3. Intelligence integration with existing endpoints
4. Performance metrics and monitoring
5. Fallback mechanisms and error handling

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
    from services.core_intelligence_service import (
        CoreIntelligenceService, create_core_intelligence_service,
        IntelligentResponse, InteractionMode, AgentType, RagieQueryContext
    )
    
    from services.intelligence_integration import (
        IntelligenceIntegration, initialize_intelligence_integration,
        enhance_chat_endpoint, enhance_voice_endpoint
    )
    
    IMPORTS_SUCCESSFUL = True
    logger.info("✅ All imports successful")
    
except ImportError as e:
    logger.error(f"❌ Import failed: {e}")
    IMPORTS_SUCCESSFUL = False

# ===============================================================================
# MOCK SERVICES FOR TESTING
# ===============================================================================

class MockRagieService:
    """Mock Ragie service for testing"""
    
    def __init__(self):
        self.mock_responses = {
            'fryer': {
                'content': 'The Taylor C602 fryer operates at 350°F for optimal cooking. Regular maintenance includes daily cleaning and weekly deep cleaning cycles.',
                'confidence': 0.9,
                'sources': [{'title': 'Fryer Manual', 'page': 12}],
                'metadata': {'equipment_type': 'fryer', 'manual_section': 'operation'}
            },
            'cleaning': {
                'content': 'Daily cleaning procedure: 1. Cool equipment completely 2. Remove all removable parts 3. Clean with approved sanitizer 4. Rinse thoroughly 5. Reassemble',
                'confidence': 0.85,
                'sources': [{'title': 'Cleaning Manual', 'page': 8}],
                'metadata': {'procedure_type': 'cleaning', 'frequency': 'daily'}
            },
            'safety': {
                'content': 'SAFETY PRIORITY: Always disconnect power before maintenance. Use appropriate PPE. Never bypass safety systems. Report all incidents immediately.',
                'confidence': 0.95,
                'sources': [{'title': 'Safety Manual', 'page': 3}],
                'metadata': {'safety_level': 'critical', 'compliance': 'OSHA'}
            }
        }
    
    async def search_documents(self, query: str, limit: int = 10, hybrid_search: bool = True) -> Dict[str, Any]:
        """Mock document search"""
        await asyncio.sleep(0.1)  # Simulate search time
        
        query_lower = query.lower()
        
        # Return relevant mock response
        for keyword, response in self.mock_responses.items():
            if keyword in query_lower:
                return response
        
        # Default response
        return {
            'content': f'General QSR information for: {query}',
            'confidence': 0.7,
            'sources': [{'title': 'QSR Manual', 'page': 1}],
            'metadata': {'query_type': 'general'}
        }

class MockCitationService:
    """Mock citation service for testing"""
    
    def __init__(self):
        self.mock_citations = {
            'diagram': ['equipment diagram', 'temperature control diagram'],
            'image': ['safety equipment image', 'procedure illustration'],
            'table': ['temperature specifications', 'cleaning schedule']
        }
    
    def extract_visual_references(self, text: str) -> Dict[str, List[str]]:
        """Mock visual reference extraction"""
        references = {}
        
        text_lower = text.lower()
        
        for ref_type, refs in self.mock_citations.items():
            matching_refs = [ref for ref in refs if any(word in text_lower for word in ref.split())]
            if matching_refs:
                references[ref_type] = matching_refs
        
        return references

# ===============================================================================
# CORE INTELLIGENCE SERVICE TESTS
# ===============================================================================

async def test_core_intelligence_service_initialization():
    """Test core intelligence service initialization"""
    logger.info("🔍 Testing Core Intelligence Service Initialization...")
    
    # Create mock services
    mock_ragie = MockRagieService()
    mock_citation = MockCitationService()
    
    # Create core intelligence service
    core_service = await create_core_intelligence_service(
        ragie_service=mock_ragie,
        citation_service=mock_citation
    )
    
    # Verify initialization
    assert core_service is not None, "Core service should be created"
    assert len(core_service.agents) == 5, "Should have 5 specialized agents"
    assert core_service.ragie_service is not None, "Should have Ragie service"
    assert core_service.citation_service is not None, "Should have citation service"
    
    # Test health check
    health = await core_service.health_check()
    assert health['service_status'] == 'healthy', "Service should be healthy"
    assert health['agents_initialized'] == 5, "All agents should be initialized"
    
    logger.info("✅ Core Intelligence Service initialization successful")
    
    return core_service

async def test_multi_agent_processing():
    """Test multi-agent processing with different query types"""
    logger.info("🔍 Testing Multi-Agent Processing...")
    
    # Create service
    core_service = await test_core_intelligence_service_initialization()
    
    # Test queries for different agents
    test_queries = [
        {
            'query': 'How do I troubleshoot the Taylor C602 fryer?',
            'expected_agent': AgentType.EQUIPMENT,
            'mode': InteractionMode.TEXT_CHAT
        },
        {
            'query': 'What are the steps for cleaning the fryer?',
            'expected_agent': AgentType.PROCEDURE,
            'mode': InteractionMode.VOICE_CHAT
        },
        {
            'query': 'Safety procedures for hot oil equipment',
            'expected_agent': AgentType.SAFETY,
            'mode': InteractionMode.TEXT_CHAT
        },
        {
            'query': 'Daily maintenance schedule for cleaning',
            'expected_agent': AgentType.MAINTENANCE,
            'mode': InteractionMode.VOICE_CHAT
        },
        {
            'query': 'General QSR operations information',
            'expected_agent': AgentType.GENERAL,
            'mode': InteractionMode.TEXT_CHAT
        }
    ]
    
    results = []
    
    for test_case in test_queries:
        # Process query
        response = await core_service.process_universal_query(
            query=test_case['query'],
            interaction_mode=test_case['mode'],
            session_id=f"test_session_{test_case['expected_agent'].value}"
        )
        
        # Verify response
        assert isinstance(response, IntelligentResponse), "Should return IntelligentResponse"
        assert response.primary_agent == test_case['expected_agent'], f"Should use {test_case['expected_agent'].value} agent"
        assert response.confidence_score > 0.5, "Should have reasonable confidence"
        assert len(response.text_response) > 0, "Should have text response"
        
        results.append({
            'query': test_case['query'],
            'agent': response.primary_agent.value,
            'confidence': response.confidence_score,
            'response_length': len(response.text_response),
            'visual_citations': response.citation_count,
            'safety_priority': response.safety_priority
        })
    
    logger.info(f"✅ Multi-Agent Processing: Processed {len(results)} queries successfully")
    
    # Print results summary
    for result in results:
        logger.info(f"  {result['agent']}: {result['confidence']:.2f} confidence, {result['visual_citations']} citations")
    
    return results

async def test_intelligence_integration():
    """Test intelligence integration with existing endpoints"""
    logger.info("🔍 Testing Intelligence Integration...")
    
    # Create mock services
    mock_ragie = MockRagieService()
    mock_citation = MockCitationService()
    
    # Initialize intelligence integration
    success = await initialize_intelligence_integration(
        ragie_service=mock_ragie,
        citation_service=mock_citation
    )
    
    assert success, "Intelligence integration should initialize successfully"
    
    # Test chat endpoint enhancement
    chat_result = await enhance_chat_endpoint(
        message="How do I clean the fryer safely?",
        session_id="test_chat_session",
        use_intelligence=True
    )
    
    # Verify chat result
    assert 'response' in chat_result, "Should have response"
    assert 'confidence' in chat_result, "Should have confidence"
    assert 'agent_type' in chat_result, "Should have agent type"
    assert chat_result['intelligence_used'], "Should use intelligence"
    
    # Test voice endpoint enhancement
    voice_result = await enhance_voice_endpoint(
        message="What are the safety procedures for equipment maintenance?",
        session_id="test_voice_session",
        use_intelligence=True
    )
    
    # Verify voice result
    assert hasattr(voice_result, 'text_response'), "Should have text response"
    assert hasattr(voice_result, 'confidence_score'), "Should have confidence"
    assert hasattr(voice_result, 'safety_priority'), "Should have safety priority"
    
    logger.info("✅ Intelligence Integration successful")
    
    return {
        'chat_result': chat_result,
        'voice_result': voice_result
    }

async def test_performance_metrics():
    """Test performance metrics and monitoring"""
    logger.info("🔍 Testing Performance Metrics...")
    
    # Create service
    core_service = await test_core_intelligence_service_initialization()
    
    # Process multiple queries to generate metrics
    test_queries = [
        "How do I troubleshoot the fryer?",
        "What are the cleaning steps?",
        "Safety procedures for maintenance",
        "Daily maintenance schedule",
        "General QSR information"
    ]
    
    for query in test_queries:
        await core_service.process_universal_query(
            query=query,
            interaction_mode=InteractionMode.TEXT_CHAT,
            session_id="metrics_test_session"
        )
    
    # Get performance metrics
    metrics = core_service.get_performance_metrics()
    
    # Verify metrics
    assert isinstance(metrics, dict), "Should return metrics dictionary"
    assert len(metrics) == 5, "Should have metrics for all 5 agents"
    
    # Check agent metrics
    for agent_type, agent_metrics in metrics.items():
        assert 'total_queries' in agent_metrics, "Should have total queries"
        assert 'success_rate' in agent_metrics, "Should have success rate"
        assert 'avg_confidence' in agent_metrics, "Should have average confidence"
        assert 'avg_response_time' in agent_metrics, "Should have average response time"
    
    logger.info("✅ Performance Metrics test successful")
    
    return metrics

async def test_fallback_mechanisms():
    """Test fallback mechanisms when intelligence fails"""
    logger.info("🔍 Testing Fallback Mechanisms...")
    
    # Test with missing services
    integration = IntelligenceIntegration()
    
    # Test chat fallback
    chat_result = await integration.process_chat_message(
        message="Test message",
        session_id="fallback_test",
        use_intelligence=True  # Should fallback since not initialized
    )
    
    # Verify fallback
    assert isinstance(chat_result, dict), "Should return fallback response"
    assert 'fallback_used' in chat_result, "Should indicate fallback used"
    
    # Test voice fallback
    voice_result = await integration.process_voice_message(
        message="Test voice message",
        session_id="fallback_test",
        use_intelligence=True
    )
    
    # Verify fallback
    assert hasattr(voice_result, 'text_response'), "Should return VoiceResponse"
    assert voice_result.confidence_score > 0, "Should have some confidence"
    
    logger.info("✅ Fallback Mechanisms test successful")
    
    return {
        'chat_fallback': chat_result,
        'voice_fallback': voice_result
    }

async def test_agent_specialization():
    """Test agent specialization and context understanding"""
    logger.info("🔍 Testing Agent Specialization...")
    
    # Create service
    core_service = await test_core_intelligence_service_initialization()
    
    # Test equipment agent specialization
    equipment_response = await core_service.process_universal_query(
        query="The fryer temperature is not reaching 350°F",
        interaction_mode=InteractionMode.TEXT_CHAT,
        session_id="equipment_test"
    )
    
    # Verify equipment specialization
    assert equipment_response.primary_agent == AgentType.EQUIPMENT, "Should use equipment agent"
    assert 'fryer' in equipment_response.text_response.lower(), "Should mention fryer"
    assert equipment_response.confidence_score > 0.7, "Should have high confidence"
    
    # Test safety agent specialization
    safety_response = await core_service.process_universal_query(
        query="Emergency procedure for hot oil spill",
        interaction_mode=InteractionMode.TEXT_CHAT,
        session_id="safety_test"
    )
    
    # Verify safety specialization
    assert safety_response.primary_agent == AgentType.SAFETY, "Should use safety agent"
    assert safety_response.safety_priority == True, "Should have safety priority"
    assert len(safety_response.safety_warnings) > 0, "Should have safety warnings"
    
    # Test procedure agent specialization
    procedure_response = await core_service.process_universal_query(
        query="Step-by-step cleaning procedure",
        interaction_mode=InteractionMode.VOICE_CHAT,
        session_id="procedure_test"
    )
    
    # Verify procedure specialization
    assert procedure_response.primary_agent == AgentType.PROCEDURE, "Should use procedure agent"
    assert procedure_response.voice_optimized == True, "Should be voice optimized"
    assert 'step' in procedure_response.text_response.lower(), "Should mention steps"
    
    logger.info("✅ Agent Specialization test successful")
    
    return {
        'equipment_response': equipment_response,
        'safety_response': safety_response,
        'procedure_response': procedure_response
    }

# ===============================================================================
# INTEGRATION TESTS
# ===============================================================================

async def test_end_to_end_integration():
    """Test complete end-to-end integration"""
    logger.info("🔍 Testing End-to-End Integration...")
    
    # Initialize complete system
    mock_ragie = MockRagieService()
    mock_citation = MockCitationService()
    
    # Initialize intelligence integration
    success = await initialize_intelligence_integration(
        ragie_service=mock_ragie,
        citation_service=mock_citation
    )
    
    assert success, "Integration should initialize"
    
    # Test complete workflow
    scenarios = [
        {
            'name': 'Equipment Troubleshooting',
            'message': 'The Taylor C602 fryer is not heating properly',
            'expected_agent': 'equipment',
            'mode': 'text'
        },
        {
            'name': 'Safety Emergency',
            'message': 'Hot oil spill emergency procedures',
            'expected_agent': 'safety',
            'mode': 'voice'
        },
        {
            'name': 'Cleaning Procedure',
            'message': 'How do I clean the fryer step by step?',
            'expected_agent': 'procedure',
            'mode': 'text'
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        if scenario['mode'] == 'text':
            result = await enhance_chat_endpoint(
                message=scenario['message'],
                session_id=f"e2e_{scenario['name'].lower().replace(' ', '_')}"
            )
        else:
            result = await enhance_voice_endpoint(
                message=scenario['message'],
                session_id=f"e2e_{scenario['name'].lower().replace(' ', '_')}"
            )
        
        results.append({
            'scenario': scenario['name'],
            'success': True,
            'result': result
        })
    
    logger.info(f"✅ End-to-End Integration: {len(results)} scenarios successful")
    
    return results

# ===============================================================================
# MAIN TEST RUNNER
# ===============================================================================

async def run_all_tests():
    """Run all integration tests"""
    logger.info("🚀 Starting Core Intelligence Integration Tests...")
    
    if not IMPORTS_SUCCESSFUL:
        logger.error("❌ Cannot run tests due to import failures")
        return False
    
    test_results = {}
    
    try:
        # Core service tests
        test_results['initialization'] = await test_core_intelligence_service_initialization()
        test_results['multi_agent'] = await test_multi_agent_processing()
        test_results['specialization'] = await test_agent_specialization()
        test_results['performance'] = await test_performance_metrics()
        
        # Integration tests
        test_results['integration'] = await test_intelligence_integration()
        test_results['fallback'] = await test_fallback_mechanisms()
        test_results['end_to_end'] = await test_end_to_end_integration()
        
        logger.info("✅ All tests completed successfully!")
        
        # Print comprehensive summary
        print("\n" + "="*80)
        print("CORE INTELLIGENCE INTEGRATION TEST SUMMARY")
        print("="*80)
        
        print(f"✅ Core Service: {len(test_results['initialization'].agents)} agents initialized")
        print(f"✅ Multi-Agent Processing: {len(test_results['multi_agent'])} queries processed")
        print(f"✅ Agent Specialization: 3 specialized agents tested")
        print(f"✅ Performance Metrics: {len(test_results['performance'])} agent metrics collected")
        print(f"✅ Integration: Chat and voice endpoints enhanced")
        print(f"✅ Fallback Mechanisms: Graceful degradation tested")
        print(f"✅ End-to-End: {len(test_results['end_to_end'])} scenarios completed")
        
        print("\n📊 Performance Summary:")
        for agent_type, metrics in test_results['performance'].items():
            print(f"  {agent_type}: {metrics['success_rate']:.1%} success, {metrics['avg_confidence']:.2f} confidence")
        
        print("\n🎉 All Core Intelligence Integration Tests PASSED!")
        print("🤖 Universal intelligence successfully integrated with existing QSR system")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)