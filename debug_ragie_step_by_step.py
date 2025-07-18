#!/usr/bin/env python3
"""Detailed debug script for Ragie enhancement issue"""

import sys
import os
import asyncio
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

from dotenv import load_dotenv
load_dotenv()

async def debug_ragie_step_by_step():
    """Debug each step of the Ragie enhancement"""
    
    print("=== Step 1: Import Services ===")
    from services.enhanced_ragie_service import enhanced_ragie_service
    from services.ragie_verification_service import ragie_verification
    
    print(f"enhanced_ragie_service available: {enhanced_ragie_service.is_available()}")
    
    print("\n=== Step 2: Test QSR Context Detection ===")
    query = "Show me a Baxter oven diagram"
    qsr_context = enhanced_ragie_service._detect_qsr_context(query)
    print(f"QSR context detected: {qsr_context}")
    
    print("\n=== Step 3: Test Direct Search ===")
    try:
        direct_results = await enhanced_ragie_service.search_with_qsr_context(
            query, qsr_context=qsr_context, top_k=2
        )
        print(f"Direct search results: {len(direct_results) if direct_results else 0} found")
        if direct_results:
            for i, result in enumerate(direct_results):
                print(f"  Result {i+1}: score={result.score:.3f}, doc_id={result.document_id}")
    except Exception as e:
        print(f"Direct search failed: {e}")
    
    print("\n=== Step 4: Test Verification Service ===")
    try:
        results, metrics = await ragie_verification.verify_ragie_call(
            query,
            enhanced_ragie_service.search_with_qsr_context,
            query,
            qsr_context=qsr_context,
            top_k=2
        )
        print(f"Verification results: {len(results) if results else 0} found")
        print(f"Verification metrics: success={metrics.success}, duration={metrics.duration:.3f}s")
    except Exception as e:
        print(f"Verification failed: {e}")
    
    print("\n=== Step 5: Test Safe Enhancement ===")
    try:
        from services.safe_ragie_enhancement import safe_ragie_enhancement
        result = await safe_ragie_enhancement.enhance_query_safely(query)
        print(f"Safe enhancement result:")
        print(f"  ragie_enhanced: {result.ragie_enhanced}")
        print(f"  visual_citations: {len(result.visual_citations)}")
        print(f"  processing_time: {result.processing_time:.3f}s")
        print(f"  error: {result.error}")
    except Exception as e:
        print(f"Safe enhancement failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_ragie_step_by_step())