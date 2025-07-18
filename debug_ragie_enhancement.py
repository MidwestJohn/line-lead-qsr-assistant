#!/usr/bin/env python3
"""Debug script to check Ragie enhancement issue"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Check environment first
print("=== Environment Check ===")
from dotenv import load_dotenv
load_dotenv()

ragie_key = os.getenv('RAGIE_API_KEY')
print(f"RAGIE_API_KEY exists: {bool(ragie_key)}")
if ragie_key:
    print(f"RAGIE_API_KEY length: {len(ragie_key)}")
    print(f"RAGIE_API_KEY starts with: {ragie_key[:10]}...")

# Check import
print("\n=== Import Check ===")
try:
    from services.enhanced_ragie_service import enhanced_ragie_service, RAGIE_AVAILABLE
    print(f"enhanced_ragie_service imported: ✅")
    print(f"RAGIE_AVAILABLE: {RAGIE_AVAILABLE}")
    print(f"enhanced_ragie_service.available: {enhanced_ragie_service.available}")
    print(f"enhanced_ragie_service.is_available(): {enhanced_ragie_service.is_available()}")
except Exception as e:
    print(f"enhanced_ragie_service import failed: {e}")

# Check safe enhancement
print("\n=== Safe Enhancement Check ===")
try:
    from services.safe_ragie_enhancement import safe_ragie_enhancement
    print(f"safe_ragie_enhancement imported: ✅")
    print(f"safe_ragie_enhancement.available: {safe_ragie_enhancement.available}")
    print(f"Enhancement stats: {safe_ragie_enhancement.get_enhancement_stats()}")
except Exception as e:
    print(f"safe_ragie_enhancement import failed: {e}")

# Test a simple enhancement
print("\n=== Enhancement Test ===")
try:
    import asyncio
    from services.safe_ragie_enhancement import enhance_query_for_orchestrator
    
    async def test_enhancement():
        result = await enhance_query_for_orchestrator("Show me a Baxter oven diagram")
        print(f"Test result: {result}")
    
    asyncio.run(test_enhancement())
except Exception as e:
    print(f"Enhancement test failed: {e}")