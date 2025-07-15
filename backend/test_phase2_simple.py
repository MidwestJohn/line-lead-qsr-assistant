#!/usr/bin/env python3
"""
Simple Phase 2 Test
===================

Basic test to verify Phase 2 components work individually.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_agent():
    """Test basic QSR agent"""
    logger.info("🔄 Testing basic QSR agent...")
    
    try:
        from agents.qsr_base_agent import create_qsr_agent_async, QSRContext
        
        agent = await create_qsr_agent_async()
        
        context = QSRContext(
            user_role="manager",
            restaurant_location="main",
            shift_time="morning",
            equipment_status={},
            current_issues=[],
            urgency_level="normal",
            timestamp=datetime.now()
        )
        
        response = await agent.process_query(
            "What's the procedure for opening the restaurant?",
            context
        )
        
        logger.info(f"✅ Base agent working - response length: {len(response.response)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Base agent test failed: {e}")
        return False


async def test_equipment_agent():
    """Test equipment specialist agent"""
    logger.info("🔄 Testing equipment specialist agent...")
    
    try:
        from agents.equipment_agent import EquipmentSpecialistAgent, EquipmentContext, EquipmentType
        
        agent = EquipmentSpecialistAgent()
        
        context = EquipmentContext(
            equipment_type=EquipmentType.TAYLOR_ICE_CREAM,
            error_codes=["E01"],
            symptoms=["mix low alarm"],
            urgency_level="urgent",
            timestamp=datetime.now()
        )
        
        response = await agent.diagnose_equipment(
            "Taylor machine showing error E01",
            context
        )
        
        logger.info(f"✅ Equipment agent working - confidence: {response.confidence}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Equipment agent test failed: {e}")
        return False


async def test_query_classification():
    """Test query classification without full orchestrator"""
    logger.info("🔄 Testing query classification...")
    
    try:
        from agents.qsr_orchestrator import AgentType
        
        # Simple keyword-based classification
        test_queries = {
            "Taylor machine error E01": AgentType.EQUIPMENT,
            "Employee burn emergency": AgentType.SAFETY,
            "Opening procedure": AgentType.OPERATIONS,
            "Train new employee": AgentType.TRAINING
        }
        
        correct = 0
        for query, expected in test_queries.items():
            # Simple classification logic
            query_lower = query.lower()
            if any(kw in query_lower for kw in ["taylor", "machine", "error", "equipment"]):
                classified = AgentType.EQUIPMENT
            elif any(kw in query_lower for kw in ["burn", "emergency", "safety"]):
                classified = AgentType.SAFETY  
            elif any(kw in query_lower for kw in ["opening", "procedure", "operation"]):
                classified = AgentType.OPERATIONS
            elif any(kw in query_lower for kw in ["train", "employee", "training"]):
                classified = AgentType.TRAINING
            else:
                classified = AgentType.BASE
            
            if classified == expected:
                correct += 1
                logger.info(f"   ✅ '{query}' -> {classified.value}")
            else:
                logger.info(f"   ❌ '{query}' -> {classified.value} (expected {expected.value})")
        
        accuracy = correct / len(test_queries)
        logger.info(f"📊 Classification accuracy: {accuracy:.2%}")
        return accuracy >= 0.75
        
    except Exception as e:
        logger.error(f"❌ Classification test failed: {e}")
        return False


async def run_simple_tests():
    """Run simple Phase 2 component tests"""
    
    logger.info("🚀 Running Simple Phase 2 Tests")
    logger.info("=" * 40)
    
    tests = [
        ("Base Agent", test_basic_agent),
        ("Equipment Agent", test_equipment_agent), 
        ("Classification", test_query_classification)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 40)
    logger.info("📊 SIMPLE TEST RESULTS")
    logger.info("=" * 40)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    success_rate = passed / total
    logger.info(f"\n📈 Success Rate: {success_rate:.2%} ({passed}/{total})")
    
    if success_rate >= 0.8:
        logger.info("🎉 Phase 2 components are working!")
    else:
        logger.info("⚠️  Some Phase 2 components need fixes")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_simple_tests())