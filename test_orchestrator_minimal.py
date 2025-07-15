#!/usr/bin/env python3
"""
Minimal test for orchestrator to isolate the hang issue
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

async def test_orchestrator():
    """Test orchestrator directly"""
    print("🧪 Testing QSR Orchestrator directly...")
    
    try:
        from backend.agents.qsr_orchestrator import QSROrchestrator
        
        print("1. Creating orchestrator...")
        orchestrator = QSROrchestrator()
        
        print("2. Initializing orchestrator...")
        await orchestrator.initialize()
        
        print("3. Testing classification...")
        classification = await orchestrator.classify_query("Taylor E01 grill not heating")
        print(f"   Classification: {classification.primary_agent} (confidence: {classification.confidence})")
        
        print("4. Testing handle_query...")
        response = await orchestrator.handle_query(
            query="Taylor E01 grill not heating",
            conversation_id="test_001"
        )
        
        print(f"5. ✅ Success! Response: {response.response[:100]}...")
        print(f"   Agent used: {response.agent_used}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator())