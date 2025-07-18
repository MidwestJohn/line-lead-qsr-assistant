#!/usr/bin/env python3
"""Test to see what the backend health endpoint is actually returning"""

import requests
import json

def test_health_endpoint():
    """Test the backend health endpoint"""
    
    print("Testing backend health endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Check for search_ready
            if 'search_ready' in data:
                print(f"✅ search_ready: {data['search_ready']}")
            else:
                print("❌ search_ready field is missing!")
                
            # Check pydantic orchestration status
            pydantic_status = data.get('services', {}).get('pydantic_orchestration', {}).get('status')
            print(f"pydantic_orchestration status: {pydantic_status}")
            
            # Print full response for debugging
            print("\nFull response:")
            print(json.dumps(data, indent=2))
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_health_endpoint()