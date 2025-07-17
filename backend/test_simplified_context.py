"""
Test the simplified architecture for context preservation
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def test_simplified_context():
    """Test the simplified architecture for context preservation"""
    
    session_id = "test_simplified_context"
    
    print("🧪 Testing simplified architecture for context preservation...")
    print(f"📋 Session ID: {session_id}")
    
    # Clear any existing history
    voice_orchestrator.clear_all_contexts()
    
    # Test 1: Equipment cleaning question
    print("\n1️⃣ Testing: 'How do I clean the Baxter oven?'")
    
    try:
        response1 = await voice_orchestrator.process_voice_message(
            message="How do I clean the Baxter oven?",
            relevant_docs=[],
            session_id=session_id
        )
        
        print(f"✅ Response: {response1.text_response[:100]}...")
        print(f"📊 Equipment mentioned: {response1.equipment_mentioned}")
        
        # Check message history
        history1 = voice_orchestrator.get_message_history(session_id)
        print(f"📊 Message history count: {len(history1)}")
        
    except Exception as e:
        print(f"❌ First call failed: {e}")
        return
    
    # Test 2: Follow-up with context - THE CRITICAL TEST
    print("\n2️⃣ Testing: 'Show me a diagram'")
    
    try:
        response2 = await voice_orchestrator.process_voice_message(
            message="Show me a diagram",
            relevant_docs=[],
            session_id=session_id
        )
        
        print(f"✅ Response: {response2.text_response[:100]}...")
        print(f"📊 Equipment mentioned: {response2.equipment_mentioned}")
        
        # Check message history growth
        history2 = voice_orchestrator.get_message_history(session_id)
        print(f"📊 Message history count: {len(history2)}")
        
        # Check for context preservation
        if "baxter" in response2.text_response.lower() or "oven" in response2.text_response.lower():
            print("🎯 SUCCESS: Context preserved with simplified architecture!")
            print("✅ Single agent with simplified flow working correctly!")
        else:
            print("❌ FAILURE: Context not preserved")
            print(f"🔍 Response: {response2.text_response}")
            
        # Check visual citations
        if hasattr(response2, 'visual_citations') and response2.visual_citations:
            print(f"📷 Visual citations: {len(response2.visual_citations)} found")
        else:
            print("📷 No visual citations found")
            
    except Exception as e:
        print(f"❌ Second call failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n📈 Message history progression: {len(history1)} → {len(history2)}")

if __name__ == "__main__":
    asyncio.run(test_simplified_context())