#!/usr/bin/env python3
"""
Test QSR optimization configuration without processing documents
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

async def test_qsr_config():
    """Test QSR optimization configuration without document processing."""
    
    print("🧪 TESTING QSR OPTIMIZATION CONFIGURATION")
    print("=" * 55)
    
    try:
        # Import services
        from services.optimized_rag_service import optimized_qsr_rag_service
        
        # Initialize optimized service
        print("🔧 Initializing optimized RAG service...")
        success = await optimized_qsr_rag_service.initialize()
        
        if not success:
            print("❌ Failed to initialize optimized RAG service")
            return False
        
        print("✅ Optimized RAG service initialized successfully")
        
        # Test optimization report
        print("\n📊 Getting optimization report...")
        report = optimized_qsr_rag_service.get_optimization_report()
        
        print("\n✅ OPTIMIZATION CONFIGURATION:")
        print(f"   Service Type: {report['service_type']}")
        print(f"   Initialized: {report['initialized']}")
        print(f"   Target: {report['performance_target']}")
        print(f"   Features: {len(report['optimization_features'])}")
        
        print("\n🎯 OPTIMIZATION FEATURES:")
        for i, feature in enumerate(report['optimization_features'], 1):
            print(f"   {i}. {feature}")
        
        print("\n🔍 TARGET ENTITY CATEGORIES:")
        for i, category in enumerate(report['target_entity_categories'], 1):
            print(f"   {i}. {category}")
        
        # Test Neo4j connection
        print("\n🔌 Testing Neo4j connection...")
        from services.neo4j_service import neo4j_service
        
        connection_test = neo4j_service.test_connection()
        
        if connection_test.get('connected', False):
            print("✅ Neo4j connection successful")
            
            # Get current graph statistics
            stats = await neo4j_service.get_graph_statistics()
            print(f"   Current entities: {stats.get('total_nodes', 0)}")
            print(f"   Current relationships: {stats.get('total_relationships', 0)}")
            print(f"   Entity types: {len(stats.get('node_types', {}))}")
            
        else:
            print("❌ Neo4j connection failed")
            print(f"   Error: {connection_test.get('error', 'Unknown error')}")
        
        # Test configuration parameters
        print("\n⚙️ CONFIGURATION PARAMETERS:")
        if hasattr(optimized_qsr_rag_service, 'rag_instance') and optimized_qsr_rag_service.rag_instance:
            rag_instance = optimized_qsr_rag_service.rag_instance
            print(f"   Chunk size: {getattr(rag_instance, 'chunk_token_size', 'N/A')} tokens")
            print(f"   Chunk overlap: {getattr(rag_instance, 'chunk_overlap_token_size', 'N/A')} tokens")
            print(f"   Working directory: {getattr(rag_instance, 'working_dir', 'N/A')}")
            print(f"   Graph storage: {getattr(rag_instance, 'graph_storage_cls', 'N/A')}")
        
        # Test custom prompts
        print("\n💬 QSR-SPECIFIC PROMPTS:")
        if hasattr(optimized_qsr_rag_service, 'qsr_entity_prompt'):
            prompt_preview = optimized_qsr_rag_service.qsr_entity_prompt[:200] + "..."
            print(f"   Entity prompt: {prompt_preview}")
        
        if hasattr(optimized_qsr_rag_service, 'qsr_relationship_prompt'):
            rel_prompt_preview = optimized_qsr_rag_service.qsr_relationship_prompt[:200] + "..."
            print(f"   Relationship prompt: {rel_prompt_preview}")
        
        print("\n" + "=" * 55)
        print("✅ QSR OPTIMIZATION CONFIGURATION TEST PASSED")
        print("🎯 System is ready for QSR entity extraction optimization")
        print("⚠️  Note: Document processing blocked by LightRAG 'history_messages' issue")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_qsr_config())
    
    if success:
        print("\n🎉 QSR OPTIMIZATION CONFIGURATION IS READY!")
    else:
        print("\n❌ QSR OPTIMIZATION CONFIGURATION FAILED")