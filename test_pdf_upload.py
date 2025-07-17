#!/usr/bin/env python3
"""
Test PDF Upload
===============

Test PDF file upload to ensure backward compatibility
"""

import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def create_test_pdf():
    """Create a simple test PDF"""
    buffer = io.BytesIO()
    
    # Create PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "Equipment Manual")
    p.drawString(100, 700, "Step 1: Turn on equipment")
    p.drawString(100, 650, "Step 2: Follow safety procedures")
    p.drawString(100, 600, "Step 3: Monitor performance")
    p.save()
    
    buffer.seek(0)
    return buffer.getvalue()

def test_pdf_upload():
    """Test PDF upload"""
    
    try:
        # Create test PDF
        pdf_data = create_test_pdf()
        
        url = "http://localhost:8000/upload-simple"
        files = {'file': ('test_equipment_manual.pdf', pdf_data, 'application/pdf')}
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF Upload successful")
            print(f"   Process ID: {result.get('process_id')}")
            print(f"   Message: {result.get('message')}")
        else:
            print("❌ PDF Upload failed")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ PDF Upload error: {e}")

if __name__ == "__main__":
    try:
        test_pdf_upload()
    except ImportError:
        print("reportlab not available, skipping PDF test")
        print("Install with: pip install reportlab")