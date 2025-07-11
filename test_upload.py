#!/usr/bin/env python3
"""
Test the simple upload system with a small file upload
"""

import requests
import os
from pathlib import Path

# Create a test PDF file
test_pdf_path = Path("test_equipment_manual.pdf")
if not test_pdf_path.exists():
    # Create a simple test file (not a real PDF, but will work for our test)
    with open(test_pdf_path, 'wb') as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Equipment Manual) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000225 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n319\n%%EOF")

# Test the upload
print("Testing upload to simple upload system...")
try:
    with open(test_pdf_path, 'rb') as f:
        files = {'file': ('test_equipment_manual.pdf', f, 'application/pdf')}
        response = requests.post('http://localhost:8000/upload-simple', files=files)
        print(f"Upload response status: {response.status_code}")
        print(f"Upload response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            process_id = result.get('process_id')  # Direct access, not nested
            print(f"Process ID: {process_id}")
            
            # Test progress tracking
            if process_id:
                import time
                for i in range(10):
                    time.sleep(1)
                    progress_response = requests.get(f'http://localhost:8000/progress/{process_id}')
                    print(f"Progress {i+1}: {progress_response.json()}")
                    if progress_response.json().get('progress', {}).get('progress_percent', 0) >= 100:
                        break
                        
except Exception as e:
    print(f"Upload test failed: {e}")
finally:
    # Clean up test file
    if test_pdf_path.exists():
        test_pdf_path.unlink()