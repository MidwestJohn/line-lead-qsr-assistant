#!/usr/bin/env python3

import sys
import os
sys.path.append('.')
from openai_integration import QSRAssistant

def test_system_prompt():
    print("Testing OpenAI integration directly...")
    
    assistant = QSRAssistant()
    print(f"Model: {assistant.model}")
    print(f"Temperature: {assistant.temperature}")
    print(f"Available: {assistant.is_available()}")
    print(f"Demo mode: {assistant.demo_mode}")
    
    print("\nSystem prompt first 200 characters:")
    prompt = assistant.create_system_prompt()
    print(prompt[:200])
    
    print("\nLooking for forbidden words in system prompt:")
    forbidden = ["Strategic Recommendations", "Implementation Roadmap", "Current State Analysis"]
    for word in forbidden:
        if word in prompt:
            print(f"❌ Found forbidden: {word}")
        else:
            print(f"✅ Correctly excluded: {word}")

if __name__ == "__main__":
    test_system_prompt()