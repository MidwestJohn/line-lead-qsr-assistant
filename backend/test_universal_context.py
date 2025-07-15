#!/usr/bin/env python3
"""
Test Universal Context Manager with Ragie Integration
==================================================

Tests the universal context management system that works seamlessly
across text and voice interactions while maintaining Ragie knowledge.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_separator(title):
    """Print a section separator"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_context_info(context, title):
    """Print formatted context information"""
    print(f"\n📋 {title}:")
    print(f"   Session ID: {context.session_id}")
    print(f"   Interaction Mode: {context.interaction_mode.value}")
    print(f"   Total Interactions: {context.total_interactions}")
    print(f"   Text Interactions: {context.text_interactions}")
    print(f"   Voice Interactions: {context.voice_interactions}")
    print(f"   Context Size: {context.context_size}")
    print(f"   Knowledge Entries: {len(context.knowledge_context.active_knowledge)}")
    print(f"   Active Citations: {len(context.citation_context.active_citations)}")
    print(f"   Current Equipment: {context.equipment_context.current_equipment}")
    print(f"   Current Procedure: {context.procedure_context.current_procedure}")
    print(f"   Primary Agent: {context.agent_context.primary_agent}")

async def test_context_manager_creation():
    """Test creating and managing contexts"""
    
    print_separator("CONTEXT MANAGER CREATION TEST")
    
    try:
        from context.ragie_context_manager import (
            RagieContextManager,
            UniversalRagieContext,
            InteractionMode,
            universal_context_manager
        )
        
        print("✅ Context manager imports successful")
        
        # Test creating new context
        session_id = "test_session_1"
        context = universal_context_manager.create_context(session_id, InteractionMode.TEXT)
        
        print_context_info(context, "Created Context")
        
        # Test getting existing context
        retrieved_context = universal_context_manager.get_context(session_id)
        
        assert retrieved_context is not None, "Failed to retrieve context"
        assert retrieved_context.session_id == session_id, "Session ID mismatch"
        
        print("✅ Context creation and retrieval working")
        
        # Test get_or_create
        new_context = universal_context_manager.get_or_create_context("test_session_2", InteractionMode.VOICE)
        
        assert new_context.session_id == "test_session_2", "New context creation failed"
        assert new_context.interaction_mode == InteractionMode.VOICE, "Interaction mode not set"
        
        print("✅ Get or create context working")
        
        return True
        
    except Exception as e:
        print(f"❌ Context manager creation test failed: {e}")
        return False

async def test_ragie_integration():
    """Test Ragie integration with context"""
    
    print_separator("RAGIE INTEGRATION TEST")
    
    try:
        from context.ragie_context_manager import universal_context_manager, InteractionMode
        
        # Create mock Ragie result
        class MockRagieResult:
            def __init__(self, tool_name, content, confidence=0.8):
                self.tool_name = tool_name
                self.content = content
                self.confidence = confidence
                self.success = True
                self.execution_time_ms = 1000.0
                self.visual_citations = [
                    {
                        'citation_id': 'test_citation_1',
                        'type': 'diagram',
                        'source': 'QSR Manual',
                        'title': 'Equipment Diagram',
                        'description': 'Test equipment diagram'
                    }
                ]
        
        # Test with different tool results
        session_id = "ragie_test_session"
        
        # Test knowledge result
        knowledge_result = MockRagieResult("RagieKnowledgeTool", "This is test knowledge about fryer operation")
        await universal_context_manager.process_ragie_result(session_id, knowledge_result, InteractionMode.TEXT)
        
        context = universal_context_manager.get_context(session_id)
        print_context_info(context, "After Knowledge Result")
        
        # Test equipment result
        equipment_result = MockRagieResult("RagieEquipmentTool", "Fryer maintenance information")
        equipment_result.equipment_name = "fryer"
        equipment_result.equipment_type = "deep_fryer"
        equipment_result.maintenance_required = True
        equipment_result.safety_level = "high"
        equipment_result.troubleshooting_steps = ["Step 1", "Step 2"]
        
        await universal_context_manager.process_ragie_result(session_id, equipment_result, InteractionMode.VOICE)
        
        context = universal_context_manager.get_context(session_id)
        print_context_info(context, "After Equipment Result")
        
        # Verify context was updated
        assert context.total_interactions == 2, "Total interactions not updated"
        assert context.text_interactions == 1, "Text interactions not tracked"
        assert context.voice_interactions == 1, "Voice interactions not tracked"
        assert context.interaction_mode == InteractionMode.MIXED, "Mixed mode not detected"
        assert context.equipment_context.current_equipment == "fryer", "Equipment not set"
        
        print("✅ Ragie integration working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Ragie integration test failed: {e}")
        return False

