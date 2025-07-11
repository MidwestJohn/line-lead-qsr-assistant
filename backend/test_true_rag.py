#!/usr/bin/env python3
"""
Test the true RAG-Anything service with a simple document
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.true_rag_service import true_rag_service

async def test_simple_processing():
    """Test RAG-Anything with a simple document."""
    
    print("=== Testing True RAG-Anything Service ===")
    
    # Initialize service
    success = await true_rag_service.initialize()
    print(f"Initialization: {'✅ Success' if success else '❌ Failed'}")
    
    if not success:
        print("Cannot proceed without initialization")
        return
    
    # Create a test document
    test_content = """
    The Taylor C602 ice cream machine requires daily cleaning procedures.
    The machine contains a compressor that requires maintenance.
    Safety warnings apply to the mix pump operation.
    """
    
    test_file = "/tmp/taylor_test.txt"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"Created test file: {test_file}")
    
    try:
        # Process the document
        print("Processing document with RAG-Anything...")
        result = await true_rag_service.process_document(test_file, test_content)
        print(f"Processing result: {result}")
        
        # Test search
        print("Testing search capabilities...")
        search_result = await true_rag_service.search("What cleaning procedures are required for Taylor C602?")
        print(f"Search result: {search_result}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.unlink(test_file)

if __name__ == "__main__":
    asyncio.run(test_simple_processing())