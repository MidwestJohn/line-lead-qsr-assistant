#!/usr/bin/env python3
"""
Test script to compare entity extraction performance:
Original LightRAG vs Optimized QSR LightRAG

Target: Demonstrate 10x improvement in entity extraction
"""

import asyncio
import os
import logging
from typing import Dict, List
from dotenv import load_dotenv
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('.env.rag')

# Sample QSR manual content for testing
SAMPLE_QSR_CONTENT = """
Taylor C714 Soft Serve Ice Cream Machine
Service Manual - Model C714-27

SECTION 1: EQUIPMENT OVERVIEW

The Taylor C714 is a high-volume soft serve ice cream machine designed for commercial QSR operations.
Key specifications:
- Model: C714-27
- Serial Number: TYL-2024-001
- Capacity: 27 quarts/hour
- Voltage: 208-240V, 3-phase
- Power: 7.5 kW
- Refrigerant: R-404A
- Weight: 485 lbs

MAJOR COMPONENTS:
1. Compressor Assembly (Part #C714-COMP-001)
   - Hermetic compressor unit
   - Pressure relief valve (PRV-001)
   - Suction line filter (SLF-001)
   - Discharge line (DL-001)

2. Evaporator System (Part #C714-EVAP-001)
   - Primary evaporator coil
   - Secondary evaporator coil
   - Expansion valve (EXV-001)
   - Temperature sensor (TS-001)

3. Mixing Chamber (Part #C714-MIX-001)
   - Stainless steel mixing bowl
   - Dasher assembly (DA-001)
   - Scraper blades (SB-001, SB-002)
   - Drive motor (DM-001, 2 HP)

4. Control Panel (Part #C714-CTRL-001)
   - LCD display unit (LCD-001)
   - Function selector switch (FSS-001)
   - Temperature control knob (TCK-001)
   - Emergency stop button (ESB-001)

5. Dispensing System (Part #C714-DISP-001)
   - Dispensing valve (DV-001)
   - Portion control mechanism (PCM-001)
   - Drip tray (DT-001)

SECTION 2: SAFETY PROCEDURES

LOCKOUT/TAGOUT PROCEDURES:
Step 1: Disconnect main power at circuit breaker
Step 2: Lock out electrical disconnect switch
Step 3: Tag with personal lockout tag
Step 4: Test equipment to ensure power is off
Step 5: Verify all energy sources are isolated

PERSONAL PROTECTIVE EQUIPMENT:
- Safety glasses required at all times
- Cut-resistant gloves for blade handling
- Non-slip footwear
- Hearing protection during operation

CHEMICAL SAFETY:
- Sanitizer solution: 200 ppm chlorine
- Cleaning chemical: Taylor C-9 cleaner
- Refrigerant handling: EPA certified technician only

SECTION 3: DAILY CLEANING PROCEDURES

DAILY SANITIZATION SEQUENCE:
Step 1: Press CLEAN button on control panel
Step 2: Remove dispensing nozzle (DN-001)
Step 3: Disassemble mixing chamber components
Step 4: Clean all food contact surfaces
Step 5: Rinse with potable water
Step 6: Apply sanitizer solution (200 ppm)
Step 7: Air dry for 2 minutes minimum
Step 8: Reassemble components in reverse order

WEEKLY DEEP CLEANING:
- Remove drive motor assembly
- Clean evaporator coils
- Inspect door seals and gaskets
- Lubricate dasher bearings
- Check refrigerant levels
- Test safety switches

SECTION 4: MAINTENANCE SCHEDULE

DAILY MAINTENANCE:
- Visual inspection of all components
- Check temperature readings
- Verify proper operation of all controls
- Clean exterior surfaces
- Empty and clean drip tray

WEEKLY MAINTENANCE:
- Lubricate drive motor bearings (Grease: NSF-H1)
- Check belt tension on drive system
- Inspect electrical connections
- Test emergency stop function
- Calibrate temperature sensors

MONTHLY MAINTENANCE:
- Replace air filter (AF-001)
- Check refrigerant pressure (High side: 280 PSI, Low side: 45 PSI)
- Inspect condenser coils
- Test defrost cycle operation
- Check door seal integrity

QUARTERLY MAINTENANCE:
- Professional service inspection
- Replace water filter (WF-001)
- Calibrate portion control system
- Test all safety systems
- Update maintenance log

SECTION 5: TROUBLESHOOTING

PROBLEM: Machine not cooling properly
SYMPTOMS: High product temperature, soft consistency
POSSIBLE CAUSES:
- Low refrigerant charge
- Dirty condenser coils
- Faulty expansion valve
- Blocked air filter
SOLUTIONS:
- Check refrigerant levels
- Clean condenser coils
- Replace expansion valve if faulty
- Replace air filter

PROBLEM: Dispensing valve not working
SYMPTOMS: No product dispensing, valve stuck
POSSIBLE CAUSES:
- Clogged dispensing nozzle
- Faulty portion control mechanism
- Electrical connection issue
SOLUTIONS:
- Clean dispensing nozzle thoroughly
- Inspect portion control mechanism
- Check electrical connections

PROBLEM: Excessive noise during operation
SYMPTOMS: Grinding, squealing, or rattling sounds
POSSIBLE CAUSES:
- Worn dasher bearings
- Loose drive belt
- Damaged scraper blades
SOLUTIONS:
- Replace dasher bearings
- Adjust belt tension
- Replace scraper blades

SECTION 6: TECHNICAL SPECIFICATIONS

ELECTRICAL REQUIREMENTS:
- Voltage: 208-240V ±10%
- Current: 32 Amps
- Frequency: 60 Hz
- Phase: 3-phase
- Wire: 4-wire plus ground

REFRIGERATION SPECIFICATIONS:
- Refrigerant: R-404A
- Charge: 6.2 lbs
- High pressure cutout: 400 PSI
- Low pressure cutout: 15 PSI
- Operating temperature: 18-22°F

PERFORMANCE SPECIFICATIONS:
- Production capacity: 27 quarts/hour
- Freezing time: 8-12 minutes
- Overrun: 40-60%
- Serving temperature: 18-22°F
- Mix temperature: 36-40°F

SECTION 7: PARTS LIST

COMPRESSOR ASSEMBLY PARTS:
- C714-COMP-001: Hermetic compressor unit
- PRV-001: Pressure relief valve
- SLF-001: Suction line filter
- DL-001: Discharge line
- CL-001: Compressor contactor
- OLP-001: Overload protector

EVAPORATOR SYSTEM PARTS:
- C714-EVAP-001: Primary evaporator coil
- C714-EVAP-002: Secondary evaporator coil
- EXV-001: Expansion valve
- TS-001: Temperature sensor
- TS-002: Backup temperature sensor
- DV-001: Defrost valve

MIXING CHAMBER PARTS:
- C714-MIX-001: Stainless steel mixing bowl
- DA-001: Dasher assembly
- SB-001: Primary scraper blade
- SB-002: Secondary scraper blade
- DM-001: Drive motor (2 HP)
- DB-001: Drive belt

CONTROL SYSTEM PARTS:
- C714-CTRL-001: Main control panel
- LCD-001: LCD display unit
- FSS-001: Function selector switch
- TCK-001: Temperature control knob
- ESB-001: Emergency stop button
- PCB-001: Main circuit board
"""

