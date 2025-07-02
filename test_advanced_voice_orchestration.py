#!/usr/bin/env python3

"""
Test the advanced PydanticAI voice orchestration features
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from voice_agent import voice_orchestrator, ConversationIntent

async def test_conversation_flow():
    """Test the sophisticated conversation management"""
    
    print("🧪 Testing Advanced PydanticAI Voice Orchestration")
    print("=" * 60)
    
    session_id = "test_session_123"
    
    # Test 1: Equipment extraction and context awareness
    print("\n1️⃣ Testing Smart Context Awareness:")
    response1 = await voice_orchestrator.process_voice_message(
        "How do I clean the fryer?",
        session_id=session_id
    )
    print(f"Equipment detected: {response1.equipment_mentioned}")
    print(f"Response: {response1.text_response}")
    print(f"Continue listening: {response1.should_continue_listening}")
    print(f"Response type: {response1.response_type}")
    
    # Test 2: Follow-up with context referencing
    print("\n2️⃣ Testing Conversation Management:")
    response2 = await voice_orchestrator.process_voice_message(
        "What about the oil change?",
        session_id=session_id
    )
    print(f"Intent: {response2.detected_intent}")
    print(f"Context references: {response2.context_references}")
    print(f"Response: {response2.text_response}")
    
    # Test 3: Equipment switch detection
    print("\n3️⃣ Testing Equipment Switch:")
    response3 = await voice_orchestrator.process_voice_message(
        "Now show me how to clean the grill",
        session_id=session_id
    )
    print(f"Equipment switch detected: {response3.equipment_switch_detected}")
    print(f"New equipment: {response3.equipment_mentioned}")
    print(f"Response: {response3.text_response}")
    
    # Test 4: Conversation completion
    print("\n4️⃣ Testing Conversation Completion:")
    response4 = await voice_orchestrator.process_voice_message(
        "Thanks, that's all I needed",
        session_id=session_id
    )
    print(f"Conversation complete: {response4.conversation_complete}")
    print(f"Continue listening: {response4.should_continue_listening}")
    print(f"Response: {response4.text_response}")
    
    # Test 5: Conversation summary
    print("\n5️⃣ Testing Conversation Summary:")
    summary = voice_orchestrator.get_conversation_summary(session_id)
    print(f"Summary: {summary}")
    
    print("\n" + "=" * 60)
    print("✅ Advanced voice orchestration test completed!")

async def test_safety_priority():
    """Test safety-first response handling"""
    print("\n🔥 Testing Safety Priority Features:")
    
    response = await voice_orchestrator.process_voice_message(
        "What temperature should the fryer be at?",
        session_id="safety_test"
    )
    
    print(f"Safety priority: {response.safety_priority}")
    print(f"Response type: {response.response_type}")
    print(f"Response: {response.text_response}")

async def test_procedure_tracking():
    """Test multi-step procedure tracking"""
    print("\n📋 Testing Procedure Tracking:")
    
    session_id = "procedure_test"
    
    # Start a procedure
    response1 = await voice_orchestrator.process_voice_message(
        "Walk me through cleaning the ice machine step by step",
        session_id=session_id
    )
    
    print(f"Procedure info: {response1.procedure_step_info}")
    print(f"Workflow phase: {response1.workflow_phase}")
    print(f"Response: {response1.text_response}")

if __name__ == "__main__":
    async def main():
        await test_conversation_flow()
        await test_safety_priority()
        await test_procedure_tracking()
    
    asyncio.run(main())