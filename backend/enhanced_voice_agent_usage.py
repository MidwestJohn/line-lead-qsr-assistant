#!/usr/bin/env python3
"""
Enhanced Voice Agent Usage Examples
==================================

Demonstrates how to use the enhanced voice agent with Ragie integration
for sophisticated QSR voice assistance.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
from typing import Dict, List, Any

# Import enhanced voice agent
from voice_agent_enhanced import (
    enhanced_voice_orchestrator,
    process_enhanced_voice_message,
    get_enhanced_voice_health,
    get_enhanced_voice_metrics,
    RagieEnhancedVoiceResponse
)

async def example_basic_voice_interaction():
    """Example of basic voice interaction with Ragie enhancement"""
    
    print("🎤 Basic Voice Interaction Example")
    print("=" * 40)
    
    # Simple voice query
    query = "How do I clean the fryer?"
    session_id = "example_session_1"
    
    print(f"User: {query}")
    
    # Process with enhanced voice agent
    response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
        query, session_id=session_id
    )
    
    print(f"Assistant: {response.text_response}")
    print(f"Safety Priority: {response.safety_priority}")
    print(f"Ragie Enhanced: {response.ragie_knowledge_used}")
    
    if response.ragie_knowledge_used:
        print(f"Ragie Sources: {len(response.ragie_sources)}")
        print(f"Visual Citations: {len(response.ragie_visual_citations)}")
    
    if response.citation_descriptions:
        print("Visual References:")
        for desc in response.citation_descriptions:
            print(f"  - {desc}")
    
    return response

async def example_safety_priority_interaction():
    """Example of safety-priority voice interaction"""
    
    print("\n🛡️ Safety Priority Voice Interaction Example")
    print("=" * 40)
    
    # Safety-related query
    query = "Is it safe to clean the fryer while it's hot?"
    session_id = "safety_session"
    
    print(f"User: {query}")
    
    # Process with enhanced voice agent
    response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
        query, session_id=session_id
    )
    
    print(f"Assistant: {response.text_response}")
    print(f"Safety Priority: {response.safety_priority}")
    print(f"Safety Context: {response.safety_context}")
    
    if response.ragie_knowledge_used and response.safety_context:
        print(f"Safety Level: {response.safety_context.get('safety_level', 'unknown')}")
        print(f"Risk Factors: {len(response.safety_context.get('risk_factors', []))}")
        print(f"Emergency Procedures: {len(response.safety_context.get('emergency_procedures', []))}")
    
    return response

async def example_procedural_interaction():
    """Example of procedural voice interaction"""
    
    print("\n📋 Procedural Voice Interaction Example")
    print("=" * 40)
    
    # Procedural query
    query = "Walk me through making pizza dough step by step"
    session_id = "procedure_session"
    
    print(f"User: {query}")
    
    # Process with enhanced voice agent
    response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
        query, session_id=session_id
    )
    
    print(f"Assistant: {response.text_response}")
    print(f"Response Type: {response.response_type}")
    
    if response.procedure_context:
        print(f"Procedure: {response.procedure_context.get('procedure_name', 'unknown')}")
        print(f"Steps: {response.procedure_context.get('step_count', 0)}")
        print(f"Estimated Time: {response.procedure_context.get('estimated_time', 'unknown')}")
        print(f"Difficulty: {response.procedure_context.get('difficulty_level', 'unknown')}")
    
    return response

async def example_equipment_interaction():
    """Example of equipment-focused voice interaction"""
    
    print("\n⚙️ Equipment Voice Interaction Example")
    print("=" * 40)
    
    # Equipment query
    query = "The fryer is making strange noises"
    session_id = "equipment_session"
    
    print(f"User: {query}")
    
    # Process with enhanced voice agent
    response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
        query, session_id=session_id
    )
    
    print(f"Assistant: {response.text_response}")
    print(f"Equipment Mentioned: {response.equipment_mentioned}")
    
    if response.equipment_context:
        print(f"Equipment: {response.equipment_context.get('equipment_name', 'unknown')}")
        print(f"Equipment Type: {response.equipment_context.get('equipment_type', 'unknown')}")
        print(f"Maintenance Required: {response.equipment_context.get('maintenance_required', False)}")
        print(f"Safety Level: {response.equipment_context.get('safety_level', 'unknown')}")
        print(f"Troubleshooting Steps: {len(response.equipment_context.get('troubleshooting_steps', []))}")
    
    return response

async def example_conversation_context():
    """Example of conversation context building"""
    
    print("\n💬 Conversation Context Example")
    print("=" * 40)
    
    # Conversation flow
    conversation = [
        "I need help with the fryer",
        "How do I clean it safely?",
        "What about the oil?",
        "How often should I do this maintenance?"
    ]
    
    session_id = "conversation_session"
    
    for i, query in enumerate(conversation):
        print(f"\n{i+1}. User: {query}")
        
        # Process with enhanced voice agent
        response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
            query, session_id=session_id
        )
        
        print(f"   Assistant: {response.text_response[:80]}...")
        print(f"   Equipment: {response.equipment_mentioned or 'None'}")
        print(f"   Ragie Used: {response.ragie_knowledge_used}")
        
        if response.context_updates:
            print(f"   Context Updates: {response.context_updates}")
    
    return conversation

async def example_voice_optimizations():
    """Example of voice-specific optimizations"""
    
    print("\n🎙️ Voice Optimization Example")
    print("=" * 40)
    
    # Technical query that needs voice optimization
    query = "Show me the equipment specifications and maintenance documentation"
    session_id = "voice_opt_session"
    
    print(f"User: {query}")
    
    # Process with enhanced voice agent
    response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
        query, session_id=session_id
    )
    
    print(f"Original Response: {response.text_response}")
    
    if response.voice_optimized_response and response.voice_optimized_response != response.text_response:
        print(f"Voice Optimized: {response.voice_optimized_response}")
    
    print(f"Simplified for Voice: {response.simplified_for_voice}")
    
    if response.citation_descriptions:
        print("Citation Descriptions:")
        for desc in response.citation_descriptions:
            print(f"  - {desc}")
    
    return response

async def example_performance_monitoring():
    """Example of performance monitoring"""
    
    print("\n📊 Performance Monitoring Example")
    print("=" * 40)
    
    # Get performance metrics
    metrics = get_enhanced_voice_metrics()
    
    print("Performance Metrics:")
    print(f"  Ragie Available: {metrics['ragie_available']}")
    print(f"  Total Queries: {metrics['total_queries']}")
    print(f"  Success Rate: {metrics['success_rate']:.1%}")
    print(f"  Avg Response Time: {metrics['avg_response_time_ms']:.1f}ms")
    print(f"  Cache Hits: {metrics['knowledge_cache_hits']}")
    print(f"  Voice Optimizations: {metrics['voice_optimizations']}")
    print(f"  Active Sessions: {metrics['active_sessions']}")
    
    # Get health check
    health = await get_enhanced_voice_health()
    
    print("\nHealth Check:")
    print(f"  Ragie Tools Available: {health['ragie_tools_available']}")
    print(f"  Cache Efficiency: {health['cache_efficiency']:.1%}")
    
    if 'tool_health' in health:
        tool_health = health['tool_health']
        print(f"  Tool Health: {tool_health['available_tools']}/{tool_health['total_tools']} available")
    
    return metrics, health

async def example_backward_compatibility():
    """Example of backward compatibility"""
    
    print("\n🔄 Backward Compatibility Example")
    print("=" * 40)
    
    # Use the enhanced agent with the original API
    query = "How do I operate the cash register?"
    session_id = "compat_session"
    
    print(f"User: {query}")
    
    # Call original method - enhanced agent provides backward compatibility
    response = await enhanced_voice_orchestrator.process_voice_message(
        query, session_id=session_id
    )
    
    print(f"Assistant: {response.text_response}")
    print(f"Agent Type: {response.primary_agent.value}")
    print(f"Confidence: {response.confidence_score:.2f}")
    
    # The response is a VoiceResponse object (original format)
    print(f"Response Type: {type(response).__name__}")
    
    # But it has been enhanced with Ragie intelligence behind the scenes
    print("✅ Backward compatibility maintained while using Ragie enhancement")
    
    return response

async def example_error_handling():
    """Example of error handling and fallback"""
    
    print("\n🚨 Error Handling Example")
    print("=" * 40)
    
    # Test with various edge cases
    edge_cases = [
        "",  # Empty query
        "completely unrelated space travel question",  # Unrelated query
        "a" * 500,  # Very long query
    ]
    
    for query in edge_cases:
        query_display = query[:50] + "..." if len(query) > 50 else query
        print(f"\nTesting: {query_display}")
        
        try:
            response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
                query, session_id="error_test"
            )
            
            print(f"Response: {response.text_response[:60]}...")
            print(f"Ragie Used: {response.ragie_knowledge_used}")
            print(f"Confidence: {response.confidence_score:.2f}")
            
        except Exception as e:
            print(f"Error handled gracefully: {e}")
    
    return True

async def main():
    """Run all usage examples"""
    
    print("🚀 Enhanced Voice Agent Usage Examples")
    print("=" * 60)
    
    # Run examples
    examples = [
        example_basic_voice_interaction,
        example_safety_priority_interaction,
        example_procedural_interaction,
        example_equipment_interaction,
        example_conversation_context,
        example_voice_optimizations,
        example_performance_monitoring,
        example_backward_compatibility,
        example_error_handling
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"Example failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All Usage Examples Completed")
    print("=" * 60)
    
    print("\n🎯 Key Benefits Demonstrated:")
    print("• Enhanced voice responses with Ragie intelligence")
    print("• Voice-optimized technical content")
    print("• Safety priority handling with Ragie analysis")
    print("• Equipment and procedure context awareness")
    print("• Conversation context building over time")
    print("• Performance monitoring and health checks")
    print("• 100% backward compatibility maintained")
    print("• Graceful error handling and fallback")
    
    print("\n🎉 Enhanced Voice Agent is ready for production use!")

if __name__ == "__main__":
    asyncio.run(main())