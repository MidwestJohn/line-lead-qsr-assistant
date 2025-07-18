#!/usr/bin/env python3
"""Test Baxter oven search specifically"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv()

async def test_baxter_search():
    """Test different Baxter search queries"""
    
    from services.enhanced_ragie_service import enhanced_ragie_service
    
    test_queries = [
        "Show me a Baxter oven diagram",
        "Baxter oven",
        "Baxter OV520E1",
        "rotating rack oven",
        "Baxter rotating oven",
        "oven diagram",
        "Baxter"
    ]
    
    for query in test_queries:
        print(f"\n=== Testing: '{query}' ===")
        try:
            # Test with QSR context
            qsr_context = enhanced_ragie_service._detect_qsr_context(query)
            print(f"QSR context: {qsr_context}")
            
            results = await enhanced_ragie_service.search_with_qsr_context(
                query, qsr_context=qsr_context, top_k=3
            )
            
            print(f"Results: {len(results)} found")
            for i, result in enumerate(results):
                print(f"  {i+1}. Score: {result.score:.3f}")
                print(f"     Doc ID: {result.document_id}")
                print(f"     Text: {result.text[:100]}...")
                print(f"     Images: {len(result.images) if result.images else 0}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_baxter_search())