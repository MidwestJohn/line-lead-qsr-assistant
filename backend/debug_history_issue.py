"""
Debug the exact message history issue
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def debug_history_issue():
    """Debug what's happening with message history"""
    
    session_id = "debug_session"
    
    print("🔍 Debugging message history issue...")
    print(f"📋 Session ID: {session_id}")
    
    # Clear any existing history
    voice_orchestrator.clear_all_contexts()
    
    # Check initial state
    initial_history = voice_orchestrator.get_message_history(session_id)
    print(f"📊 Initial message history count: {len(initial_history)}")
    
    # Test 1: Ask about Baxter oven
    print("\n1️⃣ First message: 'How do I clean the Baxter oven?'")
    
    print("🔍 Before first call:")
    before_history = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(before_history)}")
    
    response1 = await voice_orchestrator.process_voice_message(
        message="How do I clean the Baxter oven?",
        relevant_docs=[],
        session_id=session_id
    )
    
    print("🔍 After first call:")
    after_history = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(after_history)}")
    print(f"  Response: {response1.text_response[:100]}...")
    
    # Show the actual messages in history
    print("\n📜 Message history contents after first call:")
    for i, msg in enumerate(after_history):
        try:
            print(f"  {i+1}. {msg.role}: {str(msg.content)[:50]}...")
        except:
            print(f"  {i+1}. {type(msg)}: {str(msg)[:50]}...")
    
    # Test 2: Ask for diagram
    print("\n2️⃣ Second message: 'Show me a diagram'")
    
    print("🔍 Before second call:")
    before_history2 = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(before_history2)}")
    
    response2 = await voice_orchestrator.process_voice_message(
        message="Show me a diagram",
        relevant_docs=[],
        session_id=session_id
    )
    
    print("🔍 After second call:")
    after_history2 = voice_orchestrator.get_message_history(session_id)
    print(f"  Message count: {len(after_history2)}")
    print(f"  Response: {response2.text_response[:100]}...")
    
    # Show the actual messages in history
    print("\n📜 Message history contents after second call:")
    for i, msg in enumerate(after_history2):
        try:
            print(f"  {i+1}. {msg.role}: {str(msg.content)[:50]}...")
        except:
            print(f"  {i+1}. {type(msg)}: {str(msg)[:50]}...")

if __name__ == "__main__":
    asyncio.run(debug_history_issue())