#!/usr/bin/env python3
import requests
import json

def test_api():
    try:
        response = requests.post(
            "http://localhost:8000/chat/stream",
            headers={"Content-Type": "application/json"},
            json={"message": "Show me an image of Pizza Canotto"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("API Response received")
            print(f"Response keys: {list(data.keys())}")
            
            # Debug: Check actual values
            print(f"visual_citations raw: {data.get('visual_citations')}")
            print(f"manual_references raw: {data.get('manual_references')}")
            
            visual_citations = data.get("visual_citations") or []
            manual_references = data.get("manual_references") or []
            
            print(f"Visual citations: {len(visual_citations)}")
            print(f"Manual references: {len(manual_references)}")
            
            if visual_citations:
                print("First visual citation:")
                citation = visual_citations[0]
                print(f"  Type: {citation.get('type')}")
                print(f"  Source: {citation.get('source')}")
                print(f"  Page: {citation.get('page')}")
            
            return True
            
        else:
            print(f"API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    test_api()