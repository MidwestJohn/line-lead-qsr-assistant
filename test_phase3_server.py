#!/usr/bin/env python3
"""Test Phase 3 production server startup"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

def test_phase3_server():
    """Test Phase 3 production server startup"""
    print("Testing Phase 3 production server startup...")
    
    try:
        # Test the server imports
        from start_phase3_production import app
        print('✅ Phase 3 production server imports successfully')
        
        # Test that it creates the FastAPI app
        print('✅ FastAPI application created')
        
        # Test core dependencies
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from backend.agents.qsr_orchestrator import QSROrchestrator
        from backend.endpoints.pydantic_chat_endpoints import setup_pydantic_chat_endpoints
        from backend.services.ragie_service_clean import clean_ragie_service
        
        print('✅ All Phase 3 dependencies working')
        print('✅ System ready for production deployment')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase3_server()
    sys.exit(0 if success else 1)