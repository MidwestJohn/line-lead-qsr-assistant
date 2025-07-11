#!/usr/bin/env python3
"""
Debug the documents database issue
"""

import json
import os
from datetime import datetime

def debug_documents_db():
    """Debug the documents database"""
    
    # Load the current documents database
    db_path = "documents.json"
    if not os.path.exists(db_path):
        print("documents.json not found!")
        return
    
    try:
        with open(db_path, 'r') as f:
            docs_db = json.load(f)
    except Exception as e:
        print(f"Error loading documents database: {e}")
        return
    
    print(f"Found {len(docs_db)} documents in database")
    
    # Check each document for required fields
    required_fields = ['id', 'filename', 'original_filename', 'upload_timestamp', 'file_size', 'pages_count', 'text_content', 'text_preview']
    
    for doc_id, doc_info in docs_db.items():
        print(f"\nDocument: {doc_id}")
        
        missing_fields = []
        for field in required_fields:
            if field not in doc_info:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"  ❌ Missing fields: {missing_fields}")
        else:
            print(f"  ✅ All required fields present")
            
        # Show the 'id' field specifically
        if 'id' in doc_info:
            print(f"  ID field: '{doc_info['id']}'")
        else:
            print(f"  ❌ NO ID FIELD")
        
        print(f"  Available fields: {list(doc_info.keys())}")
    
    # Try to simulate the failing operation
    print("\nTrying to simulate document listing...")
    try:
        documents = []
        for doc_id, doc_info in docs_db.items():
            # This is what the backend code is trying to do
            document_summary = {
                "id": doc_info["id"],  # This line is failing
                "filename": doc_info.get("filename", ""),
                "original_filename": doc_info["original_filename"],
                "upload_timestamp": doc_info["upload_timestamp"],
                "file_size": doc_info["file_size"],
                "pages_count": doc_info["pages_count"],
                "url": f"/files/{doc_info.get('filename', '')}",
                "file_type": "PDF"
            }
            documents.append(document_summary)
        
        print(f"✅ Document listing simulation successful. {len(documents)} documents processed.")
        
    except Exception as e:
        print(f"❌ Document listing simulation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_documents_db()