async def test_original_extraction():
    """Test extraction with original LightRAG configuration."""
    
    logger.info("🔍 Testing ORIGINAL LightRAG extraction...")
    
    try:
        from services.rag_service import rag_service
        
        # Initialize original service
        await rag_service.initialize()
        
        # Process sample content
        result = await rag_service.process_document(SAMPLE_QSR_CONTENT, "test_qsr_manual.txt")
        
        # Get extraction statistics
        from services.neo4j_service import neo4j_service
        stats = await neo4j_service.get_graph_statistics()
        
        original_results = {
            'service_type': 'Original LightRAG',
            'total_entities': stats.get('total_nodes', 0),
            'total_relationships': stats.get('total_relationships', 0),
            'entity_types': stats.get('node_types', {}),
            'processing_result': str(result)[:200] + "..."
        }
        
        logger.info(f"✅ Original extraction: {original_results['total_entities']} entities, {original_results['total_relationships']} relationships")
        
        return original_results
        
    except Exception as e:
        logger.error(f"❌ Original extraction test failed: {e}")
        return None

async def test_optimized_extraction():
    """Test extraction with optimized QSR LightRAG configuration."""
    
    logger.info("🚀 Testing OPTIMIZED QSR LightRAG extraction...")
    
    try:
        from services.optimized_rag_service import optimized_qsr_rag_service
        
        # Initialize optimized service
        await optimized_qsr_rag_service.initialize()
        
        # Process sample content with optimization
        result = await optimized_qsr_rag_service.process_document_optimized(
            SAMPLE_QSR_CONTENT, 
            "test_qsr_manual_optimized.txt"
        )
        
        optimized_results = {
            'service_type': 'Optimized QSR LightRAG',
            'total_entities': result.get('total_entities', 0),
            'total_relationships': result.get('total_relationships', 0),
            'entities_added': result.get('entities_added', 0),
            'relationships_added': result.get('relationships_added', 0),
            'extraction_passes': result.get('extraction_passes', 0),
            'optimization_features': optimized_qsr_rag_service.get_optimization_report()['optimization_features']
        }
        
        logger.info(f"✅ Optimized extraction: {optimized_results['total_entities']} entities, {optimized_results['total_relationships']} relationships")
        
        return optimized_results
        
    except Exception as e:
        logger.error(f"❌ Optimized extraction test failed: {e}")
        return None

