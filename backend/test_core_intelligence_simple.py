#!/usr/bin/env python3
"""
Simple Core Intelligence Service Test
====================================

Simple test of the Core Intelligence Service without complex imports
to verify the basic functionality works.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================================================================
# MOCK SERVICES
# ===============================================================================

class MockRagieService:
    """Mock Ragie service for testing"""
    
    async def search_documents(self, query: str, limit: int = 10, hybrid_search: bool = True):
        """Mock document search"""
        await asyncio.sleep(0.1)  # Simulate search time
        
        return {
            'content': f'Mock response for: {query}',
            'confidence': 0.8,
            'sources': [{'title': 'Test Manual', 'page': 1}],
            'metadata': {'query_type': 'test'}
        }

class MockCitationService:
    """Mock citation service for testing"""
    
    def extract_visual_references(self, text: str):
        """Mock visual reference extraction"""
        return {
            'diagram': ['test diagram'],
            'image': ['test image']
        }

# ===============================================================================
# BASIC TEST
# ===============================================================================

async def test_basic_functionality():
    """Test basic functionality without complex imports"""
    
    try:
        # Test basic imports
        from services.core_intelligence_service import (
            AgentType, InteractionMode, IntelligentResponse, RagieQueryContext
        )
        
        logger.info("✅ Basic imports successful")
        
        # Test enum values
        assert AgentType.EQUIPMENT == "equipment"
        assert InteractionMode.TEXT_CHAT == "text_chat"
        
        logger.info("✅ Enums working correctly")
        
        # Test query context creation
        query_context = RagieQueryContext(
            query="Test query",
            agent_type=AgentType.GENERAL,
            interaction_mode=InteractionMode.TEXT_CHAT
        )
        
        assert query_context.query == "Test query"
        assert query_context.agent_type == AgentType.GENERAL
        
        logger.info("✅ Query context creation successful")
        
        # Test response creation
        response = IntelligentResponse(
            text_response="Test response",
            confidence_score=0.8,
            primary_agent=AgentType.GENERAL,
            detected_intent="new_topic"
        )
        
        assert response.text_response == "Test response"
        assert response.confidence_score == 0.8
        
        logger.info("✅ Response creation successful")
        
        logger.info("🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agents_basic():
    """Test basic agent functionality"""
    
    try:
        from services.core_intelligence_service import (
            QSREquipmentAgent, QSRSafetyAgent, QSRGeneralAgent,
            RagieQueryContext, AgentType, InteractionMode
        )
        
        # Create mock services
        mock_ragie = MockRagieService()
        mock_citation = MockCitationService()
        
        # Create agents
        equipment_agent = QSREquipmentAgent(mock_ragie, mock_citation)
        safety_agent = QSRSafetyAgent(mock_ragie, mock_citation)
        general_agent = QSRGeneralAgent(mock_ragie, mock_citation)
        
        logger.info("✅ Agents created successfully")
        
        # Test agent processing
        query_context = RagieQueryContext(
            query="Test equipment query",
            agent_type=AgentType.EQUIPMENT,
            interaction_mode=InteractionMode.TEXT_CHAT
        )
        
        equipment_response = await equipment_agent.process_query(query_context)
        
        assert equipment_response.text_response is not None
        assert equipment_response.primary_agent == AgentType.EQUIPMENT
        
        logger.info("✅ Equipment agent processing successful")
        
        # Test safety agent
        safety_context = RagieQueryContext(
            query="Safety emergency procedures",
            agent_type=AgentType.SAFETY,
            interaction_mode=InteractionMode.TEXT_CHAT
        )
        
        safety_response = await safety_agent.process_query(safety_context)
        
        assert safety_response.safety_priority == True
        assert len(safety_response.safety_warnings) > 0
        
        logger.info("✅ Safety agent processing successful")
        
        logger.info("🎉 Agent tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_core_service_basic():
    """Test basic core service functionality"""
    
    try:
        from services.core_intelligence_service import (
            CoreIntelligenceService, create_core_intelligence_service
        )
        
        # Create mock services
        mock_ragie = MockRagieService()
        mock_citation = MockCitationService()
        
        # Create core service
        core_service = await create_core_intelligence_service(
            ragie_service=mock_ragie,
            citation_service=mock_citation
        )
        
        logger.info("✅ Core service created successfully")
        
        # Test health check
        health = await core_service.health_check()
        assert health['service_status'] == 'healthy'
        
        logger.info("✅ Health check successful")
        
        # Test query processing
        response = await core_service.process_text_chat(
            query="Test query",
            session_id="test_session"
        )
        
        assert response.text_response is not None
        assert response.confidence_score > 0
        
        logger.info("✅ Query processing successful")
        
        logger.info("🎉 Core service tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Core service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# ===============================================================================
# MAIN TEST RUNNER
# ===============================================================================

async def run_simple_tests():
    """Run simple tests"""
    
    logger.info("🚀 Starting Simple Core Intelligence Tests...")
    
    tests = [
        test_basic_functionality,
        test_agents_basic,
        test_core_service_basic
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
            logger.info(f"✅ {test.__name__} passed")
        except Exception as e:
            logger.error(f"❌ {test.__name__} failed: {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    
    logger.info(f"Test Results: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        logger.info("🎉 All simple tests passed!")
        return True
    else:
        logger.error("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_simple_tests())
    sys.exit(0 if success else 1)