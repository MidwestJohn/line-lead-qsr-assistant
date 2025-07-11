#!/usr/bin/env python3
"""
Debug script to inspect pipeline_status and understand the history_messages issue
"""
import asyncio
import os
import sys
import logging
from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('.env.rag')

def get_embedding_function():
    """Get embedding function for LightRAG."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        return lambda texts: model.encode(texts).tolist()
    except ImportError:
        return lambda texts: [[0.1] * 1536 for _ in texts]

# Monkey patch to debug the issue
original_apipeline_process_enqueue_documents = None

async def debug_apipeline_process_enqueue_documents(self, doc_ids):
    """Debug version of apipeline_process_enqueue_documents"""
    print(f"🔍 Debug: Called with doc_ids: {doc_ids}")
    
    # Check pipeline_status structure
    pipeline_status = self.get_processing_status()
    print(f"🔍 Debug: pipeline_status keys: {list(pipeline_status.keys())}")
    
    # Check if history_messages exists
    if "history_messages" in pipeline_status:
        print(f"🔍 Debug: history_messages exists: {pipeline_status['history_messages']}")
    else:
        print("🔍 Debug: history_messages NOT found, creating it...")
        pipeline_status["history_messages"] = []
    
    # Call original method
    return await original_apipeline_process_enqueue_documents(doc_ids)

async def main():
    """Main debug function"""
    
    print("🔍 Testing LightRAG Debug")
    print("=" * 50)
    
    try:
        # Set Neo4j environment variables
        os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', 'neo4j')
        os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD')
        
        if not os.environ['NEO4J_PASSWORD']:
            print("❌ NEO4J_PASSWORD environment variable required")
            return False
        
        # Create LightRAG instance
        rag = LightRAG(
            working_dir="./rag_storage_debug",
            graph_storage="Neo4JStorage",
            llm_model_func=gpt_4o_mini_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=get_embedding_function()
            ),
            chunk_token_size=256,
            chunk_overlap_token_size=64
        )
        
        # Initialize storages
        await rag.initialize_storages()
        
        # Check initial pipeline status
        pipeline_status = rag.get_processing_status()
        print(f"🔍 Initial pipeline_status: {pipeline_status}")
        
        # Monkey patch for debugging
        global original_apipeline_process_enqueue_documents
        original_apipeline_process_enqueue_documents = rag.apipeline_process_enqueue_documents
        rag.apipeline_process_enqueue_documents = debug_apipeline_process_enqueue_documents.__get__(rag, LightRAG)
        
        # Test document
        test_doc = "Simple test document about ice cream machine maintenance."
        
        print("Processing test document...")
        result = await rag.ainsert(test_doc)
        print(f"✅ Success: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Debug completed successfully!")
    else:
        print("\n❌ Debug failed.")
        sys.exit(1)