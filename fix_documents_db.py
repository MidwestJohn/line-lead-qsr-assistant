#!/usr/bin/env python3
"""
Fix the documents database by removing corrupted entries
"""

import json
import os
from datetime import datetime

def fix_documents_db():
    """Fix the documents database by removing entries without required fields"""
    
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
    corrupted_docs = []
    for doc_id, doc_info in docs_db.items():
        required_fields = ['id', 'filename', 'original_filename', 'upload_timestamp', 'file_size', 'pages_count', 'text_content', 'text_preview']
        
        missing_fields = []
        for field in required_fields:
            if field not in doc_info:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Document {doc_id} is missing fields: {missing_fields}")
            corrupted_docs.append(doc_id)
    
    if corrupted_docs:
        print(f"Found {len(corrupted_docs)} corrupted documents")
        
        # Create backup
        backup_path = f"documents_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_path, 'w') as f:
            json.dump(docs_db, f, indent=2)
        print(f"Created backup: {backup_path}")
        
        # Remove corrupted documents
        for doc_id in corrupted_docs:
            del docs_db[doc_id]
            print(f"Removed corrupted document: {doc_id}")
        
        # Save the cleaned database
        with open(db_path, 'w') as f:
            json.dump(docs_db, f, indent=2)
        
        print(f"Cleaned database saved. {len(docs_db)} documents remaining.")
    else:
        print("No corrupted documents found.")

if __name__ == "__main__":
    fix_documents_db()