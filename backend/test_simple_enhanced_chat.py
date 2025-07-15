#!/usr/bin/env python3
"""
Simple test to isolate the 'list index out of range' error
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_simple_query():
    """Test a simple query to isolate the error"""
    
    print("Testing simple enhanced chat query...")
    
    try:
        from enhanced_text_chat_endpoint import ChatMessage, backward_compatible_chat_endpoint
        
        # Test with a problematic query
        message = ChatMessage(message="The ice machine is not working")
        
        print(f"Processing query: {message.message}")
        
        response = await backward_compatible_chat_endpoint(message)
        
        print(f"Response: {response.response}")
        print(f"Retrieval method: {response.retrieval_method}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        
        # Also check if we can get more detail from the service
        try:
            from enhanced_text_chat_endpoint import enhanced_text_chat_service
            print(f"Service initialized: {enhanced_text_chat_service.initialized}")
            
            # Check if we can get the error from the service metrics
            metrics = enhanced_text_chat_service.get_metrics()
            print(f"Service metrics: {metrics}")
            
        except Exception as service_error:
            print(f"Service error: {service_error}")

if __name__ == "__main__":
    asyncio.run(test_simple_query())