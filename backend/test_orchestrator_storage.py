"""
Test orchestrator message history storage directly
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def test_orchestrator_storage():
    """Test orchestrator message history storage directly"""
    
    session_id = "test_storage"
    
    print("🧪 Testing orchestrator message history storage...")
    print(f"📋 Session ID: {session_id}")
    
    # Clear any existing history
    voice_orchestrator.clear_all_contexts()
    
    # Test storage directly
    print("\n1️⃣ Testing storage directly")
    
    # Simulate some messages by running a simple agent call first
    from voice_agent import voice_agent
    
    if not voice_agent:
        print("❌ voice_agent is None")
        return
    
    # Get some real messages to test storage
    test_result = await voice_agent.run("Test message")
    test_messages = test_result.all_messages()
    print(f"📊 Generated {len(test_messages)} test messages")
    
    # Store messages
    voice_orchestrator.store_message_history(session_id, test_messages)
    
    # Retrieve messages
    retrieved = voice_orchestrator.get_message_history(session_id)
    print(f"📊 Stored: {len(test_messages)}, Retrieved: {len(retrieved)}")
    
    if len(retrieved) == len(test_messages):
        print("✅ Direct storage/retrieval working")
    else:
        print("❌ Direct storage/retrieval failed")
        return
    
    # Test 2: Simulate what happens in process_voice_message
    print("\n2️⃣ Testing process_voice_message logic")
    
    # First call
    print("🔍 First call simulation...")
    
    # This is what happens in process_voice_message
    initial_history = voice_orchestrator.get_message_history(session_id)
    print(f"📊 Initial history: {len(initial_history)}")
    
    # Simulate agent.run() result
    from voice_agent import voice_agent
    
    if voice_agent:
        result1 = await voice_agent.run("How do I clean the Baxter oven?", message_history=initial_history)
        new_messages1 = result1.all_messages()
        print(f"📊 Messages from first agent.run(): {len(new_messages1)}")
        
        # Store the result
        voice_orchestrator.store_message_history(session_id, new_messages1)
        
        # Verify storage
        stored1 = voice_orchestrator.get_message_history(session_id)
        print(f"📊 Stored after first call: {len(stored1)}")
        
        # Second call
        print("\n🔍 Second call simulation...")
        
        # Get stored history
        current_history = voice_orchestrator.get_message_history(session_id)
        print(f"📊 Current history before second call: {len(current_history)}")
        
        # Run second agent call
        result2 = await voice_agent.run("Show me a diagram", message_history=current_history)
        new_messages2 = result2.all_messages()
        print(f"📊 Messages from second agent.run(): {len(new_messages2)}")
        
        # Store the result
        voice_orchestrator.store_message_history(session_id, new_messages2)
        
        # Verify storage
        stored2 = voice_orchestrator.get_message_history(session_id)
        print(f"📊 Stored after second call: {len(stored2)}")
        
        # Check if context preserved
        response2_text = str(result2.output)
        if "baxter" in response2_text.lower() or "oven" in response2_text.lower():
            print("🎯 SUCCESS: Context preserved in orchestrator simulation!")
            print("✅ The orchestrator logic should work correctly")
        else:
            print("❌ FAILURE: Context not preserved")
            print("💔 There might be an issue with the orchestrator logic")
            
        print(f"\n📈 Message progression: {len(initial_history)} → {len(stored1)} → {len(stored2)}")
    
    else:
        print("❌ voice_agent is None")

if __name__ == "__main__":
    asyncio.run(test_orchestrator_storage())