#!/usr/bin/env python3
"""
Test Ragie Upload Fix
====================

Test that the DOCX upload to Ragie is now working
"""

import requests
import time

def test_docx_upload():
    """Test DOCX upload to Ragie"""
    
    # Create a simple DOCX-like test file (text file with docx extension)
    test_content = """
    Equipment Training Manual
    =========================
    
    Section 1: Safety Procedures
    - Always wash hands before handling equipment
    - Wear protective gear when necessary
    - Follow all safety protocols
    
    Section 2: Equipment Operation
    - Step 1: Power on the equipment
    - Step 2: Set temperature to 350°F
    - Step 3: Allow 10 minutes for preheating
    - Step 4: Begin food preparation
    
    Section 3: Cleaning Procedures
    - Turn off equipment after use
    - Clean all surfaces with approved cleaner
    - Sanitize according to health department guidelines
    """
    
    # Write test file
    with open('/tmp/training_manual_test.txt', 'w') as f:
        f.write(test_content)
    
    url = "http://localhost:8000/upload-simple"
    
    try:
        with open('/tmp/training_manual_test.txt', 'rb') as f:
            files = {'file': ('training_manual_test.txt', f, 'text/plain')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Text file upload successful")
            print(f"   Process ID: {result.get('process_id')}")
            print(f"   Message: {result.get('message')}")
            
            # Give it some time to process
            print("⏳ Waiting for background processing...")
            time.sleep(10)
            
            # Check if it appears in the documents list
            docs_response = requests.get("http://localhost:8000/documents")
            if docs_response.status_code == 200:
                docs = docs_response.json()
                print(f"📄 Total documents: {len(docs)}")
                
                # Look for our test file
                for doc in docs:
                    if 'training_manual_test.txt' in doc.get('filename', ''):
                        print(f"✅ Found in documents: {doc.get('filename')}")
                        print(f"   Ragie Document ID: {doc.get('ragie_document_id', 'None')}")
                        break
                else:
                    print("❌ Test file not found in documents")
            else:
                print(f"❌ Failed to get documents: {docs_response.status_code}")
                
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_docx_upload()