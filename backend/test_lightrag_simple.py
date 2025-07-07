#!/usr/bin/env python3
"""
Simple test to verify LightRAG processing works independently
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
logging.basicConfig(level=logging.INFO)
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
        # Fallback to dummy embeddings
        return lambda texts: [[0.1] * 1536 for _ in texts]

async def main():
    """Main test function"""
    
    print("🧪 Testing LightRAG Processing (Independent)")
    print("=" * 50)
    
    try:
        # Set Neo4j environment variables
        os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', 'neo4j')
        os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD')
        
        if not os.environ['NEO4J_PASSWORD']:
            print("❌ NEO4J_PASSWORD environment variable required")
            return False
        
        print("✅ Environment variables set")
        
        # Create LightRAG instance
        print("Creating LightRAG instance...")
        
        rag = LightRAG(
            working_dir="./rag_storage_test",
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
        
        print("✅ LightRAG instance created")
        
        # CORRECT INITIALIZATION SEQUENCE (FIXED):
        print("Initializing LightRAG storages...")
        
        # Step 1: Initialize storages
        await rag.initialize_storages()
        
        print("✅ LightRAG properly initialized")
        
        # Test document
        test_doc = """
        Taylor C714 Advanced Ice Cream Machine
        
        The Taylor C714 is a next-generation soft-serve ice cream machine designed for high-volume commercial operations.
        
        Key Features:
        - Advanced temperature control system
        - Automatic cleaning cycles
        - Dual-flavor dispensing capability
        - Stainless steel construction
        
        Main Components:
        - Compressor unit (primary cooling)
        - Mixing chamber (ingredient blending)
        - Dispensing system (product delivery)
        - Control panel (user interface)
        
        Safety Requirements:
        - Always disconnect power before maintenance
        - Use proper lockout/tagout procedures
        - Ensure all personnel are trained on safety protocols
        - Monthly safety inspections required
        
        Cleaning Procedures:
        - Daily sanitization of all food contact surfaces
        - Weekly deep cleaning of internal components
        - Monthly inspection of seals and gaskets
        - Quarterly professional service
        """
        
        print("Processing test document...")
        
        # Process the document
        result = await rag.ainsert(test_doc)
        
        print(f"✅ Document processed successfully: {result}")
        
        # Test querying
        print("Testing query functionality...")
        
        query_result = await rag.aquery("What are the main components of the Taylor C714?")
        print(f"Query result: {query_result[:200]}...")
        
        print("\n" + "=" * 50)
        print("🎉 LightRAG processing test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n✅ LightRAG processing is working correctly!")
    else:
        print("\n❌ LightRAG processing has issues.")
        sys.exit(1)