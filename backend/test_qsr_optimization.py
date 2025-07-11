#!/usr/bin/env python3
"""
Simple test script to verify QSR optimization is working
"""

import asyncio
import logging
from dotenv import load_dotenv
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('.env.rag')

async def test_qsr_optimization():
    """Test QSR optimization functionality."""
    
    print("🧪 TESTING QSR OPTIMIZATION")
    print("=" * 50)
    
    try:
        # Import services
        from services.optimized_rag_service import optimized_qsr_rag_service
        from services.neo4j_service import neo4j_service
        
        # Initialize optimized service
        print("🔧 Initializing optimized RAG service...")
        success = await optimized_qsr_rag_service.initialize()
        
        if not success:
            print("❌ Failed to initialize optimized RAG service")
            return False
        
        print("✅ Optimized RAG service initialized")
        
        # Test optimization report
        print("📊 Getting optimization report...")
        report = optimized_qsr_rag_service.get_optimization_report()
        
        print("✅ Optimization Configuration:")
        print(f"   Service Type: {report['service_type']}")
        print(f"   Initialized: {report['initialized']}")
        print(f"   Target: {report['performance_target']}")
        print(f"   Features: {len(report['optimization_features'])}")
        
        # Test with sample QSR content
        sample_content = """
        Taylor C714 Ice Cream Machine Manual
        
        Main Components:
        - Compressor unit (Model: COMP-714)
        - Mixing chamber (Part #: MIX-001)
        - Control panel (Display: LCD-714)
        - Dispensing valve (Part #: VALVE-001)
        
        Daily Cleaning Procedure:
        1. Turn off power switch
        2. Remove dispensing nozzle
        3. Clean with sanitizer solution
        4. Rinse thoroughly
        5. Reassemble components
        
        Safety Requirements:
        - Lockout/tagout before maintenance
        - Wear protective gloves
        - Use proper cleaning chemicals
        """
        
        print("🔄 Testing document processing...")
        
        # Get initial stats
        initial_stats = await neo4j_service.get_graph_statistics()
        print(f"Initial entities: {initial_stats.get('total_nodes', 0)}")
        
        # Process sample document
        result = await optimized_qsr_rag_service.process_document_optimized(
            sample_content, 
            "test_sample.txt"
        )
        
        print("✅ Document processed successfully")
        print(f"   Entities added: {result.get('entities_added', 0)}")
        print(f"   Total entities: {result.get('total_entities', 0)}")
        print(f"   Extraction passes: {result.get('extraction_passes', 0)}")
        
        # Test query optimization
        print("🔍 Testing query optimization...")
        
        query_result = await optimized_qsr_rag_service.query_optimized(
            "What are the main components of the Taylor C714?"
        )
        
        print("✅ Query executed successfully")
        print(f"   Result length: {len(query_result)} characters")
        print(f"   Sample: {query_result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_qsr_optimization())
    
    if success:
        print("\n✅ QSR OPTIMIZATION TEST PASSED")
    else:
        print("\n❌ QSR OPTIMIZATION TEST FAILED")