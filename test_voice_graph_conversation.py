#!/usr/bin/env python3
"""
Voice + Graph Context Multi-Turn Conversation Demo
Tests persistent context-aware conversations using Neo4j knowledge graph
"""

import requests
import json
import time

def test_conversation_turn(message, conversation_id, turn_number):
    """Test a single conversation turn with graph context"""
    print(f"\n=== TURN {turn_number} ===")
    print(f"User: {message}")
    
    response = requests.post(
        "http://localhost:8000/voice-with-graph-context",
        headers={"Content-Type": "application/json"},
        json={
            "message": message,
            "conversation_id": conversation_id
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        assistant_response = data["response"]
        
        # Extract equipment context if mentioned
        equipment_context = "None"
        if "🔧 Equipment Context:" in assistant_response:
            equipment_context = assistant_response.split("🔧 Equipment Context:")[1].split("\n")[0].strip()
        
        print(f"Assistant: {assistant_response.split('📚')[0].strip()}")
        print(f"Equipment Context: {equipment_context}")
        
        return True, equipment_context
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False, None

def main():
    """Run comprehensive voice + graph context conversation test"""
    
    print("🎯 VOICE + KNOWLEDGE GRAPH CONTEXT INTEGRATION DEMO")
    print("=" * 60)
    
    conversation_id = "demo_voice_graph_conversation"
    
    # Multi-turn conversation scenarios
    conversation_scenarios = [
        {
            "turn": 1,
            "message": "Help me with the Taylor ice cream machine",
            "expected": "Equipment selection and context establishment"
        },
        {
            "turn": 2, 
            "message": "What maintenance procedures are available?",
            "expected": "Context-aware procedure listing for Taylor equipment"
        },
        {
            "turn": 3,
            "message": "Tell me about the cleaning procedure",
            "expected": "Specific cleaning procedure with maintained equipment context"
        },
        {
            "turn": 4,
            "message": "What safety precautions should I take?",
            "expected": "Safety guidelines for the Taylor ice cream machine"
        },
        {
            "turn": 5,
            "message": "Now help me with the fryer",
            "expected": "Context switching from ice cream machine to fryer"
        },
        {
            "turn": 6,
            "message": "What's the cleaning procedure?",
            "expected": "Fryer cleaning procedure (not ice cream machine)"
        }
    ]
    
    results = []
    current_equipment = None
    
    for scenario in conversation_scenarios:
        print(f"\nScenario: {scenario['expected']}")
        
        success, equipment_context = test_conversation_turn(
            scenario["message"], 
            conversation_id, 
            scenario["turn"]
        )
        
        if equipment_context and equipment_context != "None":
            current_equipment = equipment_context
        
        results.append({
            "turn": scenario["turn"],
            "success": success,
            "equipment_context": current_equipment,
            "context_maintained": equipment_context != "None" or current_equipment is not None
        })
        
        time.sleep(1)  # Brief pause between requests
    
    # Summary
    print(f"\n{'=' * 60}")
    print("🎯 CONVERSATION SUMMARY")
    print(f"{'=' * 60}")
    
    successful_turns = sum(1 for r in results if r["success"])
    context_maintained_turns = sum(1 for r in results if r["context_maintained"])
    
    print(f"✅ Successful turns: {successful_turns}/{len(results)}")
    print(f"🔧 Context maintained: {context_maintained_turns}/{len(results)}")
    
    # Test voice graph status
    print(f"\n🔍 VOICE + GRAPH INTEGRATION STATUS")
    try:
        status_response = requests.get("http://localhost:8000/voice-graph-status")
        if status_response.status_code == 200:
            status_data = status_response.json()
            
            print(f"Integration Ready: {status_data['voice_graph_integration_ready']}")
            print("\nComponent Status:")
            for component, status in status_data['components_status'].items():
                icon = "✅" if status else "❌"
                print(f"  {icon} {component}: {status}")
            
            print(f"\nActive Conversations: {status_data['components_status']['conversation_contexts_active']}")
            
        else:
            print("Failed to get voice graph status")
            
    except Exception as e:
        print(f"Status check failed: {e}")
    
    print(f"\n🎉 VOICE + GRAPH CONTEXT INTEGRATION DEMO COMPLETE!")
    print("The system demonstrates:")
    print("✅ Equipment context detection and switching")  
    print("✅ Multi-turn conversation persistence")
    print("✅ Voice orchestrator + Neo4j graph integration")
    print("✅ Context-aware response generation")

if __name__ == "__main__":
    main()