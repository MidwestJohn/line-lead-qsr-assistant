#!/usr/bin/env python3
"""
Test the load_documents_db function directly
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the function from the backend
def load_documents_db():
    """Load documents database from JSON file"""
    DOCUMENTS_DB = "documents.json"
    if os.path.exists(DOCUMENTS_DB):
        try:
            with open(DOCUMENTS_DB, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading documents database: {e}")
            return {}
    return {}

def test_load_db():
    """Test loading the documents database"""
    
    print("Testing load_documents_db function...")
    
    # Test the function
    docs_db = load_documents_db()
    print(f"Loaded {len(docs_db)} documents")
    
    # Check each document
    for doc_id, doc_info in docs_db.items():
        print(f"\nDocument: {doc_id}")
        
        # Check if id field exists
        if 'id' in doc_info:
            print(f"  ✅ ID field: '{doc_info['id']}'")
        else:
            print(f"  ❌ NO ID FIELD")
        
        # Check all available fields
        print(f"  Available fields: {list(doc_info.keys())}")
        
        # Try to access the id field like the backend does
        try:
            extracted_id = doc_info["id"]
            print(f"  ✅ ID access successful: {extracted_id}")
        except KeyError as e:
            print(f"  ❌ ID access failed: {e}")
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_load_db()