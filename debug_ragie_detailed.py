#!/usr/bin/env python3
"""
Debug script to get detailed information about Ragie search results
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.ragie_service_clean import clean_ragie_service

async def debug_ragie_results():
    """Get detailed information about what documents are being found"""
    
    if not clean_ragie_service.is_available():
        print("❌ Ragie service not available")
        return
    
    print("🔍 Debugging Ragie search results in detail...")
    print(f"Target Baxter document ID: 2ac643c8-8f34-4526-bd74-2b6980ac4b30")
    print("=" * 80)
    
    # Try a broad search
    try:
        print(f"\n🔍 Searching for: 'oven' (broad search)")
        results = await clean_ragie_service.search("oven", limit=15)
        
        if results:
            print(f"✅ Found {len(results)} results")
            
            for i, result in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                print(f"Document ID: {result.document_id}")
                print(f"Score: {result.score:.4f}")
                print(f"Text excerpt: {result.text[:200]}...")
                
                # Check metadata
                metadata = result.metadata if hasattr(result, 'metadata') else {}
                print(f"Metadata keys: {list(metadata.keys())}")
                
                if metadata:
                    for key, value in metadata.items():
                        if key in ['original_filename', 'filename', 'document_name', 'name']:
                            print(f"  {key}: {value}")
                
                # Check if this matches our target
                if result.document_id == "2ac643c8-8f34-4526-bd74-2b6980ac4b30":
                    print(f"🎯 THIS IS THE BAXTER DOCUMENT!")
                    print(f"Full metadata: {metadata}")
                    print(f"Full text: {result.text}")
                
                print("-" * 40)
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_ragie_results())