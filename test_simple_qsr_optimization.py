#!/usr/bin/env python3
"""
Simple QSR optimization test without custom prompts
Focus on chunk size and overlap optimization
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from services.neo4j_service import neo4j_service
from lightrag import LightRAG
from lightrag.llm.openai import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample QSR content for testing
SAMPLE_QSR_CONTENT = """
TAYLOR C602 SOFT SERVE MACHINE OPERATION MANUAL

EQUIPMENT SPECIFICATIONS:
Model: Taylor C602
Capacity: 2 flavors plus twist
Hopper Size: 2.5 gallons each
Freezing Cylinder: 2.5 quarts
Condenser: Air-cooled
Electrical: 208-230V, 3-phase, 60Hz
Dimensions: 22" W x 28" D x 68" H
Weight: 340 lbs

SAFETY PROCEDURES:
1. Always wear safety glasses when cleaning
2. Disconnect power before maintenance
3. Use only food-grade lubricants
4. Check temperature settings daily
5. Maintain proper sanitation protocols

DAILY OPERATIONS:
1. Turn on machine at 6:00 AM
2. Check mix levels in hoppers
3. Verify freezing temperature: 18°F to 22°F
4. Test product consistency every 2 hours
5. Clean serving handles after each use

MAINTENANCE SCHEDULE:
Daily: Check mix levels, clean exterior
Weekly: Sanitize hoppers, check belts
Monthly: Replace filters, lubricate bearings
Quarterly: Deep clean freezing chambers
Annually: Professional inspection

TROUBLESHOOTING:
Problem: Machine won't start
Solution: Check power connection, reset circuit breaker
Problem: Product too soft
Solution: Adjust freezing temperature, check refrigeration
Problem: Unusual noise
Solution: Check belts, lubricate bearings, inspect motor

PARTS LIST:
Drive Belt: Part #X25-1234
Mix Valve: Part #X25-5678
Temperature Sensor: Part #X25-9012
Freezing Blade: Part #X25-3456
Hopper Lid: Part #X25-7890

INGREDIENTS:
Soft serve mix: 2.5 gallons per hopper
Sanitizer solution: 200 ppm chlorine
Lubricant: Food-grade bearing grease
Water: Filtered, 40-60 psi pressure
"""

def get_embedding_function():
    """Get embedding function for LightRAG."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        return lambda texts: model.encode(texts).tolist()
    except ImportError:
        logger.warning("SentenceTransformers not available, using OpenAI embeddings")
        return None

