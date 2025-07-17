"""
Test image tool functionality through the agent
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_agent import voice_orchestrator

async def test_image_tool_functionality():
    """Test image tool functionality through the agent"""
    
    session_id = "test_image_tools"
    
    print("🧪 Testing image tool functionality through the agent...")
    print(f"📋 Session ID: {session_id}")
    
    # Clear any existing history
    voice_orchestrator.clear_all_contexts()
    
    # Test cases for image tool functionality
    test_cases = [
        {
            "name": "Explicit Equipment + Diagram Request",
            "messages": [
                "How do I clean the Baxter oven?",
                "Show me a diagram of the Baxter oven"
            ]
        },
        {
            "name": "Context-Aware Diagram Request", 
            "messages": [
                "Tell me about the Taylor fryer",
                "Show me a diagram"
            ]
        },
        {
            "name": "Vague Image Request",
            "messages": [
                "What's the procedure for ice machine maintenance?",
                "Can I see what it looks like?"
            ]
        },
        {
            "name": "Multiple Equipment Context",
            "messages": [
                "How do I clean the fryer?",
                "What about the grill?", 
                "Show me both diagrams"
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔧 Testing: {test_case['name']}")
        print("-" * 50)
        
        # Start fresh session for each test
        test_session = f"{session_id}_{test_case['name'].replace(' ', '_')}"
        voice_orchestrator.clear_all_contexts()
        
        for i, message in enumerate(test_case['messages']):
            print(f"\n{i+1}️⃣ Message: '{message}'")
            
            try:
                response = await voice_orchestrator.process_voice_message(
                    message=message,
                    relevant_docs=[],
                    session_id=test_session
                )
                
                print(f"✅ Response: {response.text_response[:100]}...")
                print(f"📊 Equipment mentioned: {response.equipment_mentioned}")
                
                # Check for visual citations
                if hasattr(response, 'visual_citations') and response.visual_citations:
                    print(f"📷 Visual citations: {len(response.visual_citations)} found")
                    for j, citation in enumerate(response.visual_citations[:2]):  # Show first 2
                        print(f"  {j+1}. {citation.get('title', 'Unknown')}: {citation.get('content_preview', 'No preview')[:50]}...")
                else:
                    print("📷 No visual citations found")
                
                # Check message history
                history = voice_orchestrator.get_message_history(test_session)
                print(f"📊 Message history: {len(history)} messages")
                
            except Exception as e:
                print(f"❌ Message failed: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"\n✅ {test_case['name']} test complete")
    
    print("\n🎉 Image tool functionality test complete!")

if __name__ == "__main__":
    asyncio.run(test_image_tool_functionality())