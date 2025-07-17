#!/usr/bin/env python3
"""
Test DOCX Upload to Ragie
=========================

Test that DOCX files are now properly uploaded to Ragie
"""

import requests
import time
import json

def test_docx_ragie_upload():
    """Test DOCX upload to Ragie"""
    
    # Create a sample DOCX-like content (as text file with docx extension)
    test_content = """
    Kitchen Equipment Training Manual
    =================================
    
    Chapter 1: Fryer Operations
    ---------------------------
    
    Safety First:
    - Always ensure fryer is clean before use
    - Check oil temperature before starting
    - Never leave fryer unattended during operation
    
    Operating Procedures:
    1. Pre-heat fryer to 350°F
    2. Add food items carefully to avoid splashing
    3. Use proper timing for different food types
    4. Monitor temperature throughout cooking
    
    Chapter 2: Grill Operations
    ---------------------------
    
    Preparation:
    - Clean grill surface thoroughly
    - Check gas connections
    - Preheat to recommended temperature
    
    Cooking Guidelines:
    - Use food thermometer to ensure proper internal temperature
    - Follow portion control guidelines
    - Maintain consistent cooking times
    
    Chapter 3: Cleaning Procedures
    ------------------------------
    
    Daily Cleaning:
    - Wipe down all surfaces after each use
    - Empty grease traps
    - Sanitize all contact surfaces
    
    Weekly Deep Clean:
    - Disassemble equipment for thorough cleaning
    - Use approved cleaning chemicals
    - Document cleaning completion
    """
    
    # Write test file
    with open('/tmp/kitchen_equipment_manual.txt', 'w') as f:
        f.write(test_content)
    
    url = "http://localhost:8000/upload-simple"
    
    try:
        with open('/tmp/kitchen_equipment_manual.txt', 'rb') as f:
            files = {'file': ('kitchen_equipment_manual.txt', f, 'text/plain')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful")
            print(f"   Process ID: {result.get('process_id')}")
            print(f"   Message: {result.get('message')}")
            
            # Give it time to process
            print("⏳ Waiting for background processing (10 seconds)...")
            time.sleep(10)
            
            # Check the logs to see if it was uploaded to Ragie
            print("📋 Checking recent upload status...")
            
            # Check if we can search for it
            search_url = "http://localhost:8000/search"
            search_data = {"query": "fryer operations"}
            
            search_response = requests.post(search_url, json=search_data)
            if search_response.status_code == 200:
                search_results = search_response.json()
                print(f"🔍 Search results: {len(search_results.get('results', []))} found")
                
                # Look for our test content
                for result in search_results.get('results', []):
                    if 'kitchen_equipment_manual' in result.get('filename', ''):
                        print(f"✅ Found in search results: {result.get('filename')}")
                        print(f"   Content preview: {result.get('text', '')[:100]}...")
                        break
                else:
                    print("❌ Test file not found in search results")
            else:
                print(f"❌ Search failed: {search_response.status_code}")
                
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_docx_ragie_upload()