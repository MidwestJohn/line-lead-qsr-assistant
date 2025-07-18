#!/usr/bin/env python3
"""Test the chat endpoint with Baxter oven query"""

import asyncio
import aiohttp
import json

async def test_chat_endpoint():
    """Test the chat endpoint with visual citations"""
    
    url = "http://localhost:8000/chat/stream"
    
    payload = {
        "message": "Show me a Baxter oven diagram",
        "conversation_id": "test_chat_123",
        "session_id": "test_session_456"
    }
    
    print("Testing chat endpoint with:", payload["message"])
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                print(f"Error: {response.status}")
                print(await response.text())
                return
            
            # Read the streaming response
            chunk_count = 0
            async for line in response.content:
                if line:
                    chunk_count += 1
                    try:
                        # Parse the SSE format
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            if data_str == '[DONE]':
                                print(f"\n✅ Stream completed after {chunk_count} chunks")
                                break
                            
                            data = json.loads(data_str)
                            print(f"Chunk {chunk_count}: {data}")
                            
                            # Look for visual citations in the first chunk
                            if chunk_count == 1 and 'visual_citations' in data:
                                print(f"🎯 Visual citations found: {len(data['visual_citations'])}")
                                for i, citation in enumerate(data['visual_citations']):
                                    print(f"  Citation {i+1}: {citation}")
                                    
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}, line: {line_str}")
                    except Exception as e:
                        print(f"Error processing chunk: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_endpoint())