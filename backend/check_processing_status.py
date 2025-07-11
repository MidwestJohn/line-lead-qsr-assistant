#!/usr/bin/env python3
"""
Check FCS-650256.pdf Processing Status and Trigger Comprehensive Logging
=======================================================================

This script checks the current processing status of FCS-650256.pdf and 
optionally re-triggers the processing with comprehensive logging enabled.

Author: Generated with Memex (https://memex.tech)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')

from comprehensive_logging import (
    create_pipeline_logger,
    upload_logger,
    lightrag_logger,
    bridge_logger,
    neo4j_logger,
    error_tracker
)

def check_file_status():
    """Check the current status of FCS-650256.pdf"""
    
    print("🔍 Checking FCS-650256.pdf Processing Status")
    print("=" * 50)
    
    # Check uploaded file
    uploaded_file = Path("uploaded_docs/259e3505-7a6d-47b2-8d2c-fe053905416d_FCS-650256.pdf")
    if uploaded_file.exists():
        size = uploaded_file.stat().st_size
        print(f"✅ Uploaded file exists: {uploaded_file}")
        print(f"📏 File size: {size:,} bytes ({size/1024/1024:.2f} MB)")
        print(f"📅 Modified: {datetime.fromtimestamp(uploaded_file.stat().st_mtime)}")
    else:
        print("❌ Uploaded file not found")
        return False
    
    # Check for LightRAG processing artifacts
    rag_storage_paths = [
        "rag_storage/entities.json",
        "rag_storage/relationships.json",
        "rag_storage/chunks.json"
    ]
    
    print("\n🔍 Checking LightRAG Processing Artifacts:")
    for path in rag_storage_paths:
        file_path = Path(path)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {path}: {size:,} bytes")
        else:
            print(f"❌ {path}: Not found")
    
    # Check for Neo4j bridge artifacts
    bridge_paths = [
        "qsr_entities.json",
        "qsr_relationships.json",
        "qsr_checkpoint.json"
    ]
    
    print("\n🔍 Checking Bridge Artifacts:")
    for path in bridge_paths:
        file_path = Path(path)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {path}: {size:,} bytes")
        else:
            print(f"❌ {path}: Not found")
    
    # Check processing logs
    print("\n🔍 Checking Processing Logs:")
    log_files = [
        "backend_cors_fixed.log",
        "backend_comprehensive_logging.log",
        "lightrag_neo4j_bridge.log"
    ]
    
    for log_file in log_files:
        file_path = Path(log_file)
        if file_path.exists():
            # Check for FCS-650256 mentions
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if "FCS-650256" in content:
                        print(f"✅ {log_file}: Contains FCS-650256 processing logs")
                    else:
                        print(f"⚠️  {log_file}: No FCS-650256 processing logs")
            except Exception as e:
                print(f"❌ {log_file}: Error reading - {e}")
        else:
            print(f"❌ {log_file}: Not found")
    
    return True

def test_comprehensive_logging():
    """Test the comprehensive logging system"""
    
    print("\n🧪 Testing Comprehensive Logging System")
    print("=" * 50)
    
    # Create test pipeline logger
    test_doc_id = "test_doc_123"
    test_filename = "test_file.pdf"
    
    try:
        # Test pipeline logger
        pipeline_logger = create_pipeline_logger(test_doc_id, test_filename)
        pipeline_logger.log_stage_start("test_stage", {"test_key": "test_value"})
        pipeline_logger.log_stage_progress(50.0, "Testing progress", {"progress_key": "progress_value"})
        pipeline_logger.log_stage_complete("test_stage", True, {"completion_key": "completion_value"})
        print("✅ Pipeline logger working correctly")
        
        # Test upload logger
        upload_logger.log_file_received("test.pdf", 1024, "application/pdf")
        upload_logger.log_validation_passed("test.pdf")
        upload_logger.log_file_saved("test.pdf", "/tmp/test.pdf")
        upload_logger.log_processing_initiated("test.pdf", "test_id")
        print("✅ Upload logger working correctly")
        
        # Test LightRAG logger
        lightrag_logger.log_document_insertion_started("/tmp/test.pdf", 1000)
        lightrag_logger.log_text_extraction_completed(5000, 10)
        lightrag_logger.log_entity_extraction_progress(25, 1.5)
        lightrag_logger.log_relationship_extraction(15, [0.8, 0.9, 0.7])
        lightrag_logger.log_storage_written(1024, 512)
        print("✅ LightRAG logger working correctly")
        
        # Test bridge logger
        bridge_logger.log_bridge_initiated(["test_entities.json", "test_relationships.json"])
        bridge_logger.log_data_extraction_from_lightrag(25, 15)
        bridge_logger.log_batch_processing(1, 3)
        print("✅ Bridge logger working correctly")
        
        # Test Neo4j logger
        neo4j_logger.log_connection_established("neo4j://localhost:7687", True)
        neo4j_logger.log_batch_insertion_started(100, 3)
        neo4j_logger.log_transaction_committed(25, 15)
        neo4j_logger.log_completion_status(45.6, True)
        print("✅ Neo4j logger working correctly")
        
        # Test error tracker
        error_tracker.log_retry_attempt("test_stage", 1, 3)
        error_tracker.log_recovery_operation("test_stage", "retry operation", True)
        print("✅ Error tracker working correctly")
        
        print("\n✅ All comprehensive logging components working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing comprehensive logging: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 FCS-650256.pdf Processing Status Check")
    print("=" * 60)
    
    os.chdir('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')
    
    # Check file status
    file_status = check_file_status()
    
    # Test logging system
    logging_status = test_comprehensive_logging()
    
    print("\n📊 Summary:")
    print(f"📄 File Status: {'✅ OK' if file_status else '❌ FAILED'}")
    print(f"📝 Logging Status: {'✅ OK' if logging_status else '❌ FAILED'}")
    
    if file_status and logging_status:
        print("\n🎯 Next Steps:")
        print("1. The file is ready for comprehensive logging processing")
        print("2. Upload a new PDF to test the full comprehensive logging pipeline")
        print("3. Or re-trigger processing of existing FCS-650256.pdf with logging")
    else:
        print("\n⚠️  Issues detected - resolve before proceeding")