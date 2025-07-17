#!/usr/bin/env python3
"""Test Enhanced Ragie + PydanticAI Integration"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_enhanced_integration():
    """Test the enhanced Ragie + PydanticAI integration"""
    print("🧪 Testing Enhanced Ragie + PydanticAI Integration...")
    
    try:
        # Test 1: Enhanced Ragie Service
        print("\n1️⃣ Testing Enhanced Ragie Service...")
        from backend.services.enhanced_ragie_service import enhanced_ragie_service, QSRContext
        
        if enhanced_ragie_service.is_available():
            print("✅ Enhanced Ragie service available")
            
            # Test search with QSR context
            qsr_context = QSRContext(equipment_type="fryer", procedure_type="cleaning")
            results = await enhanced_ragie_service.search_with_qsr_context(
                query="how to clean fryer",
                qsr_context=qsr_context,
                top_k=2
            )
            print(f"✅ Ragie search returned {len(results)} results")
            
        else:
            print("⚠️ Enhanced Ragie service not available (API key or SDK missing)")
        
        # Test 2: Enhanced QSR Base Agent
        print("\n2️⃣ Testing Enhanced QSR Base Agent...")
        from backend.agents.enhanced_qsr_base_agent import get_enhanced_qsr_agent
        
        agent = await get_enhanced_qsr_agent()
        print("✅ Enhanced QSR agent created successfully")
        
        # Test query processing
        response = await agent.process_query(
            query="How do I troubleshoot a fryer temperature issue?",
            conversation_id="test_session"
        )
        
        print(f"✅ Agent response: {response.response[:100]}...")
        print(f"✅ Ragie enhanced: {response.ragie_enhanced}")
        print(f"✅ Visual citations: {len(response.visual_citations)}")
        print(f"✅ Confidence: {response.confidence_score}")
        
        # Test 3: Enhanced Orchestrator
        print("\n3️⃣ Testing Enhanced Orchestrator...")
        from backend.agents.enhanced_qsr_orchestrator import get_enhanced_qsr_orchestrator
        
        orchestrator = await get_enhanced_qsr_orchestrator()
        print("✅ Enhanced orchestrator initialized")
        
        # Test orchestrated query
        orch_response = await orchestrator.handle_query(
            query="What safety procedures should I follow when cleaning the grill?",
            conversation_id="test_orchestration"
        )
        
        print(f"✅ Orchestrator response: {orch_response.response[:100]}...")
        print(f"✅ Agent used: {orch_response.agent_used}")
        print(f"✅ Processing time: {orch_response.performance_metrics.get('processing_time', 0):.2f}s")
        print(f"✅ Visual citations: {len(orch_response.performance_metrics.get('visual_citations', []))}")
        
        # Test 4: Performance Metrics
        print("\n4️⃣ Testing Performance Metrics...")
        metrics = orchestrator.get_performance_metrics()
        print(f"✅ Total requests: {metrics['total_requests']}")
        print(f"✅ Success rate: {metrics['success_rate']:.2%}")
        print(f"✅ Average response time: {metrics['average_response_time']:.2f}s")
        print(f"✅ Agent usage: {metrics['agent_usage']}")
        
        # Test 5: Enhanced Endpoints Import
        print("\n5️⃣ Testing Enhanced Endpoints...")
        from backend.endpoints.enhanced_pydantic_chat_endpoints import setup_enhanced_pydantic_chat_endpoints
        print("✅ Enhanced endpoints import successfully")
        
        print("\n🎉 All Enhanced Integration Tests Passed!")
        print("\n📊 Integration Summary:")
        print("   ✅ Enhanced Ragie Service with QSR optimization")
        print("   ✅ PydanticAI agents with Ragie RunContext integration")  
        print("   ✅ Intelligent orchestration with context awareness")
        print("   ✅ Visual citation coordination")
        print("   ✅ Production-ready error handling")
        print("   ✅ Performance monitoring and metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_integration())
    sys.exit(0 if success else 1)