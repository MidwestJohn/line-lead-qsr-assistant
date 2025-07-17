#!/usr/bin/env python3
"""
Test Multi-Format File Upload
============================

Simple test to verify multi-format file upload is working correctly
"""

import requests
import os
from pathlib import Path

# Test different file types
test_files = [
    ("test.txt", "text/plain", "This is a test manual for equipment operation.\n\nStep 1: Turn on the equipment\nStep 2: Follow safety procedures\nStep 3: Monitor performance"),
    ("test.md", "text/markdown", "# Equipment Manual\n\n## Overview\nThis is a test manual\n\n## Steps\n1. Step one\n2. Step two"),
    ("test.csv", "text/csv", "Equipment,Model,Instructions\nFryer,F-100,Heat to 375F\nGrill,G-200,Preheat 10 minutes"),
]

def test_upload(filename, content_type, content):
    """Test upload for a specific file type"""
    
    # Create test file
    test_file_path = Path(f"/tmp/{filename}")
    test_file_path.write_text(content)
    
    url = "http://localhost:8000/upload-simple"
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': (filename, f, content_type)}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {filename}: Upload successful")
            print(f"   Process ID: {result.get('process_id')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ {filename}: Upload failed")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ {filename}: Error - {e}")
    
    finally:
        # Clean up test file
        test_file_path.unlink(missing_ok=True)

def main():
    print("Testing Multi-Format File Upload...")
    print("=" * 50)
    
    for filename, content_type, content in test_files:
        test_upload(filename, content_type, content)
        print()

if __name__ == "__main__":
    main()