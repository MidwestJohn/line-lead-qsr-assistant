"""
Debug voice orchestrator level to see what's happening
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def debug_orchestrator_level():
    """Debug the voice orchestrator level"""
    
    session_id = "debug_orchestrator"
    
    print("🔍 Debugging voice orchestrator level...")
    print(f"📋 Session ID: {session_id}")
    
    # Clear any existing history
    voice_orchestrator.clear_all_contexts()
    
    # Test 1: First call - see what agent gets selected
    print("\n1️⃣ First call: 'How do I clean the Baxter oven?'")
    
    print("🔍 Before first call:")
    before_history = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(before_history)}")
    
    # Check server logs to see agent classification
    print("🤖 Calling voice orchestrator...")
    
    response1 = await voice_orchestrator.process_voice_message(
        message="How do I clean the Baxter oven?",
        relevant_docs=[],
        session_id=session_id
    )
    
    print("🔍 After first call:")
    after_history = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(after_history)}")
    print(f"  Agent type: {response1.primary_agent}")
    print(f"  Response: {response1.text_response[:100]}...")
    
    # Test 2: Second call - see what agent gets selected
    print("\n2️⃣ Second call: 'Show me a diagram'")
    
    print("🔍 Before second call:")
    before_history2 = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(before_history2)}")
    
    print("🤖 Calling voice orchestrator...")
    
    response2 = await voice_orchestrator.process_voice_message(
        message="Show me a diagram",
        relevant_docs=[],
        session_id=session_id
    )
    
    print("🔍 After second call:")
    after_history2 = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(after_history2)}")
    print(f"  Agent type: {response2.primary_agent}")
    print(f"  Response: {response2.text_response[:100]}...")
    
    # Test for context preservation
    if "baxter" in response2.text_response.lower() or "oven" in response2.text_response.lower():
        print("🎯 SUCCESS: Context preserved at orchestrator level!")
    else:
        print("❌ FAILURE: Context not preserved at orchestrator level")
        
    # Show coordinate strategy
    print(f"  Coordination strategy: {response2.coordination_strategy}")
    
    # If different agents, that could be the issue
    if response1.primary_agent != response2.primary_agent:
        print(f"⚠️  Different agents used: {response1.primary_agent} → {response2.primary_agent}")
        print("This could explain why context isn't preserved!")
    else:
        print(f"✅ Same agent used: {response1.primary_agent}")

if __name__ == "__main__":
    asyncio.run(debug_orchestrator_level())