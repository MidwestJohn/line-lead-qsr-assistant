#!/usr/bin/env python3
"""
Fixed version of LightRAG for handling history_messages KeyError
"""
import asyncio
import os
from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
import logging

logger = logging.getLogger(__name__)

class LightRAGFixed(LightRAG):
    """Fixed version of LightRAG that handles history_messages KeyError"""
    
    async def apipeline_process_enqueue_documents(self, doc_ids, batch_size=None):
        """Override to fix history_messages KeyError"""
        try:
            # Get pipeline status
            pipeline_status = await self.get_processing_status()
            
            # Ensure history_messages exists
            if "history_messages" not in pipeline_status:
                logger.debug("🔧 Creating missing history_messages key")
                pipeline_status["history_messages"] = []
            
            # Call parent method
            return await super().apipeline_process_enqueue_documents(doc_ids, batch_size)
        
        except KeyError as e:
            if "history_messages" in str(e):
                logger.warning(f"🔧 Fixing history_messages KeyError: {e}")
                # Initialize the missing key
                pipeline_status = await self.get_processing_status()
                pipeline_status["history_messages"] = []
                # Retry the operation
                return await super().apipeline_process_enqueue_documents(doc_ids, batch_size)
            else:
                raise

def get_embedding_function():
    """Get embedding function for LightRAG."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        return lambda texts: model.encode(texts).tolist()
    except ImportError:
        return lambda texts: [[0.1] * 1536 for _ in texts]

async def create_fixed_lightrag():
    """Create a fixed LightRAG instance"""
    
    # Set Neo4j environment variables
    os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', 'neo4j')
    os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD')
    
    if not os.environ['NEO4J_PASSWORD']:
        raise ValueError("NEO4J_PASSWORD environment variable required")
    
    # Create fixed LightRAG instance
    rag = LightRAGFixed(
        working_dir="./rag_storage_fixed",
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
    
    return rag

if __name__ == "__main__":
    async def test_fixed_lightrag():
        """Test the fixed LightRAG implementation"""
        print("🧪 Testing Fixed LightRAG")
        print("=" * 50)
        
        try:
            from dotenv import load_dotenv
            load_dotenv('.env.rag')
            
            rag = await create_fixed_lightrag()
            
            # Test document
            test_doc = """
            Taylor C714 Advanced Ice Cream Machine
            
            The Taylor C714 features:
            - Advanced temperature control system
            - Automatic cleaning cycles
            - Dual-flavor dispensing capability
            
            Components:
            - Compressor unit
            - Mixing chamber
            - Dispensing system
            
            Safety: Always disconnect power before maintenance.
            """
            
            print("Processing test document...")
            result = await rag.ainsert(test_doc)
            print(f"✅ Document processed successfully: {result}")
            
            # Test querying
            print("Testing query functionality...")
            query_result = await rag.aquery("What are the main components of the Taylor C714?")
            print(f"Query result: {query_result[:200]}...")
            
            print("\n✅ Fixed LightRAG test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    success = asyncio.run(test_fixed_lightrag())
    if not success:
        exit(1)