"""
Debug script to test message history persistence
"""
import asyncio
import aiohttp
import json
import time

async def test_message_history():
    """Test that message history is working correctly"""
    
    # Test conversation with same session_id
    session_id = "test_session_123"
    
    # Message 1: Ask about Baxter oven
    message1 = {
        "message": "How do I clean the Baxter oven?",
        "conversation_id": session_id
    }
    
    # Message 2: Follow up asking for diagram (should have context)
    message2 = {
        "message": "Show me a diagram",
        "conversation_id": session_id
    }
    
    print("🧪 Testing message history persistence...")
    print(f"📋 Session ID: {session_id}")
    
    async with aiohttp.ClientSession() as session:
        # Send first message
        print("\n1️⃣ Sending first message: 'How do I clean the Baxter oven?'")
        async with session.post(
            "http://localhost:8000/chat/stream",
            json=message1,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                print("✅ First message sent successfully")
                # Read a few chunks to see response
                async for line in response.content:
                    if line.strip():
                        try:
                            data = json.loads(line.decode().replace("data: ", ""))
                            if data.get("done", False):
                                break
                            print(f"📝 Response chunk: {data.get('chunk', '')[:50]}...")
                        except:
                            pass
                        if len(line) > 100:  # Don't read too much
                            break
            else:
                print(f"❌ First message failed: {response.status}")
                return
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Send second message
        print("\n2️⃣ Sending second message: 'Show me a diagram'")
        async with session.post(
            "http://localhost:8000/chat/stream",
            json=message2,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                print("✅ Second message sent successfully")
                response_text = ""
                async for line in response.content:
                    if line.strip():
                        try:
                            data = json.loads(line.decode().replace("data: ", ""))
                            if data.get("done", False):
                                break
                            chunk = data.get('chunk', '')
                            response_text += chunk
                            print(f"📝 Response chunk: {chunk[:50]}...")
                        except:
                            pass
                        if len(response_text) > 500:  # Don't read too much
                            break
                
                print(f"\n🔍 Full response preview: {response_text[:200]}...")
                
                # Check if response mentions Baxter (shows context awareness)
                if "baxter" in response_text.lower() or "oven" in response_text.lower():
                    print("🎯 SUCCESS: Response shows context awareness!")
                    print("🧠 Message history is working correctly")
                else:
                    print("❌ FAILURE: Response doesn't show context awareness")
                    print("💔 Message history may not be persisting")
                    
            else:
                print(f"❌ Second message failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_message_history())