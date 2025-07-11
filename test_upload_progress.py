#!/usr/bin/env python3
"""
Test upload progress tracking to understand current pipeline visibility
"""

import requests
import time
import json

# Test uploading a small PDF file
def test_upload_progress():
    print("Testing upload progress tracking...")
    
    # Create a simple test file
    test_content = """# Test QSR Document
    
    This is a test document about ice cream machine maintenance.
    
    ## Equipment
    - Ice cream machine model XYZ
    - Cleaning supplies
    - Temperature sensors
    
    ## Procedures
    1. Daily cleaning protocol
    2. Temperature monitoring
    3. Maintenance scheduling
    """
    
    # Convert to PDF-like format (for simplicity, just upload as text)
    with open('/tmp/test_qsr_doc.txt', 'w') as f:
        f.write(test_content)
    
    # Upload the file
    try:
        with open('/tmp/test_qsr_doc.txt', 'rb') as f:
            files = {'file': ('test_qsr_doc.txt', f, 'text/plain')}
            response = requests.post(
                'http://localhost:8000/upload-simple',
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Upload successful!")
            print(f"Process ID: {result.get('process_id')}")
            
            # Track progress
            process_id = result.get('process_id')
            if process_id:
                print("\nTracking progress...")
                for i in range(20):  # Check for 20 seconds
                    try:
                        progress_response = requests.get(f'http://localhost:8000/progress/{process_id}')
                        if progress_response.status_code == 200:
                            progress = progress_response.json()
                            print(f"Stage: {progress.get('progress', {}).get('stage', 'unknown')}")
                            print(f"Progress: {progress.get('progress', {}).get('progress_percent', 0)}%")
                            print(f"Message: {progress.get('progress', {}).get('message', '')}")
                            
                            if progress.get('status') == 'completed':
                                print("✅ Processing completed!")
                                break
                        
                        time.sleep(2)
                    except Exception as e:
                        print(f"Error checking progress: {e}")
                        break
            
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload_progress()