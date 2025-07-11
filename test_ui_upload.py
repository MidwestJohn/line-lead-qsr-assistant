#!/usr/bin/env python3
"""
Test upload through the UI simulation
"""

import requests
import json
import time

# Create a test PDF file
test_pdf_path = "test_ui_manual.pdf"
with open(test_pdf_path, 'wb') as f:
    f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 55 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(QSR Equipment Manual - Test) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000225 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n330\n%%EOF")

try:
    # 1. Upload file
    print("1. Uploading file...")
    with open(test_pdf_path, 'rb') as f:
        files = {'file': ('test_ui_manual.pdf', f, 'application/pdf')}
        response = requests.post('http://localhost:8000/upload-simple', files=files)
        
        if response.status_code == 200:
            result = response.json()
            process_id = result.get('process_id')
            print(f"✅ Upload successful. Process ID: {process_id}")
            
            # 2. Monitor progress
            print("\n2. Monitoring progress...")
            last_stage = None
            while True:
                progress_response = requests.get(f'http://localhost:8000/progress/{process_id}')
                if progress_response.status_code == 200:
                    progress = progress_response.json()
                    current_stage = progress.get('progress', {}).get('stage', 'unknown')
                    progress_percent = progress.get('progress', {}).get('progress_percent', 0)
                    message = progress.get('progress', {}).get('message', '')
                    
                    if current_stage != last_stage:
                        print(f"📊 Stage: {current_stage} ({progress_percent}%) - {message}")
                        last_stage = current_stage
                    
                    if progress_percent >= 100 and current_stage == 'verification':
                        print("✅ Processing complete!")
                        break
                        
                time.sleep(1)
            
            # 3. Check if file appears in document list
            print("\n3. Checking document list...")
            docs_response = requests.get('http://localhost:8000/documents')
            if docs_response.status_code == 200:
                docs = docs_response.json()
                print(f"📄 Total documents: {docs.get('total_count', 0)}")
                
                # Look for our uploaded file
                found = False
                for doc in docs.get('documents', []):
                    if 'test_ui_manual.pdf' in doc.get('filename', ''):
                        print(f"✅ Found uploaded file: {doc.get('filename')}")
                        found = True
                        break
                
                if not found:
                    print("❌ Uploaded file not found in document list")
                    print("Available documents:")
                    for doc in docs.get('documents', []):
                        print(f"  - {doc.get('filename', 'unknown')}")
            else:
                print("❌ Failed to fetch documents")
                
        else:
            print(f"❌ Upload failed: {response.status_code}")
            
except Exception as e:
    print(f"Test failed: {e}")
finally:
    # Clean up
    import os
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)