async def test_configuration(chunk_size, overlap, name):
    """Test a specific chunk size and overlap configuration."""
    try:
        logger.info(f"🧪 Testing {name} (chunk: {chunk_size}, overlap: {overlap})")
        
        # Clear previous data
        await clear_neo4j_data()
        
        # Set Neo4j environment variables
        os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', 'neo4j')
        os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD')
        
        # Create LightRAG instance
        rag_instance = LightRAG(
            working_dir=f"./rag_storage_test_{name.lower().replace(' ', '_')}",
            
            # Neo4j storage backend
            graph_storage="Neo4JStorage",
            
            # LLM configuration
            llm_model_func=gpt_4o_mini_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=get_embedding_function()
            ),
            
            # TEST PARAMETERS
            chunk_token_size=chunk_size,
            chunk_overlap_token_size=overlap,
            
            # Debugging
            log_level="DEBUG"
        )
        
        # Initialize storage
        await rag_instance.initialize_storages()
        
        # Enhanced content with entity hints
        enhanced_content = f"""
        QSR EQUIPMENT MANUAL - COMPREHENSIVE ENTITY EXTRACTION REQUIRED
        
        Extract all entities including:
        - Equipment names and models
        - All part numbers and specifications
        - Every procedure step
        - All safety requirements
        - Maintenance tasks and schedules
        - Troubleshooting problems and solutions
        - Temperature and time specifications
        - All ingredients and materials
        
        CONTENT:
        {SAMPLE_QSR_CONTENT}
        """
        
        # Process content
        start_time = time.time()
        result = await rag_instance.ainsert(enhanced_content)
        processing_time = time.time() - start_time
        
        # Get statistics
        stats = await get_neo4j_statistics()
        
        logger.info(f"✅ {name} completed in {processing_time:.2f}s")
        logger.info(f"📊 Entities: {stats.get('entities', 0)}")
        logger.info(f"📊 Relationships: {stats.get('relationships', 0)}")
        
        return {
            "name": name,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "entities": stats.get('entities', 0),
            "relationships": stats.get('relationships', 0),
            "processing_time": processing_time,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ {name} failed: {e}")
        return {"name": name, "error": str(e)}

async def get_neo4j_statistics():
    """Get Neo4j statistics."""
    try:
        if not neo4j_service.connected:
            neo4j_service.connect()
        
        with neo4j_service.driver.session() as session:
            # Count entities
            entity_result = session.run("MATCH (n) RETURN count(n) as entities")
            entities = entity_result.single()["entities"]
            
            # Count relationships
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as relationships")
            relationships = rel_result.single()["relationships"]
            
            return {
                "entities": entities,
                "relationships": relationships
            }
            
    except Exception as e:
        logger.error(f"Error getting Neo4j statistics: {e}")
        return {"entities": 0, "relationships": 0}

async def clear_neo4j_data():
    """Clear Neo4j data for clean testing."""
    try:
        if not neo4j_service.connected:
            neo4j_service.connect()
        
        with neo4j_service.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
    except Exception as e:
        logger.error(f"Error clearing Neo4j data: {e}")

async def main():
    """Main test function."""
    logger.info("🎯 QSR Chunk Size Optimization Test")
    logger.info("=" * 50)
    
    # Test different configurations
    test_configs = [
        (1024, 64, "Default LightRAG"),        # Default settings
        (512, 80, "Medium Chunks"),           # Medium chunks
        (256, 64, "Small Chunks"),            # Small chunks
        (400, 100, "Optimized QSR"),          # Optimized for QSR
        (200, 80, "Very Small Chunks"),       # Very small chunks
    ]
    
    results = []
    
    for chunk_size, overlap, name in test_configs:
        logger.info(f"\n📊 Testing: {name}")
        logger.info("-" * 40)
        
        result = await test_configuration(chunk_size, overlap, name)
        results.append(result)
        
        # Wait a bit between tests
        await asyncio.sleep(2)
    
    # Results summary
    logger.info("\n🏆 CHUNK SIZE OPTIMIZATION RESULTS")
    logger.info("=" * 50)
    
    successful_results = [r for r in results if "error" not in r]
    
    if successful_results:
        # Sort by entity count
        successful_results.sort(key=lambda x: x['entities'], reverse=True)
        
        for result in successful_results:
            logger.info(f"Configuration: {result['name']}")
            logger.info(f"  Chunk Size: {result['chunk_size']}")
            logger.info(f"  Overlap: {result['overlap']}")
            logger.info(f"  Entities: {result['entities']}")
            logger.info(f"  Relationships: {result['relationships']}")
            logger.info(f"  Processing Time: {result['processing_time']:.2f}s")
            
            # Calculate improvement vs baseline
            if result['entities'] > 0:
                improvement = result['entities'] / max(1, 35)  # vs baseline 35
                logger.info(f"  Improvement Factor: {improvement:.1f}x")
                
                if result['entities'] >= 200:
                    logger.info("  🎯 TARGET ACHIEVED: 200+ entities!")
                else:
                    logger.info(f"  📊 Progress: {result['entities']}/200 entities")
            logger.info("")
        
        # Best configuration
        best_result = successful_results[0]
        logger.info(f"🥇 BEST CONFIGURATION: {best_result['name']}")
        logger.info(f"   Chunk Size: {best_result['chunk_size']}")
        logger.info(f"   Overlap: {best_result['overlap']}")
        logger.info(f"   Entities: {best_result['entities']}")
        logger.info(f"   Relationships: {best_result['relationships']}")
        
    else:
        logger.error("❌ All configurations failed")
        for result in results:
            if "error" in result:
                logger.error(f"  {result['name']}: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())