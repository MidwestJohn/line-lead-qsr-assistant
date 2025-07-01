#!/usr/bin/env python3

import os
import sys
sys.path.append('.')
from openai import OpenAI

def test_simple_system_prompt():
    """Test if system prompts work with minimal context - no RAG, no complexity"""
    
    # Use the API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found in environment")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Test 1: Your suggested 5-year-old test
    print("🧪 TEST 1: 5-year-old system prompt (proving system prompts work)")
    messages_test1 = [
        {
            "role": "system", 
            "content": "You are a 5-year-old child. Use only simple words. Never use big words. Talk like a kid in kindergarten. Say 'tummy' not 'stomach'. Say 'big' not 'large'. Be super simple."
        },
        {
            "role": "user",
            "content": "How do I fix a broken fryer in a restaurant?"
        }
    ]
    
    try:
        response1 = client.chat.completions.create(
            model="gpt-4",
            messages=messages_test1,
            temperature=0.2,
            max_tokens=300
        )
        print("Response 1:")
        print(response1.choices[0].message.content)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Simple restaurant worker prompt - NO RAG CONTEXT
    print("🧪 TEST 2: Simple restaurant worker prompt (no RAG context)")
    messages_test2 = [
        {
            "role": "system",
            "content": """CRITICAL: You MUST write like you're talking to a teenager at their first job.

BANNED WORDS (never use these):
- Strategic, implementation, optimize, framework
- Comprehensive, methodology, facilitate  
- Analysis, recommendations, roadmap

REQUIRED STYLE:
- Use "do" not "implement"
- Use "steps" not "procedures"
- Use "fix" not "troubleshoot" 
- Talk like a helpful 20-year-old coworker
- Be encouraging: "You can do this!"

If you use ANY banned words, you've failed.
Write like you're texting a friend, not writing a business report."""
        },
        {
            "role": "user",
            "content": "How do I clean a fryer?"
        }
    ]
    
    try:
        response2 = client.chat.completions.create(
            model="gpt-4",
            messages=messages_test2,
            temperature=0.2,
            max_tokens=300
        )
        print("Response 2:")
        print(response2.choices[0].message.content)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Same question but WITH document context (to see if RAG is the problem)
    print("🧪 TEST 3: Same prompt but WITH document context (testing RAG contamination)")
    rag_context = """MANUAL CONTEXT:
Source 1 - Preview-Line Cook Training Manual - QSR.pdf (relevance: 0.60):
Turn off the hoods and fryers and let cool down 30 or 40 minutes before cleaning. Fill a spray bottle with an approved degreaser and cover the fryers with trays to avoid oil contamination. Wear safety glasses to avoid eye injury when cleaning the hood."""
    
    messages_test3 = [
        {
            "role": "system",
            "content": """CRITICAL: You MUST write like you're talking to a teenager at their first job.

BANNED WORDS (never use these):
- Strategic, implementation, optimize, framework
- Comprehensive, methodology, facilitate  
- Analysis, recommendations, roadmap

REQUIRED STYLE:
- Use "do" not "implement"
- Use "steps" not "procedures"
- Use "fix" not "troubleshoot" 
- Talk like a helpful 20-year-old coworker
- Be encouraging: "You can do this!"

If you use ANY banned words, you've failed.
Write like you're texting a friend, not writing a business report."""
        },
        {
            "role": "user",
            "content": f"How do I clean a fryer?\n\n{rag_context}"
        }
    ]
    
    try:
        response3 = client.chat.completions.create(
            model="gpt-4",
            messages=messages_test3,
            temperature=0.2,
            max_tokens=300
        )
        print("Response 3:")
        print(response3.choices[0].message.content)
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")

if __name__ == "__main__":
    test_simple_system_prompt()