"""
Test message history directly through voice_agent
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def test_message_history_direct():
    """Test message history persistence directly"""
    
    session_id = "test_session_direct"
    
    print("🧪 Testing message history persistence directly...")
    print(f"📋 Session ID: {session_id}")
    
    # Test 1: Ask about Baxter oven
    print("\n1️⃣ First message: 'How do I clean the Baxter oven?'")
    
    response1 = await voice_orchestrator.process_voice_message(
        message="How do I clean the Baxter oven?",
        relevant_docs=[],
        session_id=session_id
    )
    
    print(f"✅ First response: {response1.text_response[:100]}...")
    
    # Check message history count
    history1 = voice_orchestrator.get_message_history(session_id)
    print(f"📊 Message history count after first message: {len(history1)}")
    
    # Test 2: Ask for diagram (should have context)
    print("\n2️⃣ Second message: 'Show me a diagram'")
    
    response2 = await voice_orchestrator.process_voice_message(
        message="Show me a diagram",
        relevant_docs=[],
        session_id=session_id
    )
    
    print(f"✅ Second response: {response2.text_response[:100]}...")
    
    # Check message history count
    history2 = voice_orchestrator.get_message_history(session_id)
    print(f"📊 Message history count after second message: {len(history2)}")
    
    # Check if context is preserved
    if "baxter" in response2.text_response.lower() or "oven" in response2.text_response.lower():
        print("🎯 SUCCESS: Context is preserved!")
        print("🧠 Message history is working correctly")
    else:
        print("❌ FAILURE: Context not preserved")
        print("💔 Message history may not be working")
        
    # Print some message history for debugging
    print(f"\n🔍 Message history contents:")
    for i, msg in enumerate(history2[-4:]):  # Show last 4 messages
        print(f"  {i+1}. {msg.role}: {str(msg.content)[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_message_history_direct())