#!/usr/bin/env python3

import os
import sys
sys.path.append('.')
from openai_integration import QSRAssistant

def test_exact_system_conditions():
    """Test using the exact same conditions as the live system"""
    
    assistant = QSRAssistant()
    
    print(f"Model: {assistant.model}")
    print(f"Temperature: {assistant.temperature}")
    print(f"Available: {assistant.is_available()}")
    print("\n" + "="*50 + "\n")
    
    # Simulate the exact conditions from the live system
    user_question = "How do I clean the fryer?"
    
    # Use the exact same document context that's being used
    relevant_chunks = [
        {
            'text': 'Turn off the hoods and fryers and let cool down 30 or 40 minutes before cleaning. Fill a spray bottle with an approved degreaser and cover the fryers with trays to avoid oil contamination. Wear safety glasses to avoid eye injury when cleaning the hood.',
            'metadata': {'filename': 'Preview-Line Cook Training Manual - QSR.pdf'},
            'similarity': 0.60
        },
        {
            'text': 'Turn off the hoods and fryers and let cool down 30 or 40 minutes before cleaning. Fill a spray bottle with an approved degreaser and cover the fryers with trays to avoid oil contamination. Wear safety glasses to avoid eye injury when cleaning the hood.',
            'metadata': {'filename': 'Preview-Line Cook Training Manual - QSR.pdf'},
            'similarity': 0.60
        },
        {
            'text': 'Turn off the hoods and fryers and let cool down 30 or 40 minutes before cleaning. Fill a spray bottle with an approved degreaser and cover the fryers with trays to avoid oil contamination. Wear safety glasses to avoid eye injury when cleaning the hood.',
            'metadata': {'filename': 'Preview-Line Cook Training Manual - QSR.pdf'},
            'similarity': 0.58
        }
    ]
    
    print("🧪 Testing with exact same conditions as live system...")
    
    # Use the same method that the live system uses
    try:
        import asyncio
        result = asyncio.run(assistant.generate_response(user_question, relevant_chunks))
        
        print("Response from system:")
        print("="*50)
        print(result['response'])
        print("="*50)
        print(f"Type: {result['type']}")
        print(f"Model used: {result.get('model_used', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_exact_system_conditions()