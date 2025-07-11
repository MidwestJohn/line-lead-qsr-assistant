#!/usr/bin/env python3
"""
Test Grote-Slicer Processing with Comprehensive Logging
=====================================================

Test the complete PDF→Neo4j pipeline for Grote-Slicer-Wear-Gauge-Toolkit-Instructions.pdf
with comprehensive logging enabled.

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_grote_slicer_processing():
    """Test the complete processing pipeline for Grote-Slicer PDF"""
    
    print("🚀 Testing Grote-Slicer PDF Processing with Comprehensive Logging")
    print("=" * 70)
    
    # Import required services
    from services.automatic_bridge_service import automatic_bridge_service
    from services.rag_service import rag_service
    from comprehensive_logging import (
        create_pipeline_logger,
        lightrag_logger,
        bridge_logger,
        neo4j_logger,
        error_tracker
    )
    
    # File details
    file_path = "/Users/johninniger/Workspace/line_lead_qsr_mvp/uploaded_docs/a2cfaf86-e1c3-46f7-a6ff-cba63d4c468c_Grote-Slicer-Wear-Gauge-Toolkit-Instructions.pdf"
    filename = "Grote-Slicer-Wear-Gauge-Toolkit-Instructions.pdf"
    process_id = "test_grote_slicer_processing"
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    file_size = Path(file_path).stat().st_size
    print(f"✅ Found file: {filename}")
    print(f"📏 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    # Create pipeline logger
    pipeline_logger = create_pipeline_logger("a2cfaf86-e1c3-46f7-a6ff-cba63d4c468c", filename)
    
    # Define progress callback
    async def progress_callback(progress_summary):
        print(f"📊 Progress: {progress_summary['stage']} ({progress_summary['progress_percent']:.1f}%)")
        print(f"   Current: {progress_summary['current_operation']}")
        if progress_summary.get('errors'):
            print(f"   ❌ Errors: {len(progress_summary['errors'])}")
    
    try:
        print("\n🔥 Starting Comprehensive Processing Pipeline...")
        print("-" * 50)
        
        # === CHECKPOINT 2: LightRAG Processing ===
        pipeline_logger.log_stage_start("lightrag_processing", {
            "file_path": file_path,
            "file_size": file_size
        })
        
        lightrag_logger.log_document_insertion_started(file_path, file_size)
        
        # Run the automatic processing
        result = await automatic_bridge_service.process_document_automatically(
            file_path=file_path,
            filename=filename,
            rag_service=rag_service,
            process_id=process_id,
            progress_callback=progress_callback
        )
        
        print("\n📊 Processing Results:")
        print("=" * 30)
        print(f"Success: {result['success']}")
        print(f"Entities extracted: {result.get('entities_extracted', 0)}")
        print(f"Relationships extracted: {result.get('relationships_extracted', 0)}")
        print(f"Entities bridged: {result.get('entities_bridged', 0)}")
        print(f"Relationships bridged: {result.get('relationships_bridged', 0)}")
        print(f"Processing time: {result.get('total_duration_seconds', 0):.2f} seconds")
        
        if result.get('errors'):
            print(f"❌ Errors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"   - {error}")
        
        return result['success']
        
    except Exception as e:
        print(f"💥 Error during processing: {e}")
        error_tracker.log_failure("test_processing", e, {
            "file_path": file_path,
            "filename": filename,
            "process_id": process_id
        })
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Change to backend directory
    os.chdir('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')
    
    # Run the test
    success = asyncio.run(test_grote_slicer_processing())
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Check Neo4j graph for extracted entities and relationships")
        print("2. Test queries against the populated graph")
        print("3. Verify comprehensive logging captured all checkpoints")
    else:
        print("\n⚠️  Processing failed - check logs for details")