async def test_context_preservation():
    """Test context preservation across interactions"""
    
    print_separator("CONTEXT PRESERVATION TEST")
    
    try:
        from context.ragie_context_manager import universal_context_manager, InteractionMode
        
        # Create mock results for conversation
        class MockProcedureResult:
            def __init__(self, procedure_name):
                self.tool_name = "RagieProcedureTool"
                self.content = f"Procedure for {procedure_name}"
                self.confidence = 0.9
                self.success = True
                self.execution_time_ms = 1500.0
                self.visual_citations = []
                self.procedure_name = procedure_name
                self.step_count = 5
                self.estimated_time = "15 minutes"
                self.difficulty_level = "medium"
                self.required_tools = ["spatula", "thermometer"]
                self.procedure_steps = [
                    {"step_number": 1, "instruction": "Step 1", "type": "action"},
                    {"step_number": 2, "instruction": "Step 2", "type": "action"}
                ]
        
        session_id = "preservation_test"
        
        # Simulate conversation flow
        interactions = [
            (InteractionMode.TEXT, "fryer_cleaning", "Start cleaning procedure"),
            (InteractionMode.VOICE, "fryer_cleaning", "Continue with step 2"),
            (InteractionMode.TEXT, "fryer_cleaning", "Complete procedure"),
            (InteractionMode.VOICE, "oil_change", "Start oil change procedure")
        ]
        
        for mode, procedure, description in interactions:
            procedure_result = MockProcedureResult(procedure)
            await universal_context_manager.process_ragie_result(session_id, procedure_result, mode)
            
            context = universal_context_manager.get_context(session_id)
            print(f"   {description}: {context.interaction_mode.value} mode, {context.total_interactions} interactions")
        
        # Verify context preservation
        final_context = universal_context_manager.get_context(session_id)
        
        assert final_context.total_interactions == 4, "Interactions not preserved"
        assert final_context.text_interactions == 2, "Text interactions not preserved"
        assert final_context.voice_interactions == 2, "Voice interactions not preserved"
        assert final_context.interaction_mode == InteractionMode.MIXED, "Mixed mode not preserved"
        assert final_context.procedure_context.current_procedure == "oil_change", "Procedure not preserved"
        
        print("✅ Context preservation working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Context preservation test failed: {e}")
        return False

async def test_context_compression():
    """Test context compression functionality"""
    
    print_separator("CONTEXT COMPRESSION TEST")
    
    try:
        from context.ragie_context_manager import (
            universal_context_manager, 
            InteractionMode,
            ContextCompressionStrategy
        )
        
        # Create context with lots of data
        session_id = "compression_test"
        context = universal_context_manager.create_context(session_id, InteractionMode.TEXT)
        
        # Add lots of knowledge entries
        for i in range(20):
            class MockKnowledgeResult:
                def __init__(self, content_id):
                    self.tool_name = "RagieKnowledgeTool"
                    self.content = f"Knowledge entry {content_id}: " + "x" * 100
                    self.confidence = 0.8
                    self.success = True
                    self.execution_time_ms = 1000.0
                    self.visual_citations = []
                    self.knowledge_type = "general"
            
            result = MockKnowledgeResult(i)
            await universal_context_manager.process_ragie_result(session_id, result, InteractionMode.TEXT)
        
        print(f"   Before compression: {len(context.knowledge_context.active_knowledge)} knowledge entries")
        
        # Test compression
        context.compress_context(ContextCompressionStrategy.RECENT_ONLY)
        
        print(f"   After compression: {len(context.knowledge_context.active_knowledge)} knowledge entries")
        print(f"   Compression count: {context.compressed_count}")
        
        # Verify compression worked
        assert context.compressed_count > 0, "Compression count not updated"
        
        print("✅ Context compression working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Context compression test failed: {e}")
        return False

