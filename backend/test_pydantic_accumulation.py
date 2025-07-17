"""
Test PydanticAI message accumulation behavior
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_agent

async def test_pydantic_accumulation():
    """Test how PydanticAI accumulates messages"""
    
    print("🧪 Testing PydanticAI message accumulation...")
    
    if not voice_agent:
        print("❌ voice_agent is None - initialization failed")
        return
    
    # Test 1: First call with empty history
    print("\n1️⃣ First call with empty history")
    
    result1 = await voice_agent.run("How do I clean the Baxter oven?", message_history=[])
    messages1 = result1.all_messages()
    print(f"📊 Messages after first call: {len(messages1)}")
    
    # Show message types
    for i, msg in enumerate(messages1):
        print(f"  {i+1}. {type(msg).__name__}: {str(msg)[:50]}...")
    
    # Test 2: Second call with accumulated history
    print("\n2️⃣ Second call with accumulated history")
    
    result2 = await voice_agent.run("Show me a diagram", message_history=messages1)
    messages2 = result2.all_messages()
    print(f"📊 Messages after second call: {len(messages2)}")
    
    # Show message types
    for i, msg in enumerate(messages2):
        print(f"  {i+1}. {type(msg).__name__}: {str(msg)[:50]}...")
    
    # Test 3: Check if context was preserved in second call
    response2_text = str(result2.output)
    print(f"\n🔍 Second response: {response2_text[:100]}...")
    
    if "baxter" in response2_text.lower() or "oven" in response2_text.lower():
        print("🎯 SUCCESS: Context preserved in second call!")
        print("✅ PydanticAI message accumulation working correctly")
    else:
        print("❌ FAILURE: Context not preserved in second call")
        print("💔 PydanticAI message accumulation may have issues")
    
    # Test 4: Third call to see continued accumulation
    print("\n3️⃣ Third call with further accumulated history")
    
    result3 = await voice_agent.run("What temperature should I use?", message_history=messages2)
    messages3 = result3.all_messages()
    print(f"📊 Messages after third call: {len(messages3)}")
    
    response3_text = str(result3.output)
    print(f"🔍 Third response: {response3_text[:100]}...")
    
    # Check if context about Baxter oven cleaning is still preserved
    if "baxter" in response3_text.lower() or "oven" in response3_text.lower():
        print("🎯 SUCCESS: Context preserved through multiple calls!")
    else:
        print("❌ Context lost in third call")
    
    print(f"\n📈 Message accumulation: {len(messages1)} → {len(messages2)} → {len(messages3)}")

if __name__ == "__main__":
    asyncio.run(test_pydantic_accumulation())