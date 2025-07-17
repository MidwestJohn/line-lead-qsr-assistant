"""
Test the simplified single agent architecture
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def test_simplified_agent():
    """Test the simplified single agent architecture"""
    
    session_id = "test_simplified"
    
    print("🧪 Testing simplified single agent architecture...")
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
    
    # Test 2: Follow-up with context
    print("\n2️⃣ Testing: 'Show me a diagram'")
    
    response2 = await voice_orchestrator.process_voice_message(
        message="Show me a diagram",
        relevant_docs=[],
        session_id=session_id
    )
    
    print(f"✅ Response: {response2.text_response[:100]}...")
    print(f"📊 Primary agent: {response2.primary_agent}")
    print(f"📊 Equipment mentioned: {response2.equipment_mentioned}")
    
    # Check if context was preserved
    if "baxter" in response2.text_response.lower() or "oven" in response2.text_response.lower():
        print("🎯 SUCCESS: Context preserved in simplified architecture!")
    else:
        print("❌ FAILURE: Context not preserved")
    
    # Test 3: Different domain (safety)
    print("\n3️⃣ Testing: 'What's the safe temperature for chicken?'")
    
    response3 = await voice_orchestrator.process_voice_message(
        message="What's the safe temperature for chicken?",
        relevant_docs=[],
        session_id=session_id
    )
    
    print(f"✅ Response: {response3.text_response[:100]}...")
    print(f"📊 Primary agent: {response3.primary_agent}")
    print(f"📊 Safety priority: {getattr(response3, 'safety_priority', False)}")
    
    # Test 4: Maintenance query
    print("\n4️⃣ Testing: 'How often should I clean the fryer?'")
    
    response4 = await voice_orchestrator.process_voice_message(
        message="How often should I clean the fryer?",
        relevant_docs=[],
        session_id=session_id
    )
    
    print(f"✅ Response: {response4.text_response[:100]}...")
    print(f"📊 Primary agent: {response4.primary_agent}")
    print(f"📊 Equipment mentioned: {response4.equipment_mentioned}")
    
    print("\n🎉 Simplified single agent architecture test complete!")

if __name__ == "__main__":
    asyncio.run(test_simplified_agent())