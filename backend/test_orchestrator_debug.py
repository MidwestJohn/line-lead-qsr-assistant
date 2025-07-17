"""
Debug the orchestrator message history issue
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def debug_orchestrator():
    """Debug the orchestrator message history issue"""
    
    session_id = "debug_orchestrator"
    
    print("🔍 Debugging orchestrator message history...")
    print(f"📋 Session ID: {session_id}")
    
    # Clear any existing history
    voice_orchestrator.clear_all_contexts()
    
    # Test 1: First call
    print("\n1️⃣ First call: 'How do I clean the Baxter oven?'")
    
    print("🔍 Before first call:")
    before_history = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(before_history)}")
    
    try:
        response1 = await voice_orchestrator.process_voice_message(
            message="How do I clean the Baxter oven?",
            relevant_docs=[],
            session_id=session_id
        )
        
        print("🔍 After first call:")
        after_history = voice_orchestrator.get_message_history(session_id)
        print(f"  Message count: {len(after_history)}")
        print(f"  Response: {response1.text_response[:100]}...")
        
    except Exception as e:
        print(f"❌ First call failed: {e}")
        return
    
    # Test 2: Second call with detailed debugging
    print("\n2️⃣ Second call: 'Show me a diagram'")
    
    print("🔍 Before second call:")
    before_history2 = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(before_history2)}")
    
    try:
        response2 = await voice_orchestrator.process_voice_message(
            message="Show me a diagram",
            relevant_docs=[],
            session_id=session_id
        )
        
        print("🔍 After second call:")
        after_history2 = voice_orchestrator.get_message_history(session_id)
        print(f"  Message count: {len(after_history2)}")
        print(f"  Response: {response2.text_response[:100]}...")
        
        # Analyze the difference
        if len(after_history2) > len(before_history2):
            print(f"✅ Message history grew by {len(after_history2) - len(before_history2)}")
        else:
            print(f"❌ Message history didn't grow (stayed at {len(after_history2)})")
            print("🔍 This suggests the orchestrator is replacing history instead of accumulating")
            
    except Exception as e:
        print(f"❌ Second call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_orchestrator())