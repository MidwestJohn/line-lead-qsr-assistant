#!/usr/bin/env python3
"""
Test the QSR Knowledge Graph functionality
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import rag_service

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path='.env.rag')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_knowledge_graph():
    """Test the knowledge graph functionality"""
    
    # Initialize RAG service
    logger.info("Initializing RAG service...")
    await rag_service.initialize()
    
    if not rag_service.initialized:
        logger.error("RAG service not initialized")
        return
    
    # Test queries
    test_queries = [
        "What is the Taylor C602?",
        "How do I clean the ice cream machine?",
        "What are the maintenance procedures?",
        "What safety requirements should I follow?",
        "Tell me about the heating element"
    ]
    
    for query in test_queries:
        logger.info(f"\n=== Testing query: {query} ===")
        
        try:
            # Test RAG search
            result = await rag_service.search(query)
            logger.info(f"RAG search result: {result}")
            
            # Test entity extraction
            entities = rag_service.rag_instance.extract_entities_from_query(query)
            logger.info(f"Extracted entities: {entities}")
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
    
    # Get statistics
    if rag_service.rag_instance:
        stats = rag_service.rag_instance.get_statistics()
        logger.info(f"\nKnowledge Graph Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_knowledge_graph())