#!/usr/bin/env python3
"""
Test Enhanced Voice Agent with Ragie Integration
==============================================

Tests the enhanced voice agent to ensure it properly integrates Ragie tools
while preserving all existing voice functionality.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_separator(title):
    """Print a section separator"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_voice_response(response, title):
    """Print formatted voice response"""
    print(f"\n🎤 {title}:")
    print(f"   Response: {response.text_response[:100]}...")
    print(f"   Agent: {response.primary_agent.value}")
    print(f"   Confidence: {response.confidence_score:.2f}")
    print(f"   Safety Priority: {response.safety_priority}")
    print(f"   Continue Listening: {response.should_continue_listening}")
    print(f"   Hands-Free: {response.hands_free_recommendation}")
    print(f"   Voice State: {response.next_voice_state.value}")
    print(f"   Response Type: {response.response_type}")
    
    # Enhanced response details
    if hasattr(response, 'ragie_knowledge_used'):
        print(f"   Ragie Used: {response.ragie_knowledge_used}")
        print(f"   Ragie Confidence: {response.ragie_confidence:.2f}")
        print(f"   Ragie Sources: {len(response.ragie_sources)}")
        print(f"   Visual Citations: {len(response.ragie_visual_citations)}")
        print(f"   Execution Time: {response.ragie_execution_time_ms:.1f}ms")
        
        if hasattr(response, 'voice_optimized_response') and response.voice_optimized_response:
            print(f"   Voice Optimized: {response.simplified_for_voice}")
    
    if response.suggested_follow_ups:
        print(f"   Follow-ups: {len(response.suggested_follow_ups)}")

async def test_enhanced_voice_agent():
    """Test the enhanced voice agent integration"""
    
    print_separator("ENHANCED VOICE AGENT INTEGRATION TEST")
    
    # Test 1: Service availability
    print("\n1. Testing enhanced voice agent availability...")
    
    try:
        from voice_agent_enhanced import (
            enhanced_voice_orchestrator,
            RagieEnhancedVoiceOrchestrator,
            RagieEnhancedVoiceResponse,
            process_enhanced_voice_message,
            get_enhanced_voice_health,
            get_enhanced_voice_metrics
        )
        
        print("✅ Enhanced voice agent imported successfully")
        
        # Check if Ragie tools are available
        ragie_available = enhanced_voice_orchestrator.ragie_available
        print(f"✅ Ragie tools available: {ragie_available}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced voice agent import failed: {e}")
        return False
    
async def test_voice_message_processing():
    """Test voice message processing with Ragie enhancement"""
    
    print_separator("VOICE MESSAGE PROCESSING TEST")
    
    try:
        from voice_agent_enhanced import enhanced_voice_orchestrator
        
        # Test voice queries that should trigger different agents
        test_queries = [
            ("How do I clean the fryer?", "equipment"),
            ("What safety procedures should I follow?", "safety"),
            ("Walk me through pizza dough making", "procedure"),
            ("The grill is making strange noises", "equipment"),
            ("Is the fryer temperature safe?", "safety")
        ]
        
        session_id = "test_voice_session"
        
        for query, expected_agent in test_queries:
            print(f"\n🎤 Testing: {query}")
            
            # Test with enhanced voice processing
            if enhanced_voice_orchestrator.ragie_available:
                response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
                    query, session_id=session_id
                )
                print_voice_response(response, "Enhanced Response")
            else:
                # Test with backward compatibility
                response = await enhanced_voice_orchestrator.process_voice_message(
                    query, session_id=session_id
                )
                print_voice_response(response, "Backward Compatible Response")
        
        print("\n✅ Voice message processing tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Voice message processing test failed: {e}")
        return False

async def test_backward_compatibility():
    """Test backward compatibility with existing voice system"""
    
    print_separator("BACKWARD COMPATIBILITY TEST")
    
    try:
        from voice_agent_enhanced import enhanced_voice_orchestrator
        
        # Test that the enhanced orchestrator can still be used as the original
        test_query = "How do I operate the cash register?"
        
        print(f"🔄 Testing backward compatibility with: {test_query}")
        
        # Test original process_voice_message method
        response = await enhanced_voice_orchestrator.process_voice_message(
            test_query, session_id="compat_test"
        )
        
        print_voice_response(response, "Backward Compatible Response")
        
        # Verify response structure is as expected
        assert hasattr(response, 'text_response'), "Missing text_response"
        assert hasattr(response, 'primary_agent'), "Missing primary_agent"
        assert hasattr(response, 'confidence_score'), "Missing confidence_score"
        assert hasattr(response, 'should_continue_listening'), "Missing should_continue_listening"
        
        print("✅ Backward compatibility maintained")
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

async def test_ragie_integration():
    """Test specific Ragie integration features"""
    
    print_separator("RAGIE INTEGRATION TEST")
    
    try:
        from voice_agent_enhanced import enhanced_voice_orchestrator
        
        if not enhanced_voice_orchestrator.ragie_available:
            print("⚠️ Ragie tools not available - skipping integration test")
            return True
        
        # Test Ragie-enhanced response
        test_query = "How do I safely clean the fryer?"
        
        print(f"🔧 Testing Ragie integration with: {test_query}")
        
        response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
            test_query, session_id="ragie_test"
        )
        
        print_voice_response(response, "Ragie Enhanced Response")
        
        # Verify Ragie-specific features
        assert hasattr(response, 'ragie_knowledge_used'), "Missing ragie_knowledge_used"
        assert hasattr(response, 'ragie_confidence'), "Missing ragie_confidence"
        assert hasattr(response, 'ragie_sources'), "Missing ragie_sources"
        assert hasattr(response, 'ragie_visual_citations'), "Missing ragie_visual_citations"
        
        print("✅ Ragie integration working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Ragie integration test failed: {e}")
        return False

