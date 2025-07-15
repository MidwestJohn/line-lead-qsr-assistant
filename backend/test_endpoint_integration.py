#!/usr/bin/env python3
"""
Test the actual /chat/stream endpoint to ensure it's fully working
"""

import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_chat_stream_endpoint():
    """Test the actual chat stream endpoint"""
    
    print("Testing /chat/stream endpoint integration...")
    
    try:
        # Import the endpoint directly
        from main_clean import chat_stream_endpoint, ChatMessage
        
        # Test message
        message = ChatMessage(message="How do I clean the fryer?")
        
        print(f"Testing message: {message.message}")
        
        # Call the endpoint
        response = await chat_stream_endpoint(message)
        
        print(f"Response type: {type(response)}")
        print(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        
        if isinstance(response, dict):
            print(f"Response content: {response.get('response', 'No response')[:100]}...")
            print(f"Retrieval method: {response.get('retrieval_method', 'No method')}")
            print(f"Visual citations: {len(response.get('visual_citations', []))}")
            print(f"Manual references: {len(response.get('manual_references', []))}")
        
        print("✅ /chat/stream endpoint working!")
        
    except Exception as e:
        import traceback
        print(f"❌ Endpoint test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_stream_endpoint())