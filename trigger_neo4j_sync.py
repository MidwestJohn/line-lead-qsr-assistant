#!/usr/bin/env python3
"""
Trigger Neo4j sync for completed extractions to test the full pipeline
"""

import sys
import os
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')

import asyncio
from services.automatic_bridge_service import automatic_bridge_service

async def trigger_sync():
    print("🔄 Triggering Neo4j sync for extracted documents...")
    
    # Find temp extraction files
    import glob
    backend_dir = "/Users/johninniger/Workspace/line_lead_qsr_mvp/backend"
    temp_files = glob.glob(f"{backend_dir}/temp_extraction_*.json")
    
    print(f"Found {len(temp_files)} extraction files to process")
    
    for temp_file in temp_files[:2]:  # Process first 2 files
        print(f"\n📄 Processing: {os.path.basename(temp_file)}")
        
        try:
            # Extract process ID from filename
            filename = os.path.basename(temp_file)
            if "auto_proc_" in filename:
                process_id = filename.replace("temp_extraction_", "").replace(".json", "")
                print(f"Process ID: {process_id}")
                
                # Try to run the automatic bridge service
                result = await automatic_bridge_service.process_extracted_data(temp_file)
                
                if result:
                    print(f"✅ Successfully processed {filename}")
                else:
                    print(f"❌ Failed to process {filename}")
                    
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_sync())