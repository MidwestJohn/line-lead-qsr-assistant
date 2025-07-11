#!/usr/bin/env python3
"""
Test Taylor C602 Manual Processing with Fixed Background Tasks
============================================================

Test the complete PDF→Neo4j pipeline for Taylor C602 manual using the 
Enterprise Bridge system with the background task fix applied.

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

async def test_taylor_c602_processing():
    """Test the complete processing pipeline for Taylor C602 manual"""
    
    print("🚀 Testing Taylor C602 Manual Processing with Background Task Fix")
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
    file_path = "/Users/johninniger/Workspace/line_lead_qsr_mvp/backend/uploaded_docs/0f028237-3119-413d-91d3-35b1d56ae596_Taylor_C602_Instruction_Manual.pdf"
    filename = "Taylor_C602_Instruction_Manual.pdf"
    process_id = "test_taylor_c602_processing"
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    file_size = Path(file_path).stat().st_size
    print(f"✅ Found file: {filename}")
    print(f"📏 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    print(f"📄 Expected: 102 pages with 150,543 characters")
    
    # Create pipeline logger
    pipeline_logger = create_pipeline_logger("0f028237-3119-413d-91d3-35b1d56ae596", filename)
    
    # Define progress callback
    async def progress_callback(progress_summary):
        print(f"📊 Progress: {progress_summary['stage']} ({progress_summary['progress_percent']:.1f}%)")
        print(f"   Current: {progress_summary['current_operation']}")
        if progress_summary.get('errors'):
            print(f"   ❌ Errors: {len(progress_summary['errors'])}")
    
    try:
        print("\n🔥 Starting Complete Processing Pipeline with Background Task Fix...")
        print("-" * 70)
        
        # === CHECKPOINT 2: LightRAG Processing ===
        pipeline_logger.log_stage_start("lightrag_processing", {
            "file_path": file_path,
            "file_size": file_size,
            "background_task_fix": "applied"
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
            "process_id": process_id,
            "background_task_fix": "applied"
        })
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Change to backend directory
    os.chdir('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')
    
    # Run the test
    success = asyncio.run(test_taylor_c602_processing())
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Check Neo4j graph for new entities and relationships from Taylor C602 manual")
        print("2. Compare with Grote Slicer manual results")
        print("3. Verify comprehensive logging captured all processing stages")
        print("4. Test upload of new documents to confirm background task fix")
    else:
        print("\n⚠️  Processing failed - check logs for details")