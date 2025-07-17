#!/usr/bin/env python3
"""
Test Image Upload
=================

Test image file upload functionality
"""

import requests
import os
from pathlib import Path
from PIL import Image
import io

def create_test_image(filename, format_type):
    """Create a simple test image"""
    # Create a simple 100x100 image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format_type)
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_image_upload():
    """Test image upload"""
    
    # Test different image formats
    test_images = [
        ("test.jpg", "JPEG", "image/jpeg"),
        ("test.png", "PNG", "image/png"),
    ]
    
    url = "http://localhost:8000/upload-simple"
    
    for filename, format_type, content_type in test_images:
        try:
            # Create test image
            image_data = create_test_image(filename, format_type)
            
            files = {'file': (filename, image_data, content_type)}
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
        
        print()

if __name__ == "__main__":
    try:
        test_image_upload()
    except ImportError:
        print("PIL not available, skipping image test")
        print("Install with: pip install Pillow")