#!/usr/bin/env python3
"""
Phase 2 Orchestration Testing
============================

Test script to validate the Phase 2 multi-agent orchestration implementation.
Tests agent classification, routing, and enhanced Ragie integration.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_orchestrator_setup():
    """Test orchestrator initialization"""
    try:
        from agents.qsr_orchestrator import QSROrchestrator, AgentType
        
        logger.info("🔄 Testing orchestrator initialization...")
        orchestrator = await QSROrchestrator.create()
        
        health_status = await orchestrator.get_health_status()
        logger.info(f"✅ Orchestrator initialized successfully")
        logger.info(f"   Status: {health_status['orchestrator']['status']}")
        logger.info(f"   Agents available: {list(health_status['agents'].keys())}")
        
        return orchestrator
        
    except Exception as e:
        logger.error(f"❌ Orchestrator initialization failed: {e}")
        return None


async def test_query_classification(orchestrator):
    """Test query classification accuracy"""
    
    if not orchestrator:
        logger.error("❌ Skipping classification test - orchestrator not available")
        return
    
    logger.info("🔄 Testing query classification...")
    
    test_queries = [
        ("Taylor machine showing error E01", AgentType.EQUIPMENT),
        ("Employee was burned by hot oil", AgentType.SAFETY),
        ("What's the opening procedure?", AgentType.OPERATIONS),
        ("How do I train a new employee?", AgentType.TRAINING),
        ("General QSR question about restaurant management", AgentType.BASE)
    ]
    
    correct_classifications = 0
    
    for query, expected_agent in test_queries:
        try:
            classification = await orchestrator.classify_query(query)
            classified_agent = classification.primary_agent
            
            status = "✅" if classified_agent == expected_agent else "❌"
            logger.info(f"   {status} '{query}' -> {classified_agent.value} (expected: {expected_agent.value})")
            logger.info(f"      Confidence: {classification.confidence:.2f}, Keywords: {classification.keywords}")
            
            if classified_agent == expected_agent:
                correct_classifications += 1
                
        except Exception as e:
            logger.error(f"❌ Classification failed for '{query}': {e}")
    
    accuracy = correct_classifications / len(test_queries)
    logger.info(f"📊 Classification accuracy: {accuracy:.2%} ({correct_classifications}/{len(test_queries)})")
    
    return accuracy >= 0.8  # 80% accuracy threshold


async def test_agent_responses(orchestrator):
    """Test responses from different specialist agents"""
    
    if not orchestrator:
        logger.error("❌ Skipping agent response test - orchestrator not available")
        return
    
    logger.info("🔄 Testing agent responses...")
    
    test_scenarios = [
        {
            "query": "Taylor ice cream machine error E01 troubleshooting",
            "expected_agent": AgentType.EQUIPMENT,
            "context": {
                "equipment_type": "taylor_ice_cream",
                "error_codes": ["E01"],
                "symptoms": ["mix low alarm"]
            }
        },
        {
            "query": "Employee safety incident reporting procedure", 
            "expected_agent": AgentType.SAFETY,
            "context": {
                "incident_type": "burn",
                "urgency": "high"
            }
        },
        {
            "query": "Morning opening checklist procedures",
            "expected_agent": AgentType.OPERATIONS, 
            "context": {
                "shift": "opening",
                "time": "06:00"
            }
        }
    ]
    
    successful_responses = 0
    
    for scenario in test_scenarios:
        try:
            logger.info(f"   Testing: {scenario['query'][:50]}...")
            
            response = await orchestrator.handle_query(
                query=scenario["query"],
                context=scenario["context"]
            )
            
            # Check if correct agent was used
            agent_correct = response.agent_used == scenario["expected_agent"]
            response_valid = len(response.response) > 50  # Basic length check
            
            status = "✅" if agent_correct and response_valid else "❌"
            logger.info(f"   {status} Agent: {response.agent_used.value}, Response length: {len(response.response)}")
            
            if agent_correct and response_valid:
                successful_responses += 1
                
        except Exception as e:
            logger.error(f"❌ Response test failed: {e}")
    
    success_rate = successful_responses / len(test_scenarios)
    logger.info(f"📊 Agent response success rate: {success_rate:.2%} ({successful_responses}/{len(test_scenarios)})")
    
    return success_rate >= 0.8


async def test_enhanced_ragie_service():
    """Test enhanced Ragie service integration"""
    
    logger.info("🔄 Testing enhanced Ragie service...")
    
    try:
        from services.enhanced_ragie_service import EnhancedRagieService, AgentType
        
        # Test service initialization  
        ragie_service = await EnhancedRagieService.create()
        health_status = await ragie_service.get_health_status()
        
        logger.info(f"   Ragie service status: {health_status['status']}")
        logger.info(f"   Query count: {health_status['query_count']}")
        
        # Test agent-specific search
        test_queries = [
            ("Taylor machine maintenance", AgentType.EQUIPMENT),
            ("Safety emergency procedures", AgentType.SAFETY),
            ("Opening procedures", AgentType.OPERATIONS)
        ]
        
        successful_searches = 0
        
        for query, agent_type in test_queries:
            try:
                results = await ragie_service.search_for_agent(query, agent_type)
                logger.info(f"   ✅ {agent_type.value} search: {results.total_results} results in {results.processing_time:.2f}s")
                successful_searches += 1
            except Exception as e:
                logger.info(f"   ❌ {agent_type.value} search failed: {e}")
        
        success_rate = successful_searches / len(test_queries)
        logger.info(f"📊 Ragie search success rate: {success_rate:.2%}")
        
        return success_rate >= 0.8
        
    except Exception as e:
        logger.error(f"❌ Enhanced Ragie service test failed: {e}")
        return False


async def test_streaming_responses(orchestrator):
    """Test streaming responses through orchestrator"""
    
    if not orchestrator:
        logger.error("❌ Skipping streaming test - orchestrator not available")
        return
    
    logger.info("🔄 Testing streaming responses...")
    
    try:
        query = "Taylor ice cream machine diagnostic procedure"
        chunk_count = 0
        total_content = ""
        
        async for chunk in orchestrator.handle_query_stream(query):
            chunk_count += 1
            if chunk.get("chunk"):
                total_content += chunk["chunk"]
            
            if chunk.get("done"):
                metadata = chunk.get("metadata", {})
                logger.info(f"   ✅ Streaming completed: {chunk_count} chunks, {len(total_content)} chars")
                logger.info(f"   Agent used: {metadata.get('agent_used', 'unknown')}")
                break
        
        return chunk_count > 0 and len(total_content) > 100
        
    except Exception as e:
        logger.error(f"❌ Streaming test failed: {e}")
        return False


async def test_endpoints():
    """Test FastAPI endpoints if server is running"""
    
    logger.info("🔄 Testing API endpoints...")
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get(f"{base_url}/chat/orchestrated/health")
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"   ✅ Health endpoint: {health_data['status']}")
                
                # Test classification endpoint
                response = await client.post(
                    f"{base_url}/chat/orchestrated/classify",
                    params={"message": "Taylor machine error E01"}
                )
                
                if response.status_code == 200:
                    classification_data = response.json()
                    logger.info(f"   ✅ Classification endpoint: {classification_data['classification']['primary_agent']}")
                    return True
                else:
                    logger.info(f"   ❌ Classification endpoint failed: {response.status_code}")
            else:
                logger.info(f"   ❌ Health endpoint failed: {response.status_code}")
                
    except httpx.ConnectError:
        logger.info("   ⚠️  Server not running - skipping endpoint tests")
    except Exception as e:
        logger.error(f"   ❌ Endpoint test failed: {e}")
    
    return False


async def run_phase2_validation():
    """Run complete Phase 2 validation suite"""
    
    logger.info("🚀 Starting Phase 2 Orchestration Validation")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test 1: Orchestrator Setup
    orchestrator = await test_orchestrator_setup()
    test_results["orchestrator_setup"] = orchestrator is not None
    
    # Test 2: Query Classification
    test_results["classification_accuracy"] = await test_query_classification(orchestrator)
    
    # Test 3: Agent Responses
    test_results["agent_responses"] = await test_agent_responses(orchestrator)
    
    # Test 4: Enhanced Ragie Service
    test_results["ragie_service"] = await test_enhanced_ragie_service()
    
    # Test 5: Streaming Responses
    test_results["streaming"] = await test_streaming_responses(orchestrator)
    
    # Test 6: API Endpoints
    test_results["endpoints"] = await test_endpoints()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 PHASE 2 VALIDATION RESULTS")
    logger.info("=" * 60)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name.replace('_', ' ').title()}")
    
    success_rate = passed_tests / total_tests
    logger.info(f"\n📈 Overall Success Rate: {success_rate:.2%} ({passed_tests}/{total_tests})")
    
    if success_rate >= 0.8:
        logger.info("🎉 Phase 2 implementation is READY for deployment!")
    elif success_rate >= 0.6:
        logger.info("⚠️  Phase 2 implementation needs minor fixes")
    else:
        logger.info("❌ Phase 2 implementation needs significant work")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(run_phase2_validation())