async def test_query_context():
    """Test getting context for query processing"""
    
    print_separator("QUERY CONTEXT TEST")
    
    try:
        from context.ragie_context_manager import universal_context_manager, InteractionMode
        
        # Setup context with data
        session_id = "query_context_test"
        
        # Add some knowledge
        class MockKnowledgeResult:
            def __init__(self, content, knowledge_type="general"):
                self.tool_name = "RagieKnowledgeTool"
                self.content = content
                self.confidence = 0.9
                self.success = True
                self.execution_time_ms = 1000.0
                self.visual_citations = []
                self.knowledge_type = knowledge_type
        
        # Add fryer knowledge
        fryer_result = MockKnowledgeResult("Fryer operation requires proper temperature control", "equipment")
        await universal_context_manager.process_ragie_result(session_id, fryer_result, InteractionMode.TEXT)
        
        # Test getting context for query
        query_context = universal_context_manager.get_context_for_query(
            session_id, 
            "How do I clean the fryer?", 
            InteractionMode.TEXT
        )
        
        print("📋 Query Context:")
        print(f"   Session ID: {query_context['session_id']}")
        print(f"   Interaction Mode: {query_context['interaction_mode']}")
        print(f"   Total Interactions: {query_context['total_interactions']}")
        print(f"   Relevant Knowledge: {len(query_context['relevant_knowledge'])}")
        print(f"   Current Equipment: {query_context['current_equipment']}")
        print(f"   Session Duration: {query_context['session_duration']:.1f}s")
        
        # Test voice context
        voice_context = universal_context_manager.get_context_for_query(
            session_id,
            "How do I clean the fryer?",
            InteractionMode.VOICE
        )
        
        print("\n📋 Voice Context:")
        print(f"   Voice Citations: {len(voice_context.get('voice_citations', []))}")
        print(f"   Visual Citations: {len(voice_context.get('visual_citations', []))}")
        
        # Verify context structure
        assert 'session_id' in query_context, "Session ID missing from context"
        assert 'interaction_mode' in query_context, "Interaction mode missing"
        assert 'relevant_knowledge' in query_context, "Relevant knowledge missing"
        
        print("✅ Query context working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Query context test failed: {e}")
        return False

async def test_performance_tracking():
    """Test performance tracking functionality"""
    
    print_separator("PERFORMANCE TRACKING TEST")
    
    try:
        from context.ragie_context_manager import universal_context_manager, InteractionMode
        
        # Get initial metrics
        initial_metrics = universal_context_manager.get_manager_metrics()
        
        print("📊 Initial Metrics:")
        print(f"   Total Sessions: {initial_metrics['total_sessions']}")
        print(f"   Active Sessions: {initial_metrics['active_sessions']}")
        
        # Create multiple sessions
        for i in range(3):
            session_id = f"perf_test_{i}"
            context = universal_context_manager.create_context(session_id, InteractionMode.TEXT)
            
            # Add some activity
            class MockResult:
                def __init__(self):
                    self.tool_name = "RagieKnowledgeTool"
                    self.content = f"Test content {i}"
                    self.confidence = 0.8
                    self.success = True
                    self.execution_time_ms = 1000.0 + i * 100
                    self.visual_citations = []
                    self.knowledge_type = "general"
            
            result = MockResult()
            await universal_context_manager.process_ragie_result(session_id, result, InteractionMode.TEXT)
        
        # Get updated metrics
        updated_metrics = universal_context_manager.get_manager_metrics()
        
        print("\n📊 Updated Metrics:")
        print(f"   Total Sessions: {updated_metrics['total_sessions']}")
        print(f"   Active Sessions: {updated_metrics['active_sessions']}")
        print(f"   Total Interactions: {updated_metrics['total_interactions']}")
        print(f"   Avg Context Size: {updated_metrics['avg_context_size']:.1f}")
        
        # Get health status
        health = universal_context_manager.get_health_status()
        
        print("\n💚 Health Status:")
        print(f"   Active Sessions: {health['active_sessions']}")
        print(f"   Ragie Tools Available: {health['ragie_tools_available']}")
        print(f"   Auto Compression: {health['auto_compression']}")
        print(f"   Compression Strategy: {health['compression_strategy']}")
        
        # List active sessions
        sessions = universal_context_manager.list_active_sessions()
        
        print(f"\n📋 Active Sessions: {len(sessions)}")
        for session in sessions[:3]:
            print(f"   {session['session_id']}: {session['interaction_mode']}, {session['total_interactions']} interactions")
        
        # Verify metrics updated
        assert updated_metrics['total_sessions'] > initial_metrics['total_sessions'], "Total sessions not updated"
        assert updated_metrics['active_sessions'] > initial_metrics['active_sessions'], "Active sessions not updated"
        
        print("✅ Performance tracking working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance tracking test failed: {e}")
        return False

