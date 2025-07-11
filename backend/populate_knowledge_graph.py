#!/usr/bin/env python3
"""
Populate QSR Knowledge Graph with existing documents.
This script processes uploaded documents through the QSR Graph RAG service.
"""

import json
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import rag_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path='.env.rag')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Load documents into QSR Knowledge Graph with optimizations."""
    
    # Show optimization settings
    optimizations_enabled = os.getenv('RAG_ENABLE_OPTIMIZATIONS', 'true').lower() == 'true'
    batch_size = os.getenv('RAG_BATCH_SIZE', '20')
    chunk_size = os.getenv('RAG_CHUNK_SIZE', '1024')
    
    logger.info("=== QSR Knowledge Graph Population ===")
    logger.info(f"Optimizations enabled: {optimizations_enabled}")
    if optimizations_enabled:
        logger.info(f"Batch size: {batch_size}, Chunk size: {chunk_size}")
        logger.info("Expected speed improvement: 50-60%")
    
    # Initialize RAG service
    logger.info("Initializing QSR Graph RAG service...")
    success = await rag_service.initialize()
    
    if not success:
        logger.error("Failed to initialize RAG service")
        return
    
    # Load documents database
    documents_db_path = "../documents.json"
    if not os.path.exists(documents_db_path):
        logger.error(f"Documents database not found: {documents_db_path}")
        return
    
    with open(documents_db_path, 'r') as f:
        documents_db = json.load(f)
    
    logger.info(f"Found {len(documents_db)} documents to process")
    
    # OPTIMIZATION: Process all documents at once instead of one-by-one
    # This is much faster as it builds the knowledge graph in a single pass
    if optimizations_enabled and hasattr(rag_service, 'rag_instance') and rag_service.rag_instance:
        logger.info("Using optimized batch processing for all documents...")
        
        # Process all documents together
        success = rag_service.rag_instance.add_documents(documents_db)
        
        if success:
            logger.info("✅ Batch processing completed successfully!")
        else:
            logger.error("❌ Batch processing failed")
            return
    else:
        # Fallback: Process each document individually (slower)
        logger.info("Using individual document processing...")
        
        for doc_id, doc_info in documents_db.items():
            logger.info(f"Processing document: {doc_info.get('original_filename', 'unknown')}")
            
            # Get text content
            text_content = doc_info.get('text_content', '')
            if not text_content:
                logger.warning(f"No text content for document {doc_id}")
                continue
            
            # Create file path for processing
            file_path = f"../uploads/{doc_info.get('filename', f'{doc_id}.pdf')}"
            
            try:
                # Process through RAG service
                result = await rag_service.process_document(file_path, text_content)
                logger.info(f"Processed {doc_info.get('original_filename', 'unknown')}: {result}")
                
            except Exception as e:
                logger.error(f"Failed to process document {doc_id}: {e}")
    
    # Get statistics
    if hasattr(rag_service, 'rag_instance') and rag_service.rag_instance:
        stats = rag_service.rag_instance.get_statistics()
        logger.info("=== Knowledge Graph Statistics ===")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
    
    logger.info("🎉 Knowledge graph population complete!")

if __name__ == "__main__":
    asyncio.run(main())