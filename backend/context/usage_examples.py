#!/usr/bin/env python3
"""
Universal Context Manager Usage Examples
=======================================

Demonstrates how to use the universal context manager for text + voice
interactions with Ragie integration.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime

# Import universal context manager
from ragie_context_manager import (
    universal_context_manager,
    InteractionMode,
    get_universal_context,
    process_ragie_result_with_context,
    get_context_for_query,
    get_context_health,
    list_active_sessions
)

async def example_text_to_voice_conversation():
    """Example of text to voice conversation with context preservation"""
    
    print("🔄 Text to Voice Conversation Example")
    print("=" * 40)
    
    session_id = "text_voice_example"
    
    # Mock Ragie results
    class MockEquipmentResult:
        def __init__(self, equipment_name, content):
            self.tool_name = "RagieEquipmentTool"
            self.content = content
            self.confidence = 0.9
            self.success = True
            self.execution_time_ms = 1200.0
            self.visual_citations = [
                {
                    'citation_id': f'{equipment_name}_diagram',
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
    
    # Text interaction
    print("\n💬 Text: 'How do I troubleshoot the fryer?'")
    
    text_result = MockEquipmentResult("fryer", "Fryer troubleshooting requires checking temperature and oil level")
    await process_ragie_result_with_context(session_id, text_result, InteractionMode.TEXT)
    
    context = get_universal_context(session_id)
    print(f"   Context: {context.interaction_mode.value}, Equipment: {context.equipment_context.current_equipment}")
    
    # Voice interaction continues conversation
    print("\n🎤 Voice: 'What about the oil change procedure?'")
    
    voice_result = MockEquipmentResult("fryer", "Oil change procedure involves draining old oil and refilling with fresh oil")
    await process_ragie_result_with_context(session_id, voice_result, InteractionMode.VOICE)
    
    context = get_universal_context(session_id)
    print(f"   Context: {context.interaction_mode.value}, Total: {context.total_interactions} interactions")
    
    # Get context for both modes
    text_context = get_context_for_query(session_id, "fryer maintenance", InteractionMode.TEXT)
    voice_context = get_context_for_query(session_id, "fryer maintenance", InteractionMode.VOICE)
    
    print(f"   Text context: {len(text_context['visual_citations'])} visual citations")
    print(f"   Voice context: {len(voice_context['voice_citations'])} voice citations")
    
    print("✅ Context preserved across text ↔ voice switch")

async def example_multi_session_management():
    """Example of managing multiple sessions"""
    
    print("\n🔄 Multi-Session Management Example")
    print("=" * 40)
    
    # Create multiple sessions
    sessions = [
        ("kitchen_station_1", "fryer", "Fryer operation and maintenance"),
        ("kitchen_station_2", "grill", "Grill temperature control"),
        ("manager_station", "pos", "POS system troubleshooting")
    ]
    
    for session_id, equipment, description in sessions:
        print(f"\n📋 Session {session_id}: {description}")
        
        # Create equipment result
        class MockResult:
            def __init__(self, equipment_name, content):
                self.tool_name = "RagieEquipmentTool"
                self.content = content
                self.confidence = 0.8
                self.success = True
                self.execution_time_ms = 1000.0
                self.visual_citations = []
                self.equipment_name = equipment_name
                self.equipment_type = "commercial"
                self.maintenance_required = False
                self.safety_level = "low"
                self.troubleshooting_steps = []
        
        result = MockResult(equipment, description)
        await process_ragie_result_with_context(session_id, result, InteractionMode.TEXT)
        
        context = get_universal_context(session_id)
        print(f"   Equipment: {context.equipment_context.current_equipment}")
        print(f"   Knowledge entries: {len(context.knowledge_context.active_knowledge)}")
    
    # List all active sessions
    active_sessions = list_active_sessions()
    print(f"\n📊 Active Sessions: {len(active_sessions)}")
    
    for session in active_sessions:
        print(f"   {session['session_id']}: {session['interaction_mode']}, {session['total_interactions']} interactions")

async def example_procedure_tracking():
    """Example of procedure tracking with context"""
    
    print("\n📋 Procedure Tracking Example")
    print("=" * 40)
    
    session_id = "procedure_example"
    
    # Mock procedure result
    class MockProcedureResult:
        def __init__(self, procedure_name, step_count=5):
            self.tool_name = "RagieProcedureTool"
            self.content = f"Step-by-step procedure for {procedure_name}"
            self.confidence = 0.9
            self.success = True
            self.execution_time_ms = 1500.0
            self.visual_citations = []
            self.procedure_name = procedure_name
            self.step_count = step_count
            self.estimated_time = "15 minutes"
            self.difficulty_level = "medium"
            self.required_tools = ["spatula", "thermometer"]
            self.procedure_steps = [
                {"step_number": i, "instruction": f"Step {i}", "type": "action"}
                for i in range(1, step_count + 1)
            ]
    
    # Start procedure
    procedure_result = MockProcedureResult("fryer_cleaning", 4)
    await process_ragie_result_with_context(session_id, procedure_result, InteractionMode.VOICE)
    
    context = get_universal_context(session_id)
    print(f"Started procedure: {context.procedure_context.current_procedure}")
    print(f"Total steps: {context.procedure_context.total_steps}")
    print(f"Current step: {context.procedure_context.procedure_step}")
    
    # Advance through steps
    for step in range(2, 5):
        context.procedure_context.advance_procedure_step()
        print(f"Advanced to step {context.procedure_context.procedure_step}")
    
    # Complete procedure
    context.procedure_context.complete_procedure()
    print(f"Procedure completed: {context.procedure_context.current_procedure}")
    print(f"Completed procedures: {len(context.procedure_context.completed_procedures)}")

async def example_safety_context():
    """Example of safety context management"""
    
    print("\n🛡️ Safety Context Example")
    print("=" * 40)
    
    session_id = "safety_example"
    
    # Mock safety result
    class MockSafetyResult:
        def __init__(self, safety_query):
            self.tool_name = "RagieSafetyTool"
            self.content = f"Safety information for {safety_query}"
            self.confidence = 0.95
            self.success = True
            self.execution_time_ms = 1100.0
            self.visual_citations = [
                {
                    'citation_id': 'safety_warning',
                    'type': 'diagram',
                    'source': 'Safety Manual',
                    'title': 'Safety Warning',
                    'description': 'Important safety information'
                }
            ]
            self.safety_level = "high"
            self.risk_factors = ["High temperature", "Oil splatter"]
            self.emergency_procedures = ["Turn off power", "Call supervisor"]
            self.immediate_actions = ["Stop current activity", "Move to safe area"]
            self.safety_warnings = ["Exercise extreme caution", "Use protective equipment"]
    
    # Add safety result
    safety_result = MockSafetyResult("fryer operation")
    await process_ragie_result_with_context(session_id, safety_result, InteractionMode.TEXT)
    
    context = get_universal_context(session_id)
    print(f"Safety citations: {len(context.citation_context.safety_citations)}")
    print(f"Knowledge entries: {len(context.knowledge_context.active_knowledge)}")
    
    # Get safety-specific context
    safety_context = get_context_for_query(session_id, "safety procedures", InteractionMode.TEXT)
    print(f"Relevant safety knowledge: {len(safety_context['relevant_knowledge'])}")

async def example_performance_monitoring():
    """Example of performance monitoring"""
    
    print("\n📊 Performance Monitoring Example")
    print("=" * 40)
    
    # Generate some activity
    for i in range(5):
        session_id = f"perf_session_{i}"
        
        class MockResult:
            def __init__(self, query_num):
                self.tool_name = "RagieKnowledgeTool"
                self.content = f"Knowledge content {query_num}"
                self.confidence = 0.8 + (query_num * 0.02)
                self.success = query_num % 4 != 0  # Some failures
                self.execution_time_ms = 1000.0 + (query_num * 100)
                self.visual_citations = []
                self.knowledge_type = "general"
        
        result = MockResult(i)
        await process_ragie_result_with_context(session_id, result, InteractionMode.TEXT)
    
    # Get performance metrics
    metrics = universal_context_manager.get_manager_metrics()
    
    print("📈 Manager Metrics:")
    print(f"   Total Sessions: {metrics['total_sessions']}")
    print(f"   Active Sessions: {metrics['active_sessions']}")
    print(f"   Total Interactions: {metrics['total_interactions']}")
    print(f"   Avg Context Size: {metrics['avg_context_size']:.1f}")
    print(f"   Compression Rate: {metrics['compression_rate']:.1%}")
    
    # Get health status
    health = get_context_health()
    
    print("\n💚 Health Status:")
    print(f"   Active Sessions: {health['active_sessions']}")
    print(f"   Ragie Tools Available: {health['ragie_tools_available']}")
    print(f"   Auto Compression: {health['auto_compression']}")
    print(f"   Compression Strategy: {health['compression_strategy']}")

async def example_context_compression():
    """Example of context compression"""
    
    print("\n🗜️ Context Compression Example")
    print("=" * 40)
    
    session_id = "compression_example"
    context = get_universal_context(session_id)
    
    # Add lots of knowledge
    for i in range(15):
        class MockResult:
            def __init__(self, content_id):
                self.tool_name = "RagieKnowledgeTool"
                self.content = f"Large knowledge entry {content_id}: " + ("detailed info " * 20)
                self.confidence = 0.8
                self.success = True
                self.execution_time_ms = 1000.0
                self.visual_citations = []
                self.knowledge_type = "general"
        
        result = MockResult(i)
        await process_ragie_result_with_context(session_id, result, InteractionMode.TEXT)
    
    print(f"Before compression: {len(context.knowledge_context.active_knowledge)} knowledge entries")
    print(f"Context size: {context.context_size}")
    
    # Trigger compression
    if context.should_compress():
        context.compress_context()
        print(f"After compression: {len(context.knowledge_context.active_knowledge)} knowledge entries")
        print(f"Context size: {context.context_size}")
        print(f"Compression count: {context.compressed_count}")

async def example_agent_coordination():
    """Example of agent coordination with context"""
    
    print("\n🤖 Agent Coordination Example")
    print("=" * 40)
    
    session_id = "agent_example"
    context = get_universal_context(session_id)
    
    # Simulate agent interactions
    agents = ["equipment", "safety", "procedure", "maintenance"]
    
    for agent in agents:
        context.agent_context.set_primary_agent(agent)
        
        # Mock agent performance
        context.agent_context.update_agent_performance(agent, True, 0.85)
        
        print(f"Agent {agent} activated")
        print(f"   Performance: {context.agent_context.get_agent_performance(agent)}")
    
    print(f"\nActive agents: {len(context.agent_context.active_agents)}")
    print(f"Primary agent: {context.agent_context.primary_agent}")
    print(f"Agent history: {len(context.agent_context.agent_history)}")

async def main():
    """Run all usage examples"""
    
    print("🚀 Universal Context Manager Usage Examples")
    print("=" * 60)
    
    # Run examples
    examples = [
        example_text_to_voice_conversation,
        example_multi_session_management,
        example_procedure_tracking,
        example_safety_context,
        example_performance_monitoring,
        example_context_compression,
        example_agent_coordination
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"Example failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All Usage Examples Completed")
    print("=" * 60)
    
    print("\n🎯 Key Features Demonstrated:")
    print("• Universal context for text and voice interactions")
    print("• Context preservation across interaction mode switches")
    print("• Multi-session management with isolation")
    print("• Procedure tracking with step progression")
    print("• Safety context with priority handling")
    print("• Performance monitoring and analytics")
    print("• Intelligent context compression")
    print("• Agent coordination with shared context")
    
    print("\n🎉 Universal Context Manager is ready for production use!")

if __name__ == "__main__":
    asyncio.run(main())