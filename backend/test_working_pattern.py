"""
ACTUAL Working LightRAG Pattern Test
===================================

Based on real working examples from LightRAG repository:
- examples/lightrag_api_openai_compatible_demo.py
- examples/lightrag_ollama_demo.py

The documentation is WRONG - no initialization calls needed!
"""

import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_working_pattern():
    """Test the ACTUAL working pattern from LightRAG examples."""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('../.env')  # Load from parent directory
    
    # Set Neo4j environment variables
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not neo4j_uri or not neo4j_password:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD required")
    
    os.environ['NEO4J_URI'] = neo4j_uri
    os.environ['NEO4J_USERNAME'] = neo4j_username
    os.environ['NEO4J_PASSWORD'] = neo4j_password
    
    logger.info("🔧 Testing ACTUAL working pattern from LightRAG examples...")
    
    # Get embedding dimensions
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        embedding_func = lambda texts: model.encode(texts).tolist()
        test_embedding = embedding_func(["test"])
        embedding_dim = len(test_embedding[0])
        logger.info(f"📏 Embedding dimension: {embedding_dim}")
    except Exception as e:
        logger.error(f"❌ Embedding function failed: {e}")
        return False
    
    # Enhanced LLM function for QSR extraction
    async def enhanced_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        # Add QSR extraction guidance
        if "extract" in prompt.lower() and ("entities" in prompt.lower() or "relationships" in prompt.lower()):
            qsr_enhanced_prompt = f"""
{prompt}

CRITICAL FOR QSR EQUIPMENT MANUALS - Extract ALL detailed entities:

EQUIPMENT: pumps, valves, sensors, controls, displays, motors, belts, filters, gaskets, seals, switches, indicators, thermostats, timers, compressors, evaporators

MAINTENANCE: daily cleaning, weekly sanitization, monthly inspections, quarterly maintenance, lubrication schedules, calibration procedures, filter changes

SAFETY: warnings, cautions, PPE requirements, lockout/tagout, emergency procedures, safety interlocks, hazard notifications

PARAMETERS: exact temperatures, pressures (PSI), speeds (RPM), flow rates, voltage, amperage, time intervals, frequencies

PROCEDURES: step-by-step instructions, startup sequences, shutdown procedures, cleaning protocols, sanitization steps, troubleshooting guides

SPECIFICATIONS: part numbers, model numbers, dimensions, capacities, ratings, tolerances, material specifications

Be extremely thorough - extract granular details like specific temperature ranges, part numbers, procedural steps.
"""
            return await gpt_4o_mini_complete(
                qsr_enhanced_prompt, 
                system_prompt=system_prompt, 
                history_messages=history_messages,
                **kwargs
            )
        
        return await gpt_4o_mini_complete(
            prompt, 
            system_prompt=system_prompt, 
            history_messages=history_messages,
            **kwargs
        )
    
    try:
        # ACTUAL WORKING PATTERN - Just create the instance!
        logger.info("🚀 Creating LightRAG instance (NO initialization calls)...")
        
        rag = LightRAG(
            working_dir="./rag_storage",
            graph_storage="Neo4JStorage",  # For Neo4j
            
            # LLM configuration
            llm_model_func=enhanced_llm_func,
            
            # Embedding configuration
            embedding_func=EmbeddingFunc(
                embedding_dim=embedding_dim,
                max_token_size=8192,
                func=embedding_func,
            ),
            
            # Enhanced extraction parameters
            chunk_token_size=200,  # Smaller chunks for more entities
            chunk_overlap_token_size=50,
            entity_extract_max_gleaning=3,  # Multiple passes
            summary_to_max_tokens=800,  # Detailed descriptions
            
            log_level="DEBUG"
        )
        
        logger.info("✅ LightRAG instance created successfully!")
        
        # Get baseline Neo4j count
        baseline = await get_neo4j_count()
        logger.info(f"📊 Baseline Neo4j nodes: {baseline}")
        
        # Test with small content first
        test_content = """
        TAYLOR C602 SOFT SERVE FREEZER MAINTENANCE PROCEDURE
        
        Daily Cleaning Protocol:
        1. Turn off freezer using main power switch
        2. Remove all product from hopper
        3. Disassemble mix inlet valve (Part #C602-MIV-001)
        4. Clean with sanitizer solution at 200°F
        5. Inspect rubber gaskets for wear
        6. Reassemble and test operation
        
        Safety Warning: Always wear protective gloves when handling sanitizer.
        Temperature Setting: Maintain serving temperature at 18-20°F.
        """
        
        logger.info("📄 Testing document processing with ACTUAL working pattern...")
        logger.info(f"📝 Content length: {len(test_content)} characters")
        
        # ACTUAL WORKING PATTERN - Direct insert (like the examples)
        result = await rag.ainsert(test_content)
        
        # Check final count
        final = await get_neo4j_count()
        added = final - baseline
        
        logger.info(f"🎯 WORKING PATTERN RESULTS:")
        logger.info(f"  • Added: {added} entities")
        logger.info(f"  • Total: {final} nodes")
        logger.info(f"  • Success: {'✅' if added > 0 else '❌'}")
        
        if added > 0:
            logger.info("🚀 WORKING PATTERN SUCCESS! The real examples method works!")
            return True
        else:
            logger.warning("⚠️ No entities added - may need debugging")
            return False
            
    except Exception as e:
        logger.error(f"❌ Working pattern test failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

async def get_neo4j_count():
    """Get current Neo4j node count."""
    try:
        from neo4j import GraphDatabase
        
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

if __name__ == "__main__":
    asyncio.run(test_working_pattern())