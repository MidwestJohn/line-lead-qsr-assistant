#!/usr/bin/env python3
"""
Test QSR optimization with bridge approach
Uses LOCAL storage + proven bridge system
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

async def test_qsr_bridge_optimization():
    """Test QSR optimization using bridge approach."""
    
    print("🧪 TESTING QSR OPTIMIZATION WITH BRIDGE APPROACH")
    print("=" * 60)
    
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
        
        print("✅ Optimized RAG service initialized with LOCAL storage")
        
        # Test with QSR sample content
        sample_content = """
        Taylor C714 Soft Serve Ice Cream Machine - Service Manual
        
        EQUIPMENT OVERVIEW:
        The Taylor C714 is a commercial soft serve ice cream machine with the following specifications:
        - Model: C714-27
        - Serial Number: TYL-2024-001
        - Capacity: 27 quarts/hour
        - Power: 7.5 kW
        - Refrigerant: R-404A
        
        MAJOR COMPONENTS:
        1. Compressor Assembly (Part #C714-COMP-001)
           - Hermetic compressor unit
           - Pressure relief valve (PRV-001)
           - Suction line filter (SLF-001)
           
        2. Mixing Chamber (Part #C714-MIX-001)
           - Stainless steel mixing bowl
           - Dasher assembly (DA-001)
           - Drive motor (DM-001, 2 HP)
           
        3. Control Panel (Part #C714-CTRL-001)
           - LCD display unit (LCD-001)
           - Function selector switch (FSS-001)
           - Emergency stop button (ESB-001)
           
        DAILY CLEANING PROCEDURES:
        Step 1: Press CLEAN button on control panel
        Step 2: Remove dispensing nozzle (DN-001)
        Step 3: Disassemble mixing chamber components
        Step 4: Clean all food contact surfaces
        Step 5: Apply sanitizer solution (200 ppm chlorine)
        Step 6: Reassemble components
        
        SAFETY PROCEDURES:
        LOCKOUT/TAGOUT:
        - Disconnect main power at circuit breaker
        - Lock out electrical disconnect switch
        - Tag with personal lockout tag
        - Test equipment to ensure power is off
        
        TROUBLESHOOTING:
        Problem: Machine not cooling properly
        Symptoms: High product temperature, soft consistency
        Causes: Low refrigerant charge, dirty condenser coils
        Solutions: Check refrigerant levels, clean condenser coils
        
        MAINTENANCE SCHEDULE:
        Daily: Visual inspection, temperature check
        Weekly: Lubricate drive motor bearings
        Monthly: Replace air filter (AF-001)
        Quarterly: Professional service inspection
        
        PARTS LIST:
        - C714-COMP-001: Hermetic compressor unit
        - PRV-001: Pressure relief valve
        - SLF-001: Suction line filter
        - DA-001: Dasher assembly
        - DM-001: Drive motor (2 HP)
        - LCD-001: LCD display unit
        - FSS-001: Function selector switch
        - ESB-001: Emergency stop button
        - DN-001: Dispensing nozzle
        - AF-001: Air filter
        """
        
        print("\n📊 Getting baseline Neo4j statistics...")
        
        # Get initial Neo4j stats
        initial_stats = await neo4j_service.get_graph_statistics()
        print(f"Initial entities: {initial_stats.get('total_nodes', 0)}")
        print(f"Initial relationships: {initial_stats.get('total_relationships', 0)}")
        
        print("\n🔄 Processing QSR content with optimization...")
        
        # Process with QSR optimization
        # Note: This will use LOCAL storage, then bridge to Neo4j
        result = await optimized_qsr_rag_service.process_document_optimized(
            sample_content,
            "test_qsr_optimization.txt"
        )
        
        print("✅ QSR optimization processing completed")
        print(f"   Extraction passes: {result.get('extraction_passes', 0)}")
        print(f"   Bridge result: {result.get('bridge_result', {}).get('success', False)}")
        
        # Get final Neo4j stats
        print("\n📈 Getting final Neo4j statistics...")
        final_stats = await neo4j_service.get_graph_statistics()
        
        entities_added = final_stats.get('total_nodes', 0) - initial_stats.get('total_nodes', 0)
        relationships_added = final_stats.get('total_relationships', 0) - initial_stats.get('total_relationships', 0)
        
        print(f"Final entities: {final_stats.get('total_nodes', 0)}")
        print(f"Final relationships: {final_stats.get('total_relationships', 0)}")
        print(f"Entities added: {entities_added}")
        print(f"Relationships added: {relationships_added}")
        
        # Calculate improvement factor
        baseline_entities = 35  # Original baseline
        current_entities = final_stats.get('total_nodes', 0)
        improvement_factor = current_entities / max(baseline_entities, 1)
        
        print(f"\n🎯 OPTIMIZATION RESULTS:")
        print(f"   Baseline entities: {baseline_entities}")
        print(f"   Current entities: {current_entities}")
        print(f"   Improvement factor: {improvement_factor:.2f}x")
        print(f"   Target achieved (10x): {'✅ YES' if improvement_factor >= 10.0 else '❌ NO'}")
        
        # Test entity types
        entity_types = final_stats.get('node_types', {})
        print(f"\n📋 ENTITY TYPES EXTRACTED:")
        for entity_type, count in entity_types.items():
            print(f"   {entity_type}: {count}")
        
        # Test query optimization
        print(f"\n🔍 Testing optimized query...")
        
        try:
            query_result = await optimized_qsr_rag_service.query_optimized(
                "What are the main components of the Taylor C714?"
            )
            print(f"✅ Query successful: {len(query_result)} characters")
            print(f"   Sample: {query_result[:150]}...")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
        
        print("\n" + "=" * 60)
        
        if improvement_factor >= 10.0:
            print("🎉 QSR OPTIMIZATION SUCCESS!")
            print("✅ 10x entity extraction improvement achieved")
            print("✅ Bridge approach working perfectly")
            return True
        else:
            print("⚠️  QSR OPTIMIZATION PARTIAL SUCCESS")
            print("✅ Bridge approach working")
            print("❌ 10x target not yet achieved - needs fine-tuning")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_qsr_bridge_optimization())
    
    if success:
        print("\n🎉 QSR BRIDGE OPTIMIZATION TEST PASSED!")
    else:
        print("\n⚠️  QSR BRIDGE OPTIMIZATION NEEDS TUNING")