#!/usr/bin/env python3
"""
Test Universal Response Models
=============================

Comprehensive test of universal response models that provide consistent
Ragie-enhanced responses across text and voice interactions.

Tests:
1. Universal response model creation
2. Ragie integration models
3. Cross-modal response adaptation
4. Enhanced clean intelligence service
5. Performance metrics and monitoring

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

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
    
    def __init__(self):
        self.responses = {
            'equipment': {
                'content': 'The Taylor C602 fryer operates at 350°F. Check heating elements and thermostat for temperature issues.',
                'confidence': 0.9,
                'sources': [
                    {'title': 'Equipment Manual', 'page': 12, 'content': 'Fryer troubleshooting guide'},
                    {'title': 'Technical Specs', 'page': 5, 'content': 'Temperature control system details'}
                ]
            },
            'procedure': {
                'content': 'Cleaning procedure: 1. Cool equipment 2. Remove parts 3. Clean with sanitizer 4. Rinse thoroughly 5. Reassemble',
                'confidence': 0.85,
                'sources': [{'title': 'Procedure Manual', 'page': 8, 'content': 'Daily cleaning procedures'}]
            },
            'safety': {
                'content': 'SAFETY CRITICAL: Hot oil safety requires PPE, proper ventilation, and emergency procedures. Never bypass safety systems.',
                'confidence': 0.95,
                'sources': [{'title': 'Safety Manual', 'page': 3, 'content': 'Hot oil safety protocols'}]
            }
        }
    
    async def search_documents(self, query: str, limit: int = 10, hybrid_search: bool = True):
        """Mock document search"""
        await asyncio.sleep(0.1)  # Simulate search time
        
        query_lower = query.lower()
        
        # Return appropriate response based on query
        if any(word in query_lower for word in ['equipment', 'fryer', 'troubleshoot']):
            return self.responses['equipment']
        elif any(word in query_lower for word in ['procedure', 'steps', 'clean']):
            return self.responses['procedure']
        elif any(word in query_lower for word in ['safety', 'danger', 'hot oil']):
            return self.responses['safety']
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
# UNIVERSAL RESPONSE MODEL TESTS
# ===============================================================================

async def test_universal_response_models():
    """Test universal response model creation"""
    logger.info("🔍 Testing Universal Response Models...")
    
    try:
        from models.universal_response_models import (
            UniversalQSRResponse, TextChatResponse, VoiceResponse, HybridResponse,
            RagieKnowledge, RagieCitation, RagieContext, AgentType, InteractionMode,
            ResponseFormat, SafetyLevel, UniversalResponseFactory
        )
        
        # Test RagieKnowledge creation
        knowledge = RagieKnowledge(
            content="Test knowledge content",
            confidence=0.9,
            source_title="Test Manual",
            source_page=12,
            agent_type=AgentType.EQUIPMENT,
            knowledge_type="factual",
            ragie_query="test query"
        )
        
        assert knowledge.content == "Test knowledge content"
        assert knowledge.confidence == 0.9
        assert knowledge.is_high_quality() == True
        assert knowledge.get_knowledge_id().startswith("equipment_")
        
        # Test RagieCitation creation
        citation = RagieCitation(
            citation_id="test_citation",
            citation_type="diagram",
            source_document="Test Manual",
            title="Test Diagram",
            agent_type=AgentType.EQUIPMENT,
            ragie_confidence=0.8,
            ragie_relevance=0.9
        )
        
        assert citation.citation_id == "test_citation"
        assert citation.citation_type == "diagram"
        assert citation.ragie_source == True
        
        # Test citation legacy format
        legacy_format = citation.to_legacy_format()
        assert legacy_format['citation_id'] == "test_citation"
        assert legacy_format['type'] == "diagram"
        
        # Test RagieContext creation
        context = RagieContext(
            session_id="test_session",
            interaction_mode=InteractionMode.TEXT_CHAT,
            agent_type=AgentType.EQUIPMENT
        )
        
        context.add_ragie_knowledge(knowledge)
        assert len(context.ragie_knowledge) == 1
        assert context.avg_ragie_confidence == 0.9
        
        logger.info("✅ Universal response models creation successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Universal response models test failed: {e}")
        raise

async def test_response_factory():
    """Test response factory functionality"""
    logger.info("🔍 Testing Response Factory...")
    
    try:
        from models.universal_response_models import (
            UniversalResponseFactory, RagieContext, RagieKnowledge, RagieCitation,
            AgentType, InteractionMode, ResponseFormat, SafetyLevel
        )
        
        # Create test context
        context = RagieContext(
            session_id="test_session",
            interaction_mode=InteractionMode.TEXT_CHAT,
            agent_type=AgentType.EQUIPMENT
        )
        
        # Create test knowledge
        knowledge = RagieKnowledge(
            content="Test knowledge",
            confidence=0.8,
            source_title="Test Manual",
            agent_type=AgentType.EQUIPMENT,
            knowledge_type="factual",
            ragie_query="test query"
        )
        
        # Create test citation
        citation = RagieCitation(
            citation_id="test_citation",
            citation_type="diagram",
            source_document="Test Manual",
            title="Test Diagram",
            agent_type=AgentType.EQUIPMENT,
            ragie_confidence=0.8,
            ragie_relevance=0.9
        )
        
        # Test text response creation
        text_response = UniversalResponseFactory.create_text_response(
            text_response="Test text response",
            agent_type=AgentType.EQUIPMENT,
            ragie_context=context,
            knowledge_sources=[knowledge],
            visual_citations=[citation]
        )
        
        assert text_response.text_response == "Test text response"
        assert text_response.primary_agent == AgentType.EQUIPMENT
        assert text_response.interaction_mode == InteractionMode.TEXT_CHAT
        assert text_response.response_format == ResponseFormat.TEXT_UI
        assert len(text_response.knowledge_sources) == 1
        assert len(text_response.visual_citations) == 1
        
        # Test voice response creation
        voice_response = UniversalResponseFactory.create_voice_response(
            text_response="Test voice response",
            agent_type=AgentType.SAFETY,
            ragie_context=context,
            knowledge_sources=[knowledge],
            visual_citations=[citation],
            safety_level=SafetyLevel.HIGH
        )
        
        assert voice_response.text_response == "Test voice response"
        assert voice_response.primary_agent == AgentType.SAFETY
        assert voice_response.interaction_mode == InteractionMode.VOICE_CHAT
        assert voice_response.response_format == ResponseFormat.VOICE_AUDIO
        assert voice_response.safety_level == SafetyLevel.HIGH
        
        # Test hybrid response creation
        hybrid_response = UniversalResponseFactory.create_hybrid_response(
            text_response="Test hybrid response",
            agent_type=AgentType.PROCEDURE,
            ragie_context=context,
            knowledge_sources=[knowledge],
            visual_citations=[citation]
        )
        
        assert hybrid_response.text_response == "Test hybrid response"
        assert hybrid_response.primary_agent == AgentType.PROCEDURE
        assert hybrid_response.interaction_mode == InteractionMode.HYBRID
        assert hybrid_response.response_format == ResponseFormat.HYBRID
        
        logger.info("✅ Response factory test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Response factory test failed: {e}")
        raise

async def test_response_adaptation():
    """Test response adaptation between modes"""
    logger.info("🔍 Testing Response Adaptation...")
    
    try:
        from models.universal_response_models import (
            UniversalResponseFactory, ResponseAdapter, RagieContext, 
            AgentType, InteractionMode, ResponseFormat, SafetyLevel
        )
        
        # Create test context
        context = RagieContext(
            session_id="test_session",
            interaction_mode=InteractionMode.TEXT_CHAT,
            agent_type=AgentType.EQUIPMENT
        )
        
        # Create text response
        text_response = UniversalResponseFactory.create_text_response(
            text_response="This is a test response with safety information. Check the equipment diagram.",
            agent_type=AgentType.EQUIPMENT,
            ragie_context=context,
            safety_level=SafetyLevel.MEDIUM,
            safety_warnings=["Ensure proper PPE"]
        )
        
        # Test text formatting
        formatted_text = text_response.format_for_ui()
        assert "This is a test response" in formatted_text
        assert "⚠️ Safety Warnings:" in formatted_text
        assert "Ensure proper PPE" in formatted_text
        
        # Test API format
        api_format = text_response.to_api_format()
        assert api_format['response'] == text_response.text_response
        assert api_format['agent'] == 'equipment'
        assert api_format['safety_priority'] == False  # Medium is not high/critical
        
        # Test adaptation to voice
        voice_response = ResponseAdapter.adapt_text_to_voice(text_response)
        assert voice_response.interaction_mode == InteractionMode.VOICE_CHAT
        assert voice_response.response_format == ResponseFormat.VOICE_AUDIO
        
        # Test voice optimization
        optimized_speech = voice_response.optimize_for_speech()
        assert "degrees" not in optimized_speech or "Fahrenheit" in optimized_speech
        
        # Test voice legacy format
        legacy_format = voice_response.to_legacy_voice_format()
        assert legacy_format['text_response'] == optimized_speech
        assert legacy_format['should_continue_listening'] == True
        assert legacy_format['safety_priority'] == False
        
        # Test adaptation back to text
        adapted_text = ResponseAdapter.adapt_voice_to_text(voice_response)
        assert adapted_text.interaction_mode == InteractionMode.TEXT_CHAT
        assert adapted_text.response_format == ResponseFormat.TEXT_UI
        
        logger.info("✅ Response adaptation test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Response adaptation test failed: {e}")
        raise

async def test_enhanced_clean_intelligence_service():
    """Test enhanced clean intelligence service"""
    logger.info("🔍 Testing Enhanced Clean Intelligence Service...")
    
    try:
        from services.enhanced_clean_intelligence_service import (
            EnhancedCleanIntelligenceService, create_enhanced_clean_intelligence_service
        )
        from models.universal_response_models import (
            TextChatResponse, VoiceResponse, HybridResponse, InteractionMode
        )
        
        # Create mock services
        mock_ragie = MockRagieService()
        mock_citation = MockCitationService()
        
        # Create enhanced service
        service = await create_enhanced_clean_intelligence_service(
            ragie_service=mock_ragie,
            citation_service=mock_citation
        )
        
        # Test text query processing
        text_response = await service.process_text_query(
            query="How do I troubleshoot the fryer temperature issue?",
            session_id="test_session",
            equipment_mentioned=["Taylor C602"]
        )
        
        assert isinstance(text_response, TextChatResponse)
        assert text_response.primary_agent.value == "equipment"
        assert text_response.interaction_mode == InteractionMode.TEXT_CHAT
        assert len(text_response.knowledge_sources) > 0
        assert text_response.confidence_score > 0.5
        
        # Test voice query processing
        voice_response = await service.process_voice_query(
            query="What are the safety procedures for hot oil?",
            session_id="test_session"
        )
        
        assert isinstance(voice_response, VoiceResponse)
        assert voice_response.primary_agent.value == "safety"
        assert voice_response.interaction_mode == InteractionMode.VOICE_CHAT
        assert voice_response.safety_level.value in ["high", "critical"]
        assert len(voice_response.safety_warnings) > 0
        
        # Test hybrid query processing
        hybrid_response = await service.process_hybrid_query(
            query="Show me the cleaning procedure steps",
            session_id="test_session"
        )
        
        assert isinstance(hybrid_response, HybridResponse)
        assert hybrid_response.primary_agent.value == "procedure"
        assert hybrid_response.interaction_mode == InteractionMode.HYBRID
        
        # Test response format adaptation
        adapted_voice = service.adapt_response_format(text_response, InteractionMode.VOICE_CHAT)
        assert adapted_voice.interaction_mode == InteractionMode.VOICE_CHAT
        
        # Test metrics
        metrics = service.get_response_metrics()
        assert metrics['total_responses'] == 3
        assert 'ragie_performance' in metrics
        assert 'interaction_modes' in metrics
        assert 'agent_usage' in metrics
        
        logger.info("✅ Enhanced clean intelligence service test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced clean intelligence service test failed: {e}")
        raise

async def test_performance_metrics():
    """Test performance metrics functionality"""
    logger.info("🔍 Testing Performance Metrics...")
    
    try:
        from models.universal_response_models import (
            ResponseMetrics, UniversalResponseFactory, RagieContext, RagieKnowledge,
            AgentType, InteractionMode, SafetyLevel
        )
        
        # Create metrics tracker
        metrics = ResponseMetrics()
        
        # Create test responses
        context = RagieContext(
            session_id="test_session",
            interaction_mode=InteractionMode.TEXT_CHAT,
            agent_type=AgentType.EQUIPMENT
        )
        
        knowledge = RagieKnowledge(
            content="Test knowledge",
            confidence=0.9,
            source_title="Test Manual",
            agent_type=AgentType.EQUIPMENT,
            knowledge_type="factual",
            ragie_query="test query"
        )
        
        context.add_ragie_knowledge(knowledge)
        
        # Test equipment response
        equipment_response = UniversalResponseFactory.create_text_response(
            text_response="Equipment response",
            agent_type=AgentType.EQUIPMENT,
            ragie_context=context,
            knowledge_sources=[knowledge],
            confidence_score=0.9,
            total_processing_time_ms=150.0
        )
        
        metrics.update_with_response(equipment_response)
        
        # Test safety response
        safety_response = UniversalResponseFactory.create_voice_response(
            text_response="Safety response",
            agent_type=AgentType.SAFETY,
            ragie_context=context,
            knowledge_sources=[knowledge],
            confidence_score=0.95,
            safety_level=SafetyLevel.CRITICAL,
            safety_warnings=["Critical safety warning"],
            total_processing_time_ms=200.0
        )
        
        metrics.update_with_response(safety_response)
        
        # Test metrics summary
        summary = metrics.get_summary()
        
        assert summary['total_responses'] == 2
        assert summary['avg_confidence'] > 0.9
        assert summary['high_quality_rate'] > 0.0
        assert summary['avg_response_time_ms'] == 175.0  # (150 + 200) / 2
        assert summary['interaction_modes']['text'] == 1
        assert summary['interaction_modes']['voice'] == 1
        assert summary['agent_usage']['equipment'] == 1
        assert summary['agent_usage']['safety'] == 1
        assert summary['safety_metrics']['critical_responses'] == 1
        assert summary['safety_metrics']['warnings_issued'] == 1
        
        logger.info("✅ Performance metrics test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance metrics test failed: {e}")
        raise

async def test_equipment_and_procedure_contexts():
    """Test equipment and procedure context creation"""
    logger.info("🔍 Testing Equipment and Procedure Contexts...")
    
    try:
        from models.universal_response_models import (
            RagieEquipmentContext, RagieProcedureContext, RagieKnowledge,
            AgentType, SafetyLevel
        )
        
        # Test equipment context
        equipment_knowledge = RagieKnowledge(
            content="Taylor C602 fryer operates at 350°F",
            confidence=0.9,
            source_title="Equipment Manual",
            agent_type=AgentType.EQUIPMENT,
            knowledge_type="factual",
            ragie_query="fryer temperature",
            equipment_context=["Taylor C602"]
        )
        
        equipment_context = RagieEquipmentContext(
            equipment_name="Taylor C602",
            equipment_type="fryer",
            manufacturer="Taylor",
            ragie_knowledge=[equipment_knowledge],
            safety_level=SafetyLevel.HIGH,
            safety_warnings=["Hot oil hazard", "Use proper PPE"]
        )
        
        assert equipment_context.equipment_name == "Taylor C602"
        assert equipment_context.equipment_type == "fryer"
        assert len(equipment_context.ragie_knowledge) == 1
        assert equipment_context.safety_level == SafetyLevel.HIGH
        
        # Test primary knowledge
        primary_knowledge = equipment_context.get_primary_knowledge()
        assert primary_knowledge.confidence == 0.9
        
        # Test safety critical info
        safety_info = equipment_context.get_safety_critical_info()
        assert len(safety_info) == 2
        assert "Hot oil hazard" in safety_info
        
        # Test procedure context
        procedure_knowledge = RagieKnowledge(
            content="Cleaning steps: 1. Cool equipment 2. Remove parts 3. Clean",
            confidence=0.85,
            source_title="Procedure Manual",
            agent_type=AgentType.PROCEDURE,
            knowledge_type="procedural",
            ragie_query="cleaning procedure"
        )
        
        procedure_context = RagieProcedureContext(
            procedure_name="Daily Cleaning",
            procedure_type="cleaning",
            ragie_knowledge=[procedure_knowledge],
            steps=[
                {"step_number": 1, "description": "Cool equipment", "safety_critical": False},
                {"step_number": 2, "description": "Remove parts", "safety_critical": False},
                {"step_number": 3, "description": "Clean with chemicals", "safety_critical": True}
            ],
            safety_requirements=["Use proper PPE", "Ensure ventilation"]
        )
        
        assert procedure_context.procedure_name == "Daily Cleaning"
        assert procedure_context.procedure_type == "cleaning"
        assert procedure_context.get_step_count() == 3
        
        # Test safety critical steps
        safety_steps = procedure_context.get_safety_critical_steps()
        assert len(safety_steps) == 1
        assert safety_steps[0]["step_number"] == 3
        
        logger.info("✅ Equipment and procedure contexts test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Equipment and procedure contexts test failed: {e}")
        raise

# ===============================================================================
# MAIN TEST RUNNER
# ===============================================================================

async def run_universal_response_tests():
    """Run all universal response model tests"""
    logger.info("🚀 Starting Universal Response Models Tests...")
    
    tests = [
        test_universal_response_models,
        test_response_factory,
        test_response_adaptation,
        test_enhanced_clean_intelligence_service,
        test_performance_metrics,
        test_equipment_and_procedure_contexts
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
        logger.info("🎉 All Universal Response Models Tests PASSED!")
        logger.info("✅ Universal intelligence across text and voice interactions")
        logger.info("✅ Consistent Ragie integration and knowledge management")
        logger.info("✅ Cross-modal response adaptation working")
        logger.info("✅ Enhanced clean intelligence service operational")
        logger.info("✅ Performance metrics and monitoring active")
        return True
    else:
        logger.error("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_universal_response_tests())
    sys.exit(0 if success else 1)