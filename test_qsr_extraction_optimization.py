#!/usr/bin/env python3
"""
Test script to compare original vs optimized QSR entity extraction
Goal: Achieve 200+ entities vs current 35 entities (10x improvement)
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from services.rag_service import rag_service
from services.optimized_qsr_rag_service import optimized_qsr_rag_service
from services.neo4j_service import neo4j_service
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

async def test_original_extraction():
    """Test original LightRAG extraction."""
    try:
        logger.info("🧪 Testing ORIGINAL LightRAG extraction...")
        
        # Initialize original service
        await rag_service.initialize()
        
        # Process content
        start_time = time.time()
        result = await rag_service.process_document(SAMPLE_QSR_CONTENT, "test_qsr_manual.pdf")
        processing_time = time.time() - start_time
        
        # Get statistics
        stats = await get_neo4j_statistics()
        
        logger.info(f"✅ Original extraction completed in {processing_time:.2f}s")
        logger.info(f"📊 Entities: {stats.get('entities', 0)}")
        logger.info(f"📊 Relationships: {stats.get('relationships', 0)}")
        
        return {
            "method": "original",
            "entities": stats.get('entities', 0),
            "relationships": stats.get('relationships', 0),
            "processing_time": processing_time,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Original extraction failed: {e}")
        return {"method": "original", "error": str(e)}

async def test_optimized_single_pass():
    """Test optimized single-pass extraction."""
    try:
        logger.info("🧪 Testing OPTIMIZED single-pass extraction...")
        
        # Clear previous data
        await clear_neo4j_data()
        
        # Initialize optimized service
        await optimized_qsr_rag_service.initialize()
        
        # Process content
        start_time = time.time()
        result = await optimized_qsr_rag_service.process_document_single_pass(SAMPLE_QSR_CONTENT, "test_qsr_manual.pdf")
        processing_time = time.time() - start_time
        
        # Get statistics
        stats = await get_neo4j_statistics()
        
        logger.info(f"✅ Optimized single-pass extraction completed in {processing_time:.2f}s")
        logger.info(f"📊 Entities: {stats.get('entities', 0)}")
        logger.info(f"📊 Relationships: {stats.get('relationships', 0)}")
        
        return {
            "method": "optimized_single",
            "entities": stats.get('entities', 0),
            "relationships": stats.get('relationships', 0),
            "processing_time": processing_time,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Optimized single-pass extraction failed: {e}")
        return {"method": "optimized_single", "error": str(e)}

async def test_optimized_multipass():
    """Test optimized multi-pass extraction."""
    try:
        logger.info("🧪 Testing OPTIMIZED multi-pass extraction...")
        
        # Clear previous data
        await clear_neo4j_data()
        
        # Initialize optimized service
        await optimized_qsr_rag_service.initialize()
        
        # Process content
        start_time = time.time()
        result = await optimized_qsr_rag_service.process_document_multipass(SAMPLE_QSR_CONTENT, "test_qsr_manual.pdf")
        processing_time = time.time() - start_time
        
        # Get statistics
        stats = await get_neo4j_statistics()
        
        logger.info(f"✅ Optimized multi-pass extraction completed in {processing_time:.2f}s")
        logger.info(f"📊 Entities: {stats.get('entities', 0)}")
        logger.info(f"📊 Relationships: {stats.get('relationships', 0)}")
        
        return {
            "method": "optimized_multipass",
            "entities": stats.get('entities', 0),
            "relationships": stats.get('relationships', 0),
            "processing_time": processing_time,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Optimized multi-pass extraction failed: {e}")
        return {"method": "optimized_multipass", "error": str(e)}

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
            logger.info("🧹 Cleared Neo4j data")
            
    except Exception as e:
        logger.error(f"Error clearing Neo4j data: {e}")

async def main():
    """Main test function."""
    logger.info("🎯 QSR Entity Extraction Optimization Test")
    logger.info("=" * 50)
    
    results = []
    
    # Test 1: Original extraction
    logger.info("\n📊 TEST 1: Original LightRAG Extraction")
    logger.info("-" * 40)
    result1 = await test_original_extraction()
    results.append(result1)
    
    # Test 2: Optimized single-pass
    logger.info("\n📊 TEST 2: Optimized Single-Pass Extraction")
    logger.info("-" * 40)
    result2 = await test_optimized_single_pass()
    results.append(result2)
    
    # Test 3: Optimized multi-pass
    logger.info("\n📊 TEST 3: Optimized Multi-Pass Extraction")
    logger.info("-" * 40)
    result3 = await test_optimized_multipass()
    results.append(result3)
    
    # Results summary
    logger.info("\n🏆 EXTRACTION OPTIMIZATION RESULTS")
    logger.info("=" * 50)
    
    for result in results:
        if "error" not in result:
            logger.info(f"Method: {result['method']}")
            logger.info(f"  Entities: {result['entities']}")
            logger.info(f"  Relationships: {result['relationships']}")
            logger.info(f"  Processing Time: {result['processing_time']:.2f}s")
            
            # Calculate improvement
            if result['entities'] > 0:
                improvement = result['entities'] / max(1, 35)  # vs baseline 35
                logger.info(f"  Improvement Factor: {improvement:.1f}x")
                
                if result['entities'] >= 200:
                    logger.info("  🎯 TARGET ACHIEVED: 200+ entities!")
                else:
                    logger.info(f"  📊 Progress: {result['entities']}/200 entities")
            
            logger.info("")
        else:
            logger.error(f"Method: {result['method']} - ERROR: {result['error']}")
    
    # Find best method
    successful_results = [r for r in results if "error" not in r]
    if successful_results:
        best_result = max(successful_results, key=lambda x: x['entities'])
        logger.info(f"🥇 BEST METHOD: {best_result['method']}")
        logger.info(f"   Entities: {best_result['entities']}")
        logger.info(f"   Relationships: {best_result['relationships']}")
        
        if best_result['entities'] >= 200:
            logger.info("✅ OPTIMIZATION GOAL ACHIEVED!")
        else:
            logger.info("⚠️  Further optimization needed")

if __name__ == "__main__":
    asyncio.run(main())