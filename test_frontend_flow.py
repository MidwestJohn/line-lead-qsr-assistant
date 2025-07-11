#!/usr/bin/env python3
"""
Test the frontend flow to identify the issue
"""

import requests
import json

# Create a test PDF file
test_pdf_path = "test_equipment_manual.pdf"
with open(test_pdf_path, 'wb') as f:
    f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Equipment Manual) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000225 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n319\n%%EOF")

try:
    # Test upload exactly as frontend does
    print("Testing upload as frontend would...")
    with open(test_pdf_path, 'rb') as f:
        files = {'file': ('test_equipment_manual.pdf', f, 'application/pdf')}
        response = requests.post('http://localhost:8000/upload-simple', files=files)
        print(f"Upload response status: {response.status_code}")
        result = response.json()
        print(f"Upload response: {json.dumps(result, indent=2)}")
        
        # Simulate the frontend wrapper
        wrapped_result = {
            "success": True,
            "data": result,
            "response": f"<Response [{response.status_code}]>"
        }
        print(f"\nWrapped result (what frontend sees): {json.dumps(wrapped_result, indent=2)}")
        
        # Test the extraction
        process_id = wrapped_result.get('data', {}).get('process_id')
        print(f"\nExtracted process_id: {process_id}")
        
        if process_id:
            print("Process ID extraction would work!")
        else:
            print("Process ID extraction would fail!")
            
except Exception as e:
    print(f"Test failed: {e}")
finally:
    # Clean up
    import os
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)