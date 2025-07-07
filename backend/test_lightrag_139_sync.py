"""
Test LightRAG 1.3.9 with Synchronous Pattern
============================================

Test if the synchronous version works in 1.3.9.
"""

import os
from dotenv import load_dotenv
from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
import logging
from neo4j import GraphDatabase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_lightrag_139_sync():
    """Test LightRAG 1.3.9 with synchronous operations."""
    
    # Load environment from parent directory
    load_dotenv('../.env')
    
    # Set Neo4j environment variables
    os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI')
    os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', 'neo4j')
    os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD')
    
    logger.info("🧪 Testing LightRAG 1.3.9 with SYNCHRONOUS pattern...")
    
    # Get current Neo4j baseline
    baseline_nodes = get_neo4j_count()
    logger.info(f"📊 Baseline Neo4j nodes: {baseline_nodes}")
    
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
        # Create LightRAG instance with working pattern
        logger.info("🚀 Creating LightRAG 1.3.9 instance (SYNC)...")
        
        rag = LightRAG(
            working_dir="./rag_storage_139_sync",
            graph_storage="Neo4JStorage",
            
            # Basic LLM
            llm_model_func=gpt_4o_mini_complete,
            
            # Basic embedding
            embedding_func=EmbeddingFunc(
                embedding_dim=embedding_dim,
                max_token_size=8192,
                func=embedding_func,
            ),
            
            # Enhanced extraction parameters
            chunk_token_size=200,
            chunk_overlap_token_size=50,
            entity_extract_max_gleaning=2,
            summary_to_max_tokens=600,
        )
        
        logger.info("✅ LightRAG 1.3.9 instance created successfully!")
        
        # Test with QSR content
        test_content = """
        TAYLOR C602 SOFT SERVE FREEZER OPERATION MANUAL
        
        EQUIPMENT SPECIFICATIONS:
        - Model: C602 Soft Serve Freezer
        - Capacity: 5 gallons per hour
        - Operating Temperature: 18-22°F
        - Compressor: Copeland scroll compressor, 3 HP
        - Refrigerant: R-404A, 12 pounds
        - Electrical: 208-230V, 60Hz, 15 amps
        
        DAILY MAINTENANCE PROCEDURES:
        1. Sanitize mix inlet valve (Part #C602-MIV-001)
        2. Clean hopper with sanitizer solution at 200°F
        3. Check rubber gaskets for wear (Part #C602-GASKET-SET)
        4. Lubricate drive motor bearings every 30 days
        5. Inspect safety interlocks on control panel
        
        SAFETY WARNINGS:
        - Always disconnect power before servicing
        - Wear protective gloves when handling sanitizer
        - Use lockout/tagout procedures for electrical work
        - Maintain proper ventilation during cleaning
        
        TROUBLESHOOTING:
        - Low product temperature: Check refrigerant levels
        - Inconsistent texture: Inspect mix valve operation
        - High energy consumption: Clean condenser coils
        """
        
        logger.info(f"📄 Testing document processing with LightRAG 1.3.9 (SYNC)...")
        logger.info(f"📝 Content length: {len(test_content)} characters")
        
        # Test the SYNCHRONOUS insert operation
        result = rag.insert(test_content)
        
        # Check final node count
        final_nodes = get_neo4j_count()
        added_nodes = final_nodes - baseline_nodes
        
        logger.info(f"🎯 LIGHTRAG 1.3.9 SYNCHRONOUS TEST RESULTS:")
        logger.info(f"  • Baseline nodes: {baseline_nodes}")
        logger.info(f"  • Final nodes: {final_nodes}")
        logger.info(f"  • Added nodes: {added_nodes}")
        logger.info(f"  • Processing result: {result}")
        
        if added_nodes > 0:
            logger.info("🎉 LIGHTRAG 1.3.9 SYNCHRONOUS SUCCESS!")
            
            # Get entity breakdown
            entity_breakdown = get_entity_breakdown()
            logger.info(f"📊 Entity breakdown: {entity_breakdown}")
            
            return True
        else:
            logger.warning("⚠️ No nodes added - may need further investigation")
            return False
            
    except Exception as e:
        logger.error(f"❌ LightRAG 1.3.9 synchronous test failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def get_neo4j_count():
    """Get current Neo4j node count."""
    try:
        driver = GraphDatabase.driver(
            os.environ['NEO4J_URI'],
            auth=(os.environ['NEO4J_USERNAME'], os.environ['NEO4J_PASSWORD'])
        )
        
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
        
        driver.close()
        return count
        
    except Exception as e:
        logger.error(f"Failed to get Neo4j count: {e}")
        return 0

def get_entity_breakdown():
    """Get entity type breakdown from Neo4j."""
    try:
        driver = GraphDatabase.driver(
            os.environ['NEO4J_URI'],
            auth=(os.environ['NEO4J_USERNAME'], os.environ['NEO4J_PASSWORD'])
        )
        
        with driver.session() as session:
            result = session.run("""
                MATCH (n) 
                RETURN labels(n) as labels, count(n) as count 
                ORDER BY count DESC
            """)
            
            breakdown = {}
            for record in result:
                labels = record["labels"]
                count = record["count"]
                breakdown[str(labels)] = count
        
        driver.close()
        return breakdown
        
    except Exception as e:
        logger.error(f"Failed to get entity breakdown: {e}")
        return {}

if __name__ == "__main__":
    test_lightrag_139_sync()