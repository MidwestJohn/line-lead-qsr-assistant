#!/usr/bin/env python3
"""
Test clean intelligence service directly to isolate the issue
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_clean_intelligence_direct():
    """Test the clean intelligence service directly"""
    
    print("Testing clean intelligence service directly...")
    
    try:
        from services.enhanced_clean_intelligence_service import create_enhanced_clean_intelligence_service
        from services.ragie_service_clean import clean_ragie_service
        from services.multimodal_citation_service import MultiModalCitationService
        
        # Create the service
        service = await create_enhanced_clean_intelligence_service(
            ragie_service=clean_ragie_service,
            citation_service=MultiModalCitationService()
        )
        
        print(f"Service created: {service}")
        
        # Test the problematic query
        query = "The ice machine is not working"
        
        print(f"Processing query: {query}")
        
        # Test process_text_query method
        result = await service.process_text_query(query)
        
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_clean_intelligence_direct())