#!/usr/bin/env python3
"""
Simple test to verify the frontend API call flow
"""
import requests
import json

def test_frontend_api_flow():
    """Test that the frontend API service gets the data correctly"""
    print("🔍 Testing frontend API data flow...")
    
    # Test the exact same call the frontend would make
    try:
        response = requests.post(
            "http://localhost:8000/chat/stream",
            headers={"Content-Type": "application/json"},
            json={"message": "Show me an image of Pizza Canotto"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API Response received")
            print(f"📊 Response keys: {list(data.keys())}")
            
            visual_citations = data.get("visual_citations", [])
            manual_references = data.get("manual_references", [])
            
            print(f"🎯 Visual citations: {len(visual_citations)}")
            print(f"📚 Manual references: {len(manual_references)}")
            
            if visual_citations:
                print("
📋 First visual citation:")
                print(json.dumps(visual_citations[0], indent=2))
            
            # Check the structure the frontend expects
            response_text = data.get("response", "")
            print(f"
📝 Response text length: {len(response_text)}")
            
            # Simulate what ChatService.sendMessage returns
            frontend_result = {
                "success": True,
                "data": data
            }
            
            print("
🔄 Frontend would extract:")
            print(f"   responseText: {len(response_text)} chars")
            print(f"   visualCitations: {len(visual_citations)}")
            print(f"   manualReferences: {len(manual_references)}")
            
            return True
            
        else:
            print(f"❌ API error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    test_frontend_api_flow()
