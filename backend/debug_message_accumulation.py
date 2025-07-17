"""
Debug message accumulation issue
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def debug_message_accumulation():
    """Debug how messages are accumulated"""
    
    session_id = "debug_accumulation"
    
    print("🔍 Debugging message accumulation...")
    print(f"📋 Session ID: {session_id}")
    
    # Clear any existing history
    voice_orchestrator.clear_all_contexts()
    
    # Test 1: First call with manual inspection
    print("\n1️⃣ First call: Manual agent inspection")
    
    # Get the maintenance agent directly
    from voice_agent import qsr_maintenance_agent
    
    if qsr_maintenance_agent:
        print("🔧 Testing maintenance agent directly...")
        
        # Test with empty history
        empty_history = []
        print(f"📥 Input history: {len(empty_history)} messages")
        
        result1 = await qsr_maintenance_agent.run(
            user_prompt="How do I clean the Baxter oven?",
            message_history=empty_history
        )
        
        all_messages_1 = result1.all_messages()
        print(f"📤 Output all_messages: {len(all_messages_1)} messages")
        
        # Store them
        voice_orchestrator.store_message_history(session_id, all_messages_1)
        stored_1 = voice_orchestrator.get_message_history(session_id)
        print(f"💾 Stored messages: {len(stored_1)} messages")
        
        # Test 2: Second call with previous history
        print("\n2️⃣ Second call: Using stored history")
        
        print(f"📥 Input history: {len(stored_1)} messages")
        
        result2 = await qsr_maintenance_agent.run(
            user_prompt="Show me a diagram",
            message_history=stored_1
        )
        
        all_messages_2 = result2.all_messages()
        print(f"📤 Output all_messages: {len(all_messages_2)} messages")
        
        # Store them
        voice_orchestrator.store_message_history(session_id, all_messages_2)
        stored_2 = voice_orchestrator.get_message_history(session_id)
        print(f"💾 Stored messages: {len(stored_2)} messages")
        
        # Check if second response has context
        response_text = result2.output
        print(f"📝 Second response: {str(response_text)[:100]}...")
        
        if "baxter" in str(response_text).lower() or "oven" in str(response_text).lower():
            print("🎯 SUCCESS: Context preserved!")
        else:
            print("❌ FAILURE: Context not preserved")
            
        # Show message types
        print("\n🔍 Message types in final history:")
        for i, msg in enumerate(stored_2[-3:]):  # Show last 3
            try:
                print(f"  {i+1}. {type(msg).__name__}: {str(msg)[:50]}...")
            except:
                print(f"  {i+1}. {type(msg)}: Error showing content")
    
    else:
        print("❌ No maintenance agent available")

if __name__ == "__main__":
    asyncio.run(debug_message_accumulation())