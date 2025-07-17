#!/usr/bin/env python3
"""
Test Enhanced Ragie Filtering
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.ragie_service_clean import clean_ragie_service

async def test_enhanced_filtering():
    """Test our enhanced filtering capabilities"""
    
    print("🎯 Testing Enhanced Ragie Filtering")
    print("=" * 40)
    
    if not clean_ragie_service.is_available():
        print("❌ Ragie service not available")
        return
    
    test_queries = [
        "Show me an image of the Baxter OV520E1",
        "Baxter OV520E1", 
        "diagram",
        "oven maintenance manual"
    ]
    
    for query in test_queries:
        try:
            print(f"\n🔍 Testing: '{query}'")
            
            # Test the filter generation
            smart_filter = clean_ragie_service._build_smart_filter(query, query)
            if smart_filter:
                print(f"🎯 Generated filter: {smart_filter}")
            else:
                print("📝 No specific filter generated")
            
            # Test the search (but handle rate limits)
            try:
                results = await clean_ragie_service.search(query, limit=3)
                print(f"✅ Found {len(results)} results")
                
                if results:
                    for i, result in enumerate(results):
                        print(f"  {i+1}. Score: {result.score:.3f}")
                        print(f"     Source: {result.metadata.get('original_filename', 'Unknown')}")
                        print(f"     Doc ID: {result.document_id[:8]}...")
                        
            except Exception as search_error:
                if "rate limit" in str(search_error).lower():
                    print("⚠️ Rate limited - but filter generation worked!")
                else:
                    print(f"❌ Search error: {search_error}")
            
        except Exception as e:
            print(f"❌ Error testing '{query}': {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_filtering())