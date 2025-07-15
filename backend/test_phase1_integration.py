#!/usr/bin/env python3
"""
Phase 1 Integration Testing
===========================

Comprehensive testing of Phase 1 PydanticAI implementation.
Tests all components without requiring actual API calls.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append('.')

async def test_phase1_integration():
    """Test Phase 1 implementation components"""
    
    print("🧪 Phase 1 Integration Testing")
    print("=" * 60)
    
    # Set up test environment
    os.environ['OPENAI_API_KEY'] = 'test-key-for-structure-testing'
    
    # Test results tracking
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Component Structure
    print("\n1. Testing Component Structure...")
    tests_total += 1
    
    try:
        from agents.qsr_base_agent import QSRBaseAgent, QSRContext, QSRResponse
        from database.qsr_database import QSRDatabase
        from endpoints.pydantic_chat_endpoints import PydanticChatRequest, PydanticChatResponse
        
        print("   ✅ All components imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Component import failed: {e}")
    
    # Test 2: Model Validation
    print("\n2. Testing Model Validation...")
    tests_total += 1
    
    try:
        # Test QSRContext
        context = QSRContext(
            conversation_id="test_conversation",
            user_location="Test Location",
            equipment_context={"Taylor Machine": "Model C712"}
        )
        
        # Test PydanticChatRequest
        request = PydanticChatRequest(
            message="How do I clean the Taylor ice cream machine?",
            conversation_id="test_conversation"
        )
        
        # Test QSRResponse
        response = QSRResponse(
            response="Test response",
            response_type="equipment",
            confidence=0.85,
            safety_alerts=["Test alert"],
            equipment_references=["Taylor"],
            citations=["Manual: Page 42"]
        )
        
        print("   ✅ All models validate correctly")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Model validation failed: {e}")
    
    # Test 3: Database Operations
    print("\n3. Testing Database Operations...")
    tests_total += 1
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp:
            tmp_db_path = Path(tmp.name)
        
        async with QSRDatabase.connect(tmp_db_path) as db:
            conversation_id = "test_phase1_conversation"
            
            # Test proper PydanticAI message format
            test_messages = json.dumps([
                {
                    "kind": "request",
                    "parts": [
                        {
                            "kind": "user-prompt",
                            "content": "Test message",
                            "timestamp": datetime.now().isoformat()
                        }
                    ]
                }
            ]).encode()
            
            # Add messages
            success = await db.add_messages(conversation_id, test_messages, 'test_agent', 1.5)
            
            if success:
                # Test analytics
                await db.add_equipment_reference(conversation_id, 'Taylor Machine', 'Page 42')
                await db.add_safety_incident(conversation_id, 'test_incident', 'low')
                await db.add_analytics_metric(conversation_id, 'response_time', 1.5)
                
                # Get analytics
                analytics = await db.get_conversation_analytics(conversation_id)
                
                if analytics and analytics.get('conversation_id') == conversation_id:
                    print("   ✅ Database operations successful")
                    tests_passed += 1
                else:
                    print("   ❌ Analytics retrieval failed")
            else:
                print("   ❌ Message storage failed")
        
        # Clean up
        tmp_db_path.unlink(missing_ok=True)
        
    except Exception as e:
        print(f"   ❌ Database operations failed: {e}")
    
    # Test 4: Endpoint Structure
    print("\n4. Testing Endpoint Structure...")
    tests_total += 1
    
    try:
        from endpoints.pydantic_chat_endpoints import QSRChatEndpoints
        from fastapi import FastAPI
        
        # Create test app
        app = FastAPI()
        endpoints = QSRChatEndpoints(app)
        
        # Check if endpoints are properly registered
        routes = [route.path for route in app.routes]
        expected_routes = [
            '/chat/pydantic',
            '/chat/pydantic/stream',
            '/chat/pydantic/history/{conversation_id}',
            '/chat/pydantic/analytics/{conversation_id}',
            '/chat/pydantic/health'
        ]
        
        all_routes_present = all(route in routes for route in expected_routes)
        
        if all_routes_present:
            print("   ✅ All endpoints registered correctly")
            tests_passed += 1
        else:
            missing_routes = [route for route in expected_routes if route not in routes]
            print(f"   ❌ Missing endpoints: {missing_routes}")
    
    except Exception as e:
        print(f"   ❌ Endpoint structure test failed: {e}")
    
    # Test 5: Response Processing
    print("\n5. Testing Response Processing...")
    tests_total += 1
    
    try:
        # Test response processing without API calls
        from agents.qsr_base_agent import QSRBaseAgent
        
        # Create agent instance (structure only)
        agent = QSRBaseAgent.__new__(QSRBaseAgent)
        
        # Test response processing methods
        test_response = "This is a test response about Taylor ice cream machine maintenance procedures."
        
        # Test classification
        response_type = agent._classify_response_type(test_response, "taylor machine")
        
        # Test safety alerts
        safety_alerts = agent._extract_safety_alerts(test_response)
        
        # Test equipment references
        equipment_refs = agent._extract_equipment_references(test_response)
        
        if response_type == "equipment" and "Taylor" in equipment_refs:
            print("   ✅ Response processing working correctly")
            tests_passed += 1
        else:
            print(f"   ❌ Response processing failed: type={response_type}, refs={equipment_refs}")
    
    except Exception as e:
        print(f"   ❌ Response processing test failed: {e}")
    
    # Test 6: Error Handling
    print("\n6. Testing Error Handling...")
    tests_total += 1
    
    try:
        from agents.qsr_base_agent import QSRBaseAgent
        
        # Test error handling structure
        agent = QSRBaseAgent.__new__(QSRBaseAgent)
        
        # Test confidence calculation
        confidence = agent._calculate_confidence("Test response with citations [Manual: Page 1]", "equipment")
        
        # Test escalation detection
        escalation_required = agent._requires_escalation("Emergency call 911 immediately", ["Emergency alert"])
        
        if 0.0 <= confidence <= 1.0 and escalation_required:
            print("   ✅ Error handling and logic working correctly")
            tests_passed += 1
        else:
            print(f"   ❌ Error handling failed: confidence={confidence}, escalation={escalation_required}")
    
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
    
    # Final Results
    print("\n" + "=" * 60)
    print("📊 Phase 1 Integration Test Results")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {tests_passed/tests_total*100:.1f}%")
    
    if tests_passed == tests_total:
        print("✅ All tests passed - Phase 1 implementation validated")
        return True
    else:
        print("❌ Some tests failed - Phase 1 needs attention")
        return False

async def main():
    """Main test execution"""
    success = await test_phase1_integration()
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)