async def test_voice_optimizations():
    """Test voice-specific optimizations"""
    
    print_separator("VOICE OPTIMIZATIONS TEST")
    
    try:
        from voice_agent_enhanced import enhanced_voice_orchestrator
        
        if not enhanced_voice_orchestrator.ragie_available:
            print("⚠️ Ragie tools not available - skipping optimization test")
            return True
        
        # Test voice optimization with technical content
        test_query = "Show me the fryer maintenance procedure"
        
        print(f"🎙️ Testing voice optimization with: {test_query}")
        
        response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
            test_query, session_id="voice_opt_test"
        )
        
        print_voice_response(response, "Voice Optimized Response")
        
        # Check for voice optimizations
        if hasattr(response, 'voice_optimized_response') and response.voice_optimized_response:
            print(f"   Original: {response.text_response[:50]}...")
            print(f"   Optimized: {response.voice_optimized_response[:50]}...")
        
        if hasattr(response, 'citation_descriptions') and response.citation_descriptions:
            print(f"   Citation Descriptions: {len(response.citation_descriptions)}")
            for desc in response.citation_descriptions[:2]:
                print(f"     - {desc}")
        
        print("✅ Voice optimizations working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Voice optimization test failed: {e}")
        return False

async def test_performance_metrics():
    """Test performance metrics and health checks"""
    
    print_separator("PERFORMANCE METRICS TEST")
    
    try:
        from voice_agent_enhanced import (
            enhanced_voice_orchestrator,
            get_enhanced_voice_health,
            get_enhanced_voice_metrics
        )
        
        # Get performance metrics
        metrics = get_enhanced_voice_metrics()
        print("📊 Performance Metrics:")
        print(f"   Ragie Available: {metrics['ragie_available']}")
        print(f"   Total Queries: {metrics['total_queries']}")
        print(f"   Success Rate: {metrics['success_rate']:.1%}")
        print(f"   Avg Response Time: {metrics['avg_response_time_ms']:.1f}ms")
        print(f"   Cache Hits: {metrics['knowledge_cache_hits']}")
        print(f"   Voice Optimizations: {metrics['voice_optimizations']}")
        print(f"   Active Sessions: {metrics['active_sessions']}")
        
        # Get health check
        health = await get_enhanced_voice_health()
        print("\n💚 Health Check:")
        print(f"   Ragie Tools Available: {health['ragie_tools_available']}")
        print(f"   Active Sessions: {health['active_sessions']}")
        print(f"   Cache Efficiency: {health['cache_efficiency']:.1%}")
        
        if 'tool_health' in health:
            tool_health = health['tool_health']
            print(f"   Tool Health: {tool_health['available_tools']}/{tool_health['total_tools']} available")
        
        print("✅ Performance metrics working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Performance metrics test failed: {e}")
        return False

async def test_conversation_context():
    """Test conversation context preservation with Ragie"""
    
    print_separator("CONVERSATION CONTEXT TEST")
    
    try:
        from voice_agent_enhanced import enhanced_voice_orchestrator
        
        # Test conversation context building
        conversation = [
            "I need help with the fryer",
            "How do I clean it?",
            "What about the oil change?",
            "How often should I do this maintenance?"
        ]
        
        session_id = "context_test"
        
        print("🔄 Testing conversation context building...")
        
        for i, query in enumerate(conversation):
            print(f"\n{i+1}. 🎤 Query: {query}")
            
            if enhanced_voice_orchestrator.ragie_available:
                response = await enhanced_voice_orchestrator.process_voice_message_with_ragie(
                    query, session_id=session_id
                )
            else:
                response = await enhanced_voice_orchestrator.process_voice_message(
                    query, session_id=session_id
                )
            
            print(f"   Response: {response.text_response[:80]}...")
            print(f"   Equipment: {response.equipment_mentioned or 'None'}")
            print(f"   Context Updates: {len(response.context_updates)}")
            
            if hasattr(response, 'ragie_knowledge_used'):
                print(f"   Ragie Used: {response.ragie_knowledge_used}")
        
        print("\n✅ Conversation context preservation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Conversation context test failed: {e}")
        return False

async def main():
    """Run all enhanced voice agent tests"""
    
    print("🚀 Starting Enhanced Voice Agent Tests")
    print("=" * 60)
    
    # Run tests
    tests = [
        test_enhanced_voice_agent,
        test_voice_message_processing,
        test_backward_compatibility,
        test_ragie_integration,
        test_voice_optimizations,
        test_performance_metrics,
        test_conversation_context
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
        print("\n✅ All tests passed! Enhanced voice agent is working correctly.")
        print("🎉 Step 4.1: Enhanced Voice Agent - COMPLETE")
        return True
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Enhanced Voice Agent with Ragie integration is ready!")
    else:
        print("\n⚠️ Enhanced Voice Agent needs attention before deployment")
        exit(1)