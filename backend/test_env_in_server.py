#!/usr/bin/env python3
"""
Test environment loading in server context
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path like in main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment like in main.py
print("Loading environment...")
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Check if API key is loaded
api_key = os.getenv('OPENAI_API_KEY')
print(f"API key loaded: {api_key is not None}")
if api_key:
    print(f"API key starts with: {api_key[:20]}...")
else:
    print("No API key found")

# Test PydanticAI agent creation in server context
try:
    from agents.qsr_base_agent import QSRBaseAgent
    print("Creating QSR Base Agent...")
    agent = QSRBaseAgent()
    print("✅ QSR Base Agent created successfully")
    
    # Test the agent
    from agents.qsr_base_agent import QSRContext
    from datetime import datetime
    
    context = QSRContext(
        conversation_id='test',
        user_location='restaurant',
        equipment_context={},
        safety_alerts=[],
        previous_queries=[]
    )
    
    print("Testing agent query...")
    import asyncio
    
    async def test_query():
        response = await agent.process_query(
            'What is the opening procedure for a QSR restaurant?',
            context
        )
        return response
    
    response = asyncio.run(test_query())
    print(f'✅ Query successful: {response.response[:100]}...')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()