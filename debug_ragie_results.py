#!/usr/bin/env python3
"""
Debug Ragie Results Processing
==============================

Simple script to debug why Ragie is finding results but 
the safe enhancement service isn't processing them correctly.
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

async def debug_ragie_processing():
    """Debug the full Ragie processing chain"""
    print("🔍 Debugging Ragie Results Processing...")
    
    try:
        # Import the services
        from services.enhanced_ragie_service import enhanced_ragie_service
        from services.safe_ragie_enhancement import safe_ragie_enhancement
        
        test_query = "Fryer temperature calibration steps"
        print(f"\n📝 Testing query: {test_query}")
        
        # Step 1: Test direct Ragie service
        print("\n1️⃣ Testing direct enhanced_ragie_service...")
        print(f"   Available: {enhanced_ragie_service.available}")
        
        if enhanced_ragie_service.available:
            # Detect QSR context
            qsr_context = enhanced_ragie_service._detect_qsr_context(test_query)
            print(f"   QSR Context: {qsr_context}")
            
            # Perform direct search
            direct_results = await enhanced_ragie_service.search_with_qsr_context(
                query=test_query,
                qsr_context=qsr_context,
                top_k=3
            )
            
            print(f"   Direct results count: {len(direct_results)}")
            for i, result in enumerate(direct_results):
                print(f"   Result {i+1}:")
                print(f"     Text: {result.text[:100]}...")
                print(f"     Score: {result.score}")
                print(f"     Document ID: {result.document_id}")
                print(f"     Has images: {bool(result.images)}")
                print(f"     Metadata: {result.metadata}")
        
        # Step 2: Test safe enhancement processing
        print("\n2️⃣ Testing safe_ragie_enhancement processing...")
        safe_result = await safe_ragie_enhancement.enhance_query_safely(test_query)
        
        print(f"   Enhanced: {safe_result.ragie_enhanced}")
        print(f"   Processing time: {safe_result.processing_time:.3f}s")
        print(f"   Visual citations: {len(safe_result.visual_citations)}")
        print(f"   Error: {safe_result.error}")
        print(f"   Enhanced query length: {len(safe_result.enhanced_query)}")
        print(f"   Original query length: {len(test_query)}")
        
        if safe_result.enhanced_query != test_query:
            print(f"   ✅ Query was actually enhanced!")
            print(f"   Enhanced query: {safe_result.enhanced_query}")
        else:
            print(f"   ❌ Query was NOT enhanced (same as original)")
        
        # Step 3: Test the _perform_ragie_search method directly
        print("\n3️⃣ Testing _perform_ragie_search method...")
        try:
            ragie_data = await safe_ragie_enhancement._perform_ragie_search(test_query)
            print(f"   Ragie data keys: {ragie_data.keys()}")
            results = ragie_data.get("results", [])
            print(f"   Results count from _perform_ragie_search: {len(results) if results else 0}")
            
            if results:
                print(f"   First result type: {type(results[0])}")
                print(f"   First result has text: {hasattr(results[0], 'text')}")
                print(f"   First result has images: {hasattr(results[0], 'images')}")
        except Exception as e:
            print(f"   ❌ _perform_ragie_search failed: {e}")
        
        # Step 4: Test different queries
        print("\n4️⃣ Testing different queries...")
        test_queries = [
            "safety procedures",
            "equipment maintenance", 
            "how to clean fryer"
        ]
        
        for query in test_queries:
            try:
                result = await safe_ragie_enhancement.enhance_query_safely(query)
                print(f"   '{query}' -> Enhanced: {result.ragie_enhanced}, Citations: {len(result.visual_citations)}")
            except Exception as e:
                print(f"   '{query}' -> Error: {e}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_ragie_processing())