async def compare_extraction_performance():
    """Compare extraction performance between original and optimized versions."""
    
    logger.info("📊 EXTRACTION PERFORMANCE COMPARISON")
    logger.info("=" * 60)
    
    # Test original extraction
    original_results = await test_original_extraction()
    
    # Clear graph for fair comparison
    logger.info("🧹 Clearing graph for fair comparison...")
    try:
        from services.neo4j_service import neo4j_service
        await neo4j_service.clear_graph()
        logger.info("✅ Graph cleared")
    except Exception as e:
        logger.warning(f"Could not clear graph: {e}")
    
    # Test optimized extraction
    optimized_results = await test_optimized_extraction()
    
    # Generate comparison report
    if original_results and optimized_results:
        
        improvement_factor = (
            optimized_results['total_entities'] / max(original_results['total_entities'], 1)
        )
        
        comparison_report = {
            'test_timestamp': asyncio.get_event_loop().time(),
            'test_content': 'QSR Manual Sample (Taylor C714)',
            'original_performance': original_results,
            'optimized_performance': optimized_results,
            'improvement_metrics': {
                'entity_improvement_factor': improvement_factor,
                'target_achieved': improvement_factor >= 10.0,
                'entities_gained': optimized_results['total_entities'] - original_results['total_entities'],
                'relationships_gained': optimized_results['total_relationships'] - original_results['total_relationships']
            },
            'optimization_summary': {
                'chunk_size_reduction': '1024 → 384 tokens',
                'overlap_increase': '25% overlap',
                'multi_pass_extraction': '3 passes',
                'qsr_specific_prompts': True,
                'preprocessing_stages': 2
            }
        }
        
        # Save comparison report
        with open('extraction_comparison_report.json', 'w') as f:
            json.dump(comparison_report, f, indent=2)
        
        # Print summary
        logger.info("\n📊 COMPARISON RESULTS:")
        logger.info(f"Original entities: {original_results['total_entities']}")
        logger.info(f"Optimized entities: {optimized_results['total_entities']}")
        logger.info(f"Improvement factor: {improvement_factor:.2f}x")
        logger.info(f"Target achieved (10x): {'✅ YES' if improvement_factor >= 10.0 else '❌ NO'}")
        
        if improvement_factor >= 10.0:
            logger.info("🎉 OPTIMIZATION SUCCESSFUL! 10x improvement achieved!")
        else:
            logger.info("⚠️ Target not reached, further optimization needed")
        
        return comparison_report
    
    else:
        logger.error("❌ Comparison failed - could not run both tests")
        return None

async def test_qsr_query_optimization():
    """Test QSR-specific query optimization."""
    
    logger.info("🔍 Testing QSR Query Optimization...")
    
    test_queries = [
        "What are the main components of the Taylor C714?",
        "How do I perform daily cleaning procedures?",
        "What should I do if the machine is not cooling properly?",
        "What are the safety requirements for maintenance?",
        "What refrigerant does the C714 use?"
    ]
    
    try:
        from services.optimized_rag_service import optimized_qsr_rag_service
        
        query_results = {}
        
        for query in test_queries:
            logger.info(f"Testing query: {query}")
            
            try:
                result = await optimized_qsr_rag_service.query_optimized(query)
                query_results[query] = {
                    'success': True,
                    'result': result[:300] + "..." if len(result) > 300 else result
                }
                logger.info(f"✅ Query successful: {len(result)} chars")
            
            except Exception as e:
                query_results[query] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"❌ Query failed: {e}")
        
        return query_results
        
    except Exception as e:
        logger.error(f"❌ Query optimization test failed: {e}")
        return None

async def main():
    """Main test function."""
    
    print("🧪 QSR ENTITY EXTRACTION OPTIMIZATION TEST")
    print("=" * 60)
    print("Target: Demonstrate 10x improvement (35 → 200+ entities)")
    print("=" * 60)
    
    try:
        # Run extraction performance comparison
        comparison_report = await compare_extraction_performance()
        
        if comparison_report:
            print("\n" + "=" * 60)
            print("📊 FINAL RESULTS:")
            print(f"Original: {comparison_report['original_performance']['total_entities']} entities")
            print(f"Optimized: {comparison_report['optimized_performance']['total_entities']} entities")
            print(f"Improvement: {comparison_report['improvement_metrics']['entity_improvement_factor']:.2f}x")
            print(f"Target Achieved: {'✅ YES' if comparison_report['improvement_metrics']['target_achieved'] else '❌ NO'}")
            
            # Test query optimization
            print("\n🔍 Testing Query Optimization...")
            query_results = await test_qsr_query_optimization()
            
            if query_results:
                successful_queries = sum(1 for r in query_results.values() if r['success'])
                print(f"Query success rate: {successful_queries}/{len(query_results)} queries")
            
            print("\n📄 Full report saved to: extraction_comparison_report.json")
            
            return comparison_report['improvement_metrics']['target_achieved']
        
        else:
            print("❌ Test failed - could not complete comparison")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 OPTIMIZATION TEST COMPLETED SUCCESSFULLY!")
        print("Target 10x improvement achieved!")
    else:
        print("\n⚠️ OPTIMIZATION NEEDS FURTHER TUNING")
        print("Review results and adjust configuration")