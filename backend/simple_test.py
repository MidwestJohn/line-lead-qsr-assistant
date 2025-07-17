"""
Simple test using curl to test message history
"""
import subprocess
import json
import time

def test_message_history():
    """Test message history with curl"""
    
    session_id = "test_session_123"
    
    # Test 1: Ask about Baxter oven
    print("1️⃣ Testing first message: 'How do I clean the Baxter oven?'")
    
    message1 = {
        "message": "How do I clean the Baxter oven?",
        "conversation_id": session_id
    }
    
    # Use curl to send first message
    curl_cmd1 = [
        "curl", "-X", "POST", 
        "http://localhost:8000/chat/stream",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(message1),
        "--no-buffer"
    ]
    
    try:
        result1 = subprocess.run(curl_cmd1, capture_output=True, text=True, timeout=10)
        print(f"✅ First message response (first 200 chars): {result1.stdout[:200]}")
        
        # Wait a moment
        time.sleep(2)
        
        # Test 2: Ask for diagram (should have context)
        print("\n2️⃣ Testing second message: 'Show me a diagram'")
        
        message2 = {
            "message": "Show me a diagram",
            "conversation_id": session_id
        }
        
        curl_cmd2 = [
            "curl", "-X", "POST", 
            "http://localhost:8000/chat/stream",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(message2),
            "--no-buffer"
        ]
        
        result2 = subprocess.run(curl_cmd2, capture_output=True, text=True, timeout=10)
        print(f"✅ Second message response (first 200 chars): {result2.stdout[:200]}")
        
        # Check for context awareness
        if "baxter" in result2.stdout.lower() or "oven" in result2.stdout.lower():
            print("🎯 SUCCESS: Response shows context awareness!")
            print("🧠 Message history is working correctly")
        else:
            print("❌ FAILURE: Response doesn't show context awareness")
            print("💔 Message history may not be persisting")
            
    except subprocess.TimeoutExpired:
        print("⏰ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_message_history()