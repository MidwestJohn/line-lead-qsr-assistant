"""
Test the orchestrator with simplified single agent architecture
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def test_orchestrator_simplified():
    """Test the orchestrator with simplified single agent architecture"""
    
    session_id = "test_orchestrator_simplified"
    
    print("🧪 Testing orchestrator with simplified single agent architecture...")
    print(f"📋 Session ID: {session_id}")
    
    # Clear any existing history
    voice_orchestrator.clear_all_contexts()
    
    # Test 1: Equipment cleaning question
    print("\n1️⃣ Testing: 'How do I clean the Baxter oven?'")
    
    response1 = await voice_orchestrator.process_voice_message(
        message="How do I clean the Baxter oven?",
        relevant_docs=[],
        session_id=session_id
    )
    
    print(f"✅ Response: {response1.text_response[:100]}...")
    print(f"📊 Primary agent: {response1.primary_agent}")
    print(f"📊 Equipment mentioned: {response1.equipment_mentioned}")
    print(f"📊 Coordination strategy: {response1.coordination_strategy}")
    
    # Check message history
    history1 = voice_orchestrator.get_message_history(session_id)
    print(f"📊 Message history count: {len(history1)}")
    
    # Test 2: Follow-up with context - this should work now!
    print("\n2️⃣ Testing: 'Show me a diagram'")
    
    response2 = await voice_orchestrator.process_voice_message(
        message="Show me a diagram",
        relevant_docs=[],
        session_id=session_id
    )
    
    print(f"✅ Response: {response2.text_response[:100]}...")
    print(f"📊 Primary agent: {response2.primary_agent}")
    print(f"📊 Equipment mentioned: {response2.equipment_mentioned}")
    print(f"📊 Coordination strategy: {response2.coordination_strategy}")
    
    # Check message history growth
    history2 = voice_orchestrator.get_message_history(session_id)
    print(f"📊 Message history count: {len(history2)}")
    
    # Check if context was preserved
    if "baxter" in response2.text_response.lower() or "oven" in response2.text_response.lower():
        print("🎯 SUCCESS: Context preserved with orchestrator!")
        print("🧠 Single agent architecture working correctly!")
    else:
        print("❌ FAILURE: Context not preserved")
        print("💔 Single agent architecture needs debugging")
    
    # Test 3: Different domain (should still work with same agent)
    print("\n3️⃣ Testing: 'What's the safe temperature for chicken?'")
    
    response3 = await voice_orchestrator.process_voice_message(
        message="What's the safe temperature for chicken?",
        relevant_docs=[],
        session_id=session_id
    )
    
    print(f"✅ Response: {response3.text_response[:100]}...")
    print(f"📊 Primary agent: {response3.primary_agent}")
    print(f"📊 Safety priority: {getattr(response3, 'safety_priority', False)}")
    
    # Check message history continues to grow
    history3 = voice_orchestrator.get_message_history(session_id)
    print(f"📊 Message history count: {len(history3)}")
    
    print("\n🎉 Orchestrator simplified single agent test complete!")
    print(f"📈 Message history grew from {len(history1)} → {len(history2)} → {len(history3)}")
    
    # Show some message history for debugging
    print(f"\n🔍 Recent message history:")
    for i, msg in enumerate(history3[-3:]):
        try:
            print(f"  {i+1}. {msg.role}: {str(msg.content)[:50]}...")
        except:
            print(f"  {i+1}. {type(msg).__name__}: {str(msg)[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_orchestrator_simplified())