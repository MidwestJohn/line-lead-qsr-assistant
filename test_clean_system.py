#!/usr/bin/env python3
"""Test clean system without RAG/Neo4j dependencies"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_clean_system():
    """Test that the clean system works without RAG/Neo4j"""
    print("Testing clean system without RAG/Neo4j dependencies...")
    
    try:
        from backend.agents.qsr_orchestrator import QSROrchestrator
        print('✅ QSR Orchestrator imports successfully')
        
        from backend.endpoints.pydantic_chat_endpoints import setup_pydantic_chat_endpoints
        print('✅ PydanticAI endpoints import successfully')
        
        from backend.services.ragie_service_clean import clean_ragie_service
        print('✅ Clean Ragie service imports successfully')
        
        # Test orchestrator initialization
        orchestrator = QSROrchestrator()
        print('✅ QSR Orchestrator creates successfully')
        
        print('✅ All clean system dependencies working')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_clean_system()
    sys.exit(0 if success else 1)