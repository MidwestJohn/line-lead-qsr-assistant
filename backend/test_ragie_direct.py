#!/usr/bin/env python3
"""
Test Ragie service directly to see what's happening
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_ragie_direct():
    """Test the Ragie service directly"""
    
    print("Testing Ragie service directly...")
    
    try:
        from services.ragie_service_clean import clean_ragie_service
        
        # Check if Ragie is available
        print(f"Ragie available: {clean_ragie_service.is_available()}")
        
        if not clean_ragie_service.is_available():
            print("Ragie service is not available")
            return
        
        # Test the problematic query
        query = "The ice machine is not working"
        
        print(f"Testing query: {query}")
        
        # Test with search_documents method
        result = await clean_ragie_service.search_documents(query)
        
        print(f"Search result type: {type(result)}")
        print(f"Search result: {result}")
        
        # Test the content
        content = result.get('content', '')
        print(f"Content length: {len(content)}")
        print(f"Content preview: {content[:200]}...")
        
        # Test sources
        sources = result.get('sources', [])
        print(f"Number of sources: {len(sources)}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ragie_direct())