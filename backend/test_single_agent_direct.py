"""
Test single agent directly without broken orchestrator
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test the single voice_agent directly
from voice_agent import voice_agent

async def test_single_agent_direct():
    """Test single voice_agent directly"""
    
    print("🧪 Testing single voice_agent directly...")
    
    if not voice_agent:
        print("❌ voice_agent is None - initialization failed")
        return
        
    print("✅ voice_agent initialized successfully")
    
    # Test 1: Equipment cleaning question
    print("\n1️⃣ Testing: 'How do I clean the Baxter oven?'")
    
    result1 = await voice_agent.run("How do I clean the Baxter oven?")
    response1 = result1.data
    
    print(f"✅ Response: {response1.text_response[:100]}...")
    print(f"📊 Equipment mentioned: {response1.equipment_mentioned}")
    
    # Test 2: Context test - but we'll use message history
    print("\n2️⃣ Testing with message history: 'Show me a diagram'")
    
    # Get message history from first call
    messages = result1.all_messages()
    print(f"📊 Message history length: {len(messages)}")
    
    result2 = await voice_agent.run("Show me a diagram", message_history=messages)
    response2 = result2.data
    
    print(f"✅ Response: {response2.text_response[:100]}...")
    print(f"📊 Equipment mentioned: {response2.equipment_mentioned}")
    
    # Check if context was preserved
    if "baxter" in response2.text_response.lower() or "oven" in response2.text_response.lower():
        print("🎯 SUCCESS: Context preserved with message history!")
    else:
        print("❌ FAILURE: Context not preserved")
    
    # Test 3: Safety question
    print("\n3️⃣ Testing: 'What's the safe temperature for chicken?'")
    
    result3 = await voice_agent.run("What's the safe temperature for chicken?")
    response3 = result3.data
    
    print(f"✅ Response: {response3.text_response[:100]}...")
    print(f"📊 Safety priority: {getattr(response3, 'safety_priority', False)}")
    
    print("\n🎉 Single agent direct test complete!")

if __name__ == "__main__":
    asyncio.run(test_single_agent_direct())