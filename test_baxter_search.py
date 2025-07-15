#!/usr/bin/env python3
"""
Test script to find the Baxter OV520E1 document in Ragie
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.ragie_service_clean import clean_ragie_service

async def test_baxter_searches():
    """Test various search terms to find the Baxter OV520E1 document"""
    
    if not clean_ragie_service.is_available():
        print("❌ Ragie service not available")
        return
    
    search_terms = [
        "Baxter OV520E1",
        "Baxter",
        "OV520E1", 
        "oven",
        "electric diagram",
        "rotating rack oven",
        "Baxter_OV520E1_Rotating_Single_Rack_Oven_Electric_Diagram.png",
        "diagram",
        "electric",
        "rotating"
    ]
    
    print("🔍 Testing Ragie search for Baxter OV520E1 document...")
    print(f"Target document: 2ac643c8-8f34-4526-bd74-2b6980ac4b30")
    print("=" * 60)
    
    for term in search_terms:
        try:
            print(f"\n🔍 Searching for: '{term}'")
            results = await clean_ragie_service.search(term, limit=10)
            
            if results:
                print(f"✅ Found {len(results)} results")
                for i, result in enumerate(results):
                    filename = result.metadata.get("original_filename", "Unknown")
                    doc_id = result.document_id
                    score = result.score
                    print(f"  {i+1}. {filename} (ID: {doc_id[:8]}..., Score: {score:.3f})")
                    
                    # Check if this is our target document
                    if doc_id == "2ac643c8-8f34-4526-bd74-2b6980ac4b30":
                        print(f"  🎯 FOUND TARGET DOCUMENT! Score: {score:.3f}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error searching for '{term}': {e}")
    
    print("\n" + "=" * 60)
    print("Search test complete!")

if __name__ == "__main__":
    asyncio.run(test_baxter_searches())