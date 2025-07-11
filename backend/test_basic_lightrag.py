#!/usr/bin/env python3
"""
Basic LightRAG test to verify configuration
"""
import os
import asyncio
import threading
from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
from dotenv import load_dotenv

load_dotenv('.env.rag')

def get_embedding_function():
    """Get embedding function for LightRAG."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        return lambda texts: model.encode(texts).tolist()
    except ImportError:
        # Fallback to dummy embeddings for testing
        return lambda texts: [[0.1] * 1536 for _ in texts]

def test_lightrag_basic():
    """Test basic LightRAG functionality"""
    
    print("🧪 Testing Basic LightRAG Configuration")
    print("=" * 50)
    
    try:
        # Set Neo4j environment variables (REQUIRED by LightRAG)
        os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', 'neo4j')
        os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD')
        
        if not os.environ['NEO4J_PASSWORD']:
            print("❌ NEO4J_PASSWORD environment variable required")
            return False
        
        print("✅ Environment variables set")
        
        # Test 1: Create LightRAG with NetworkX (should work)
        print("Test 1: Creating LightRAG with NetworkX storage...")
        
        rag_networkx = LightRAG(
            working_dir="./rag_storage_networkx",
            graph_storage="NetworkXStorage",
            llm_model_func=gpt_4o_mini_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=get_embedding_function()
            )
        )
        print("✅ NetworkX LightRAG created successfully")
        
        # Test 2: Create LightRAG with Neo4j (may have issues)
        print("Test 2: Creating LightRAG with Neo4j storage...")
        
        try:
            rag_neo4j = LightRAG(
                working_dir="./rag_storage_neo4j",
                graph_storage="Neo4JStorage",
                llm_model_func=gpt_4o_mini_complete,
                embedding_func=EmbeddingFunc(
                    embedding_dim=1536,
                    max_token_size=8192,
                    func=get_embedding_function()
                )
            )
            print("✅ Neo4j LightRAG created successfully")
            
            # Test a simple document insert
            print("Test 3: Inserting simple document...")
            simple_doc = "The Taylor C602 is an ice cream machine used in restaurants."
            
            # Use synchronous method in a separate thread to avoid event loop issues
            def insert_document():
                return rag_neo4j.insert(simple_doc)
            
            # Run in thread to avoid event loop conflicts
            thread = threading.Thread(target=insert_document)
            thread.start()
            thread.join()
            
            print("✅ Document insert completed")
            
        except Exception as e:
            print(f"❌ Neo4j LightRAG failed: {e}")
            print("This might be due to version compatibility issues")
            return False
        
        print("\n" + "=" * 50)
        print("✅ Basic LightRAG tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Basic LightRAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_lightrag_basic()
    
    if success:
        print("\n✅ LightRAG configuration is working correctly.")
    else:
        print("\n❌ LightRAG configuration has issues.")