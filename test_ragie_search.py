#!/usr/bin/env python3
"""
Test Ragie Search
=================

Test searching for content that should be in Ragie
"""

import requests
import json

def test_ragie_search():
    """Test searching for content in Ragie"""
    
    # Test different search queries
    test_queries = [
        "fryer operations",
        "kitchen equipment", 
        "training manual",
        "servers training",
        "equipment safety"
    ]
    
    base_url = "http://localhost:8000"
    
    for query in test_queries:
        print(f"\n🔍 Testing search: '{query}'")
        
        # Try the chat endpoint (which should use Ragie)
        try:
            chat_data = {
                "message": f"Tell me about {query}",
                "session_id": "test_session"
            }
            
            response = requests.post(f"{base_url}/chat", json=chat_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Chat response received")
                print(f"   Length: {len(result.get('response', ''))}")
                
                # Check if response contains relevant content
                response_text = result.get('response', '').lower()
                if 'equipment' in response_text or 'training' in response_text:
                    print(f"   ✅ Contains relevant content")
                else:
                    print(f"   ❌ No relevant content found")
                    
            else:
                print(f"❌ Chat request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing chat: {e}")
            
        # Try health check to see service status
        try:
            health_response = requests.get(f"{base_url}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                ragie_status = health_data.get('services', {}).get('ragie_enhancement', {}).get('status', 'unknown')
                print(f"   Ragie service status: {ragie_status}")
        except:
            pass

if __name__ == "__main__":
    test_ragie_search()