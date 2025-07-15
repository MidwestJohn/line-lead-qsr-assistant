#!/usr/bin/env python3
"""
Test Clean Intelligence Service - Pure Ragie + PydanticAI
========================================================

Test the clean intelligence service that ONLY uses Ragie + PydanticAI
without any Graph-RAG, Neo4j, LightRAG, or Enterprise Bridge dependencies.

Author: Generated with Memex (https://memex.tech)
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
# MOCK SERVICES - Only Ragie
# ===============================================================================

class MockRagieService:
    """Mock Ragie service for testing"""
    
    def __init__(self):
        self.responses = {
            'equipment': {
                'content': 'For equipment troubleshooting: Check power connections, verify temperature settings, inspect for clogs or damage.',
                'confidence': 0.9,
                'sources': [{'title': 'Equipment Manual', 'page': 12}]
            },
            'procedure': {
                'content': 'Follow these steps: 1. Prepare workspace 2. Gather tools 3. Follow safety protocols 4. Execute procedure 5. Clean up',
                'confidence': 0.85,
                'sources': [{'title': 'Procedure Manual', 'page': 8}]
            },
            'safety': {
                'content': 'SAFETY CRITICAL: Always follow proper safety protocols. Use PPE, disconnect power, and never bypass safety systems.',
                'confidence': 0.95,
                'sources': [{'title': 'Safety Manual', 'page': 3}]
            },
            'maintenance': {
                'content': 'Daily maintenance: Clean all surfaces, check fluid levels, inspect for wear, document completion.',
                'confidence': 0.8,
                'sources': [{'title': 'Maintenance Guide', 'page': 15}]
            }
        }
    
    async def search_documents(self, query: str, limit: int = 10, hybrid_search: bool = True):
        """Mock document search"""
        await asyncio.sleep(0.1)  # Simulate search time
        
        query_lower = query.lower()
        
        # Return appropriate response based on query
        if any(word in query_lower for word in ['equipment', 'machine', 'troubleshoot', 'repair']):
            return self.responses['equipment']
        elif any(word in query_lower for word in ['procedure', 'steps', 'how to', 'process']):
            return self.responses['procedure']
        elif any(word in query_lower for word in ['safety', 'danger', 'emergency', 'hazard']):
            return self.responses['safety']
        elif any(word in query_lower for word in ['clean', 'maintenance', 'sanitize']):
            return self.responses['maintenance']
        else:
            return {
                'content': f'General information for: {query}',
                'confidence': 0.7,
                'sources': [{'title': 'General Manual', 'page': 1}]
            }

class MockCitationService:
    """Mock citation service for testing"""
    
    def extract_visual_references(self, text: str):
        """Mock visual reference extraction"""
        return {
            'diagram': ['equipment diagram'] if 'equipment' in text.lower() else [],
            'image': ['procedure image'] if 'procedure' in text.lower() else [],
            'table': ['safety table'] if 'safety' in text.lower() else []
        }

# ===============================================================================
# CLEAN INTELLIGENCE TESTS
# ===============================================================================

async def test_clean_service_initialization():
    """Test clean service initialization"""
    logger.info("🔍 Testing Clean Intelligence Service Initialization...")
    
    try:
        from services.clean_intelligence_service import (
            CleanIntelligenceService, create_clean_intelligence_service,
            AgentType, InteractionMode, ConversationIntent
        )
        
        # Test basic imports
        assert AgentType.EQUIPMENT == "equipment"
        assert InteractionMode.TEXT_CHAT == "text_chat"
        assert ConversationIntent.EQUIPMENT_QUESTION == "equipment_question"
        
        # Create mock services
        mock_ragie = MockRagieService()
        mock_citation = MockCitationService()
        
        # Create clean service
        service = await create_clean_intelligence_service(
            ragie_service=mock_ragie,
            citation_service=mock_citation
        )
        
        # Verify service
        assert service is not None
        assert len(service.agents) == 5
        assert service.ragie_service is not None
        assert service.citation_service is not None
        
        # Health check
        health = await service.health_check()
        assert health['status'] == 'healthy'
        assert health['ragie_available'] == True
        assert health['citation_available'] == True
        assert health['dependencies']['graph_rag'] == False
        assert health['dependencies']['neo4j'] == False
        assert health['dependencies']['lightrag'] == False
        assert health['dependencies']['ragie_only'] == True
        
        logger.info("✅ Clean service initialization successful")
        return service
        
    except Exception as e:
        logger.error(f"❌ Clean service initialization failed: {e}")
        raise

async def test_clean_agent_selection():
    """Test clean agent selection"""
    logger.info("🔍 Testing Clean Agent Selection...")
    
    try:
        service = await test_clean_service_initialization()
        
        # Test different query types
        test_cases = [
            ("How do I troubleshoot the fryer?", "equipment"),
            ("What are the steps for cleaning?", "procedure"),
            ("Safety procedures for hot oil", "safety"),
            ("Daily maintenance schedule", "maintenance"),
            ("General QSR information", "general")
        ]
        
        for query, expected_agent in test_cases:
            selected_agent = service._select_agent_clean(query)
            assert selected_agent.value == expected_agent, f"Expected {expected_agent}, got {selected_agent.value} for query: {query}"
        
        logger.info("✅ Clean agent selection successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Clean agent selection failed: {e}")
        raise

async def test_clean_query_processing():
    """Test clean query processing"""
    logger.info("🔍 Testing Clean Query Processing...")
    
    try:
        service = await test_clean_service_initialization()
        
        from services.clean_intelligence_service import InteractionMode, AgentType
        
        # Test equipment query
        response = await service.process_query(
            query="How do I fix the fryer temperature issue?",
            interaction_mode=InteractionMode.TEXT_CHAT,
            session_id="test_session"
        )
        
        # Verify response
        assert response.text_response is not None
        assert response.primary_agent == AgentType.EQUIPMENT
        assert response.confidence_score > 0.5
        assert len(response.ragie_sources) > 0
        assert 'equipment' in response.text_response.lower()
        
        # Test safety query
        safety_response = await service.process_query(
            query="Emergency procedures for hot oil spill",
            interaction_mode=InteractionMode.TEXT_CHAT,
            session_id="test_session"
        )
        
        # Verify safety response
        assert safety_response.primary_agent == AgentType.SAFETY
        assert safety_response.safety_priority == True
        assert len(safety_response.safety_warnings) > 0
        assert 'safety' in safety_response.text_response.lower()
        
        logger.info("✅ Clean query processing successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Clean query processing failed: {e}")
        raise

async def test_clean_performance_metrics():
    """Test performance metrics"""
    logger.info("🔍 Testing Clean Performance Metrics...")
    
    try:
        service = await test_clean_service_initialization()
        
        # Process multiple queries
        queries = [
            "How do I troubleshoot equipment?",
            "What are the cleaning steps?",
            "Safety procedures for maintenance",
            "Daily maintenance schedule",
            "General QSR operations"
        ]
        
        from services.clean_intelligence_service import InteractionMode
        
        for query in queries:
            await service.process_query(query, InteractionMode.TEXT_CHAT, "metrics_test")
        
        # Get metrics
        metrics = service.get_performance_metrics()
        
        # Verify metrics
        assert isinstance(metrics, dict)
        assert len(metrics) == 5  # 5 agents
        
        for agent_type, agent_metrics in metrics.items():
            assert 'total_queries' in agent_metrics
            assert 'success_rate' in agent_metrics
            assert 'avg_time_ms' in agent_metrics
        
        logger.info("✅ Clean performance metrics successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Clean performance metrics failed: {e}")
        raise

async def test_clean_no_dependencies():
    """Test that there are no Graph-RAG dependencies"""
    logger.info("🔍 Testing No Graph-RAG Dependencies...")
    
    try:
        # Import clean service
        from services.clean_intelligence_service import CleanIntelligenceService
        
        # Check that service doesn't import Graph-RAG modules
        import inspect
        
        # Get all imported modules in the service
        service_file = inspect.getfile(CleanIntelligenceService)
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Check for forbidden imports (excluding status strings)
        forbidden_imports = [
            'import neo4j',
            'from neo4j',
            'import lightrag',
            'from lightrag',
            'import enterprise_bridge',
            'from enterprise_bridge',
            'import rag_anything',
            'from rag_anything',
            'import voice_graph_service',
            'from voice_graph_service',
            'import graph_rag_service',
            'from graph_rag_service'
        ]
        
        for forbidden in forbidden_imports:
            assert forbidden not in content.lower(), f"Found forbidden import: {forbidden}"
        
        # Check for allowed imports
        allowed_imports = [
            'ragie_service_clean',
            'multimodal_citation_service',
            'pydantic_ai'
        ]
        
        for allowed in allowed_imports:
            if allowed in content.lower():
                logger.info(f"✅ Found allowed import: {allowed}")
        
        logger.info("✅ No Graph-RAG dependencies confirmed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dependency check failed: {e}")
        raise

async def test_clean_visual_citations():
    """Test visual citations with clean service"""
    logger.info("🔍 Testing Clean Visual Citations...")
    
    try:
        service = await test_clean_service_initialization()
        
        from services.clean_intelligence_service import InteractionMode
        
        # Test query with visual content
        response = await service.process_query(
            query="Show me the equipment diagram for troubleshooting",
            interaction_mode=InteractionMode.TEXT_CHAT,
            session_id="citation_test"
        )
        
        # Verify visual citations
        assert isinstance(response.visual_citations, list)
        if response.visual_citations:
            citation = response.visual_citations[0]
            assert 'citation_id' in citation
            assert 'type' in citation
            assert 'source' in citation
            assert citation['ragie_source'] == True
        
        logger.info("✅ Clean visual citations successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Clean visual citations failed: {e}")
        raise

# ===============================================================================
# MAIN TEST RUNNER
# ===============================================================================

async def run_clean_tests():
    """Run all clean intelligence tests"""
    logger.info("🚀 Starting Clean Intelligence Tests (Ragie + PydanticAI Only)...")
    
    tests = [
        test_clean_service_initialization,
        test_clean_agent_selection,
        test_clean_query_processing,
        test_clean_performance_metrics,
        test_clean_no_dependencies,
        test_clean_visual_citations
    ]
    
    results = []
    
    for test in tests:
        try:
            await test()
            results.append(True)
            logger.info(f"✅ {test.__name__} passed")
        except Exception as e:
            logger.error(f"❌ {test.__name__} failed: {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    
    logger.info(f"Test Results: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        logger.info("🎉 All Clean Intelligence Tests PASSED!")
        logger.info("✅ System runs purely on Ragie + PydanticAI")
        logger.info("✅ No Graph-RAG, Neo4j, LightRAG, or Enterprise Bridge dependencies")
        return True
    else:
        logger.error("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_clean_tests())
    sys.exit(0 if success else 1)