async def test_cross_modal_interaction():
    """Test cross-modal interaction (text ↔ voice)"""
    
    print_separator("CROSS-MODAL INTERACTION TEST")
    
    try:
        from context.ragie_context_manager import universal_context_manager, InteractionMode
        
        session_id = "cross_modal_test"
        
        # Start with text interaction
        class MockEquipmentResult:
            def __init__(self, equipment_name):
                self.tool_name = "RagieEquipmentTool"
                self.content = f"Equipment information for {equipment_name}"
                self.confidence = 0.9
                self.success = True
                self.execution_time_ms = 1200.0
                self.visual_citations = [
                    {
                        'citation_id': 'equipment_diagram',
                        'type': 'diagram',
                        'source': 'Equipment Manual',
                        'title': f'{equipment_name} Diagram',
                        'description': f'Technical diagram for {equipment_name}'
                    }
                ]
                self.equipment_name = equipment_name
                self.equipment_type = "commercial"
                self.maintenance_required = True
                self.safety_level = "medium"
                self.troubleshooting_steps = ["Check power", "Verify settings"]
        
        print("🔄 Testing text to voice transition...")
        
        # Text interaction
        equipment_result = MockEquipmentResult("fryer")
        await universal_context_manager.process_ragie_result(session_id, equipment_result, InteractionMode.TEXT)
        
        context = universal_context_manager.get_context(session_id)
        print(f"   Text interaction: {context.interaction_mode.value}, equipment: {context.equipment_context.current_equipment}")
        
        # Voice interaction on same equipment
        voice_result = MockEquipmentResult("fryer")
        await universal_context_manager.process_ragie_result(session_id, voice_result, InteractionMode.VOICE)
        
        context = universal_context_manager.get_context(session_id)
        print(f"   Voice interaction: {context.interaction_mode.value}, equipment: {context.equipment_context.current_equipment}")
        
        # Test context retrieval for both modes
        text_context = universal_context_manager.get_context_for_query(session_id, "fryer status", InteractionMode.TEXT)
        voice_context = universal_context_manager.get_context_for_query(session_id, "fryer status", InteractionMode.VOICE)
        
        print(f"   Text context citations: {len(text_context.get('visual_citations', []))}")
        print(f"   Voice context citations: {len(voice_context.get('voice_citations', []))}")
        
        # Verify cross-modal behavior
        assert context.interaction_mode == InteractionMode.MIXED, "Mixed mode not detected"
        assert context.text_interactions == 1, "Text interactions not tracked"
        assert context.voice_interactions == 1, "Voice interactions not tracked"
        assert context.equipment_context.current_equipment == "fryer", "Equipment context not preserved"
        
        print("✅ Cross-modal interaction working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Cross-modal interaction test failed: {e}")
        return False

async def test_context_cleanup():
    """Test context cleanup and session management"""
    
    print_separator("CONTEXT CLEANUP TEST")
    
    try:
        from context.ragie_context_manager import RagieContextManager, InteractionMode
        
        # Create temporary context manager for testing
        temp_manager = RagieContextManager()
        temp_manager.session_timeout = timedelta(seconds=1)  # Short timeout for testing
        
        # Create some contexts
        for i in range(3):
            session_id = f"cleanup_test_{i}"
            context = temp_manager.create_context(session_id, InteractionMode.TEXT)
        
        print(f"   Created {len(temp_manager.contexts)} contexts")
        
        # Wait for timeout
        await asyncio.sleep(2)
        
        # Run cleanup
        temp_manager.cleanup_expired_sessions()
        
        print(f"   After cleanup: {len(temp_manager.contexts)} contexts")
        
        # Verify cleanup worked
        assert len(temp_manager.contexts) == 0, "Contexts not cleaned up"
        
        print("✅ Context cleanup working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Context cleanup test failed: {e}")
        return False

async def main():
    """Run all universal context tests"""
    
    print("🚀 Starting Universal Context Manager Tests")
    print("=" * 60)
    
    # Run tests
    tests = [
        test_context_manager_creation,
        test_ragie_integration,
        test_context_preservation,
        test_context_compression,
        test_query_context,
        test_performance_tracking,
        test_cross_modal_interaction,
        test_context_cleanup
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if all(results):
        print("\n✅ All tests passed! Universal context manager is working correctly.")
        print("🎉 Step 4.2: Universal Context with Ragie - COMPLETE")
        return True
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Universal Context Manager with Ragie is ready!")
    else:
        print("\n⚠️ Universal Context Manager needs attention before deployment")
        exit(1)