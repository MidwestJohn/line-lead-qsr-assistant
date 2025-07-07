"""
Synchronous Working Pattern Test
===============================

Test the synchronous version to avoid async issues.
"""

import os
from dotenv import load_dotenv
from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sync_working():
    """Test the synchronous working pattern."""
    
    # Load environment
    load_dotenv('../.env')
    
    # Check environment variables
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not neo4j_uri or not neo4j_password:
        logger.error("❌ NEO4J_URI and NEO4J_PASSWORD required")
        return False
    
    # Set environment variables
    os.environ['NEO4J_URI'] = neo4j_uri
    os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', 'neo4j')
    os.environ['NEO4J_PASSWORD'] = neo4j_password
    
    logger.info("🔧 Testing SYNCHRONOUS working pattern...")
    
    # Simple embedding function
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        embedding_func = lambda texts: model.encode(texts).tolist()
        
        # Test embedding
        test_embedding = embedding_func(["test"])
        embedding_dim = len(test_embedding[0])
        logger.info(f"📏 Embedding dimension: {embedding_dim}")
        
    except Exception as e:
        logger.error(f"❌ Embedding setup failed: {e}")
        return False
    
    try:
        # SYNCHRONOUS CONFIGURATION
        logger.info("🚀 Creating LightRAG with SYNCHRONOUS configuration...")
        
        rag = LightRAG(
            working_dir="./rag_storage_sync",
            graph_storage="Neo4JStorage",
            
            # Basic LLM (no enhancement)
            llm_model_func=gpt_4o_mini_complete,
            
            # Basic embedding
            embedding_func=EmbeddingFunc(
                embedding_dim=embedding_dim,
                max_token_size=8192,
                func=embedding_func,
            ),
        )
        
        logger.info("✅ LightRAG instance created!")
        
        # Test with minimal content
        test_content = "The Taylor C602 freezer has a temperature setting of 18°F."
        
        logger.info(f"📄 Testing with minimal content: {len(test_content)} chars")
        
        # SYNCHRONOUS INSERT
        result = rag.insert(test_content)
        
        logger.info("🎯 Synchronous working pattern SUCCESS!")
        logger.info(f"Result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Synchronous working pattern failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_sync_working()