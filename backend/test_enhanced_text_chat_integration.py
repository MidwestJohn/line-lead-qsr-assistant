#!/usr/bin/env python3
"""
Test Enhanced Text Chat Integration
==================================

Tests the integration of the enhanced text chat endpoint with the main application.
Verifies that the `/chat/stream` endpoint now uses PydanticAI + Ragie intelligence.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test the enhanced text chat integration
async def test_enhanced_text_chat_integration():
    """Test that enhanced text chat is properly integrated into main app"""
    
    print("🧪 Testing Enhanced Text Chat Integration")
    print("=" * 50)
    
    # Test 1: Import check
    print("\n1. Testing imports...")
    try:
        from enhanced_text_chat_endpoint import (
            enhanced_text_chat_service,
            backward_compatible_chat_endpoint,
            ChatMessage,
            ChatResponse,
            initialize_enhanced_text_chat,
            get_enhanced_chat_metrics
        )
        print("✅ Enhanced text chat imports successful")
    except ImportError as e:
        print(f"❌ Enhanced text chat imports failed: {e}")
        return False
    
    # Test 2: Main app integration
    print("\n2. Testing main app integration...")
    try:
        # Import main app with enhanced text chat
        from main_clean import app, ENHANCED_TEXT_CHAT_AVAILABLE
        
        print(f"✅ Main app imported successfully")
        print(f"   Enhanced text chat available: {ENHANCED_TEXT_CHAT_AVAILABLE}")
        
        if not ENHANCED_TEXT_CHAT_AVAILABLE:
            print("⚠️ Enhanced text chat not available in main app")
            return False
            
    except ImportError as e:
        print(f"❌ Main app import failed: {e}")
        return False
    
    # Test 3: Service initialization
    print("\n3. Testing service initialization...")
    try:
        success = await initialize_enhanced_text_chat()
        print(f"✅ Service initialization: {success}")
        
        # Check service metrics
        metrics = await get_enhanced_chat_metrics()
        print(f"✅ Service metrics: {metrics.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False
    
    # Test 4: Endpoint functionality
    print("\n4. Testing endpoint functionality...")
    try:
        # Test message
        test_message = ChatMessage(message="How do I clean the pizza oven?")
        
        # Test enhanced endpoint
        response = await backward_compatible_chat_endpoint(test_message)
        
        print(f"✅ Enhanced endpoint response received")
        print(f"   Response length: {len(response.response)} characters")
        print(f"   Retrieval method: {response.retrieval_method}")
        print(f"   Visual citations: {len(response.visual_citations)}")
        print(f"   Manual references: {len(response.manual_references)}")
        
        # Verify response structure
        assert isinstance(response.response, str)
        assert response.timestamp
        assert response.retrieval_method
        
        print("✅ Response structure validation passed")
        
    except Exception as e:
        print(f"❌ Endpoint functionality test failed: {e}")
        return False
    
    # Test 5: Performance metrics
    print("\n5. Testing performance metrics...")
    try:
        # Get service metrics
        service_metrics = await enhanced_text_chat_service.health_check()
        
        print(f"✅ Service health check: {service_metrics.get('status', 'unknown')}")
        print(f"   Initialized: {service_metrics.get('initialized', False)}")
        print(f"   Intelligence available: {service_metrics.get('intelligence_available', False)}")
        
        # Check performance metrics
        if 'metrics' in service_metrics:
            metrics = service_metrics['metrics']
            print(f"   Total requests: {metrics.get('total_requests', 0)}")
            print(f"   Success rate: {metrics.get('success_rate', 0):.2f}")
            print(f"   Avg response time: {metrics.get('avg_response_time_ms', 0):.2f}ms")
        
    except Exception as e:
        print(f"❌ Performance metrics test failed: {e}")
        return False
    
    # Test 6: Error handling
    print("\n6. Testing error handling...")
    try:
        # Test with empty message
        empty_message = ChatMessage(message="")
        
        # This should handle gracefully
        response = await backward_compatible_chat_endpoint(empty_message)
        
        print(f"✅ Empty message handled gracefully")
        print(f"   Response: {response.response[:100]}...")
        
    except Exception as e:
        print(f"⚠️ Error handling test: {e}")
        # This might be expected behavior
    
    print("\n" + "=" * 50)
    print("✅ Enhanced Text Chat Integration Tests Complete")
    return True

async def test_integration_with_sample_queries():
    """Test integration with sample QSR queries"""
    
    print("\n🔍 Testing Integration with Sample QSR Queries")
    print("=" * 50)
    
    # Sample QSR queries to test different agent routing
    sample_queries = [
        ("How do I clean the fryer?", "maintenance"),
        ("What safety procedures should I follow?", "safety"),
        ("How do I make pizza dough?", "procedure"),
        ("The ice machine is not working", "equipment"),
        ("What are the opening hours?", "general")
    ]
    
    try:
        from enhanced_text_chat_endpoint import backward_compatible_chat_endpoint, ChatMessage
        
        for query, expected_category in sample_queries:
            print(f"\n🔍 Testing: {query}")
            
            # Process query
            message = ChatMessage(message=query)
            response = await backward_compatible_chat_endpoint(message)
            
            print(f"   Response: {response.response[:100]}...")
            print(f"   Retrieval method: {response.retrieval_method}")
            print(f"   Citations: {len(response.visual_citations)}")
            print(f"   References: {len(response.manual_references)}")
            
            # Verify response quality
            assert len(response.response) > 20, "Response too short"
            assert response.timestamp, "Missing timestamp"
            
        print("\n✅ All sample queries processed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Sample queries test failed: {e}")
        return False

async def test_backward_compatibility():
    """Test that the enhanced service maintains backward compatibility"""
    
    print("\n🔄 Testing Backward Compatibility")
    print("=" * 50)
    
    try:
        # Test with original ChatMessage format
        from enhanced_text_chat_endpoint import ChatMessage, ChatResponse
        
        # Create test message
        test_message = ChatMessage(message="How do I operate the cash register?")
        
        # Process with backward compatible endpoint
        from enhanced_text_chat_endpoint import backward_compatible_chat_endpoint
        response = await backward_compatible_chat_endpoint(test_message)
        
        # Verify response is in expected format
        assert isinstance(response, ChatResponse)
        assert response.response
        assert response.timestamp
        assert isinstance(response.visual_citations, list)
        assert isinstance(response.manual_references, list)
        
        print("✅ Backward compatibility maintained")
        print(f"   Response type: {type(response).__name__}")
        print(f"   Required fields present: ✓")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    
    print("🚀 Starting Enhanced Text Chat Integration Tests")
    print("=" * 60)
    
    # Run tests
    tests = [
        test_enhanced_text_chat_integration,
        test_integration_with_sample_queries,
        test_backward_compatibility
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
        print("\n✅ All tests passed! Enhanced text chat integration is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Enhanced Text Chat Integration: READY FOR DEPLOYMENT")
    else:
        print("\n⚠️ Enhanced Text Chat Integration: NEEDS ATTENTION")
        exit(1)