#!/usr/bin/env python3

"""
Complete HTTP Fallback Test Script

This script tests the HTTP fallback system by:
1. Simulating a file upload that generates a process_id
2. Broadcasting progress updates via WebSocket
3. Testing HTTP fallback endpoint access during the process
4. Verifying the frontend can retrieve progress via HTTP when WebSocket fails
"""

import asyncio
import requests
import json
import time
import random
import string
from websocket_endpoints_robust import robust_websocket_manager

def generate_test_process_id():
    """Generate a realistic process ID similar to what the upload system creates."""
    timestamp = int(time.time())
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"auto_proc_{random_part}-test-{timestamp}"

async def simulate_upload_progress(process_id: str):
    """Simulate the upload progress that would be generated during file processing."""
    
    progress_stages = [
        {
            "stage": "upload_received",
            "progress_percent": 10,
            "message": f"File upload received for {process_id}",
            "entities_found": 0,
            "relationships_found": 0
        },
        {
            "stage": "text_extraction", 
            "progress_percent": 30,
            "message": "Extracting text content from document...",
            "entities_found": 0,
            "relationships_found": 0
        },
        {
            "stage": "entity_extraction",
            "progress_percent": 50,
            "message": "Extracting QSR entities and equipment data...",
            "entities_found": 12,
            "relationships_found": 0
        },
        {
            "stage": "relationship_generation",
            "progress_percent": 70,
            "message": "Generating semantic relationships...",
            "entities_found": 12,
            "relationships_found": 8
        },
        {
            "stage": "neo4j_storage",
            "progress_percent": 90,
            "message": "Storing data in knowledge graph...",
            "entities_found": 12,
            "relationships_found": 8
        },
        {
            "stage": "verification",
            "progress_percent": 100,
            "message": "Processing complete! Document successfully integrated.",
            "entities_found": 12,
            "relationships_found": 8
        }
    ]
    
    print(f"🚀 Starting progress simulation for {process_id}")
    
    for i, stage_data in enumerate(progress_stages):
        print(f"📊 Stage {i+1}/6: {stage_data['stage']} ({stage_data['progress_percent']}%)")
        
        # Add timestamp and process_id to the progress data
        progress_with_metadata = {
            **stage_data,
            "process_id": process_id,
            "timestamp": time.time()
        }
        
        # Store in the progress cache (simulating what the upload system would do)
        if process_id not in robust_websocket_manager.progress_cache:
            robust_websocket_manager.progress_cache[process_id] = []
        
        robust_websocket_manager.progress_cache[process_id].append(progress_with_metadata)
        
        # Simulate processing time
        await asyncio.sleep(2)
    
    print(f"✅ Progress simulation complete for {process_id}")

def test_http_fallback_endpoint(process_id: str):
    """Test the HTTP fallback endpoint during active processing."""
    
    print(f"\n🔄 Testing HTTP fallback endpoint for {process_id}")
    
    try:
        # Test the specific process endpoint
        response = requests.get(f"http://localhost:8000/ws/progress/{process_id}")
        print(f"📡 HTTP Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ HTTP Fallback Success!")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Fallback Mode: {data.get('fallback_mode')}")
            
            if data.get('success') and data.get('progress'):
                progress = data['progress']
                print(f"   - Stage: {progress.get('stage')}")
                print(f"   - Progress: {progress.get('progress_percent')}%")
                print(f"   - Message: {progress.get('message')}")
                print(f"   - Entities: {progress.get('entities_found')}")
                print(f"   - Relationships: {progress.get('relationships_found')}")
            else:
                print(f"   - Error: {data.get('error')}")
                
        else:
            print(f"❌ HTTP Request Failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ HTTP Fallback Test Failed: {e}")

def test_frontend_compatible_format(process_id: str):
    """Test that the HTTP response format matches what the frontend expects."""
    
    print(f"\n🎯 Testing frontend compatibility for {process_id}")
    
    try:
        response = requests.get(f"http://localhost:8000/ws/progress/{process_id}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields that frontend expects
            required_fields = ['success', 'process_id', 'fallback_mode']
            
            print("🔍 Checking required fields:")
            for field in required_fields:
                if field in data:
                    print(f"   ✅ {field}: {data[field]}")
                else:
                    print(f"   ❌ Missing: {field}")
            
            # If success=true, check progress fields
            if data.get('success') and data.get('progress'):
                progress = data['progress']
                progress_fields = ['stage', 'progress_percent', 'message', 'entities_found', 'relationships_found']
                
                print("🔍 Checking progress fields:")
                for field in progress_fields:
                    if field in progress:
                        print(f"   ✅ progress.{field}: {progress[field]}")
                    else:
                        print(f"   ❌ Missing: progress.{field}")
            
            print("✅ Frontend compatibility test complete")
            
        else:
            print(f"❌ HTTP request failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Frontend compatibility test failed: {e}")

async def run_complete_test():
    """Run the complete HTTP fallback test."""
    
    print("🧪 HTTP Fallback Complete Test")
    print("=" * 50)
    
    # Generate test process ID
    process_id = generate_test_process_id()
    print(f"🆔 Test Process ID: {process_id}")
    
    # Test 1: HTTP endpoint with non-existent process (should return success=false)
    print(f"\n📋 Test 1: Non-existent process")
    test_http_fallback_endpoint("non_existent_process_id")
    test_frontend_compatible_format("non_existent_process_id")
    
    # Test 2: Start progress simulation and test HTTP fallback during processing
    print(f"\n📋 Test 2: Active process monitoring")
    
    # Start the progress simulation in background
    progress_task = asyncio.create_task(simulate_upload_progress(process_id))
    
    # Test HTTP fallback at different stages
    for i in range(6):
        await asyncio.sleep(2.5)  # Wait a bit into each stage
        print(f"\n🔍 Testing during stage {i+1}:")
        test_http_fallback_endpoint(process_id)
        test_frontend_compatible_format(process_id)
    
    # Wait for progress simulation to complete
    await progress_task
    
    # Test 3: Final test after completion
    print(f"\n📋 Test 3: Completed process")
    test_http_fallback_endpoint(process_id)
    test_frontend_compatible_format(process_id)
    
    print(f"\n🎉 Complete HTTP fallback test finished!")
    print(f"📊 Process cache size: {len(robust_websocket_manager.progress_cache)}")
    
    # Clean up test data
    if process_id in robust_websocket_manager.progress_cache:
        del robust_websocket_manager.progress_cache[process_id]
        print(f"🧹 Cleaned up test data for {process_id}")

if __name__ == "__main__":
    print("🚀 Starting HTTP Fallback Complete Test")
    asyncio.run(run_complete_test())