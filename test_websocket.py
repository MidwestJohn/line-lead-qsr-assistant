import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/progress/auto_proc_d9cbb83c-0ede-4fa7-a8a8-d2b680eca9fd_1751939836"
    print(f"🔌 Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send ping
            await websocket.send("ping")
            print("📤 Sent ping")
            
            # Wait for responses
            try:
                for i in range(5):  # Wait for up to 5 messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    print(f"📥 Received: {message}")
            except asyncio.TimeoutError:
                print("⏰ No more messages received (timeout)")
            
            print("🔌 Closing connection")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
