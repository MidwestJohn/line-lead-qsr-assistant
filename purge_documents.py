#!/usr/bin/env python3
"""
Script to purge all documents from the Line Lead QSR MVP system
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def get_documents():
    """Get list of all documents"""
    try:
        response = requests.get(f"{BASE_URL}/documents")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting documents: {e}")
        return None

def delete_document(doc_id):
    """Delete a specific document"""
    try:
        response = requests.delete(f"{BASE_URL}/documents/{doc_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error deleting document {doc_id}: {e}")
        return None

def purge_all_documents():
    """Purge all documents from the system"""
    print("🗑️  Starting document purge...")
    
    # Get current documents
    docs_response = get_documents()
    if not docs_response:
        print("❌ Failed to get documents list")
        return
    
    documents = docs_response.get('documents', [])
    total_count = len(documents)
    
    if total_count == 0:
        print("✅ No documents to purge")
        return
    
    print(f"📄 Found {total_count} documents to delete")
    
    # Delete each document
    success_count = 0
    for i, doc in enumerate(documents, 1):
        doc_id = doc['id']
        filename = doc['original_filename']
        
        print(f"🗑️  Deleting ({i}/{total_count}): {filename}")
        
        result = delete_document(doc_id)
        if result and result.get('success'):
            success_count += 1
            print(f"   ✅ Deleted successfully")
        else:
            print(f"   ❌ Failed to delete")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    print(f"\n📊 Purge complete: {success_count}/{total_count} documents deleted")
    
    # Verify purge
    print("\n🔍 Verifying purge...")
    final_docs = get_documents()
    if final_docs:
        remaining = len(final_docs.get('documents', []))
        if remaining == 0:
            print("✅ All documents successfully purged")
        else:
            print(f"⚠️  {remaining} documents still remain")
    else:
        print("❌ Could not verify purge status")

if __name__ == "__main__":
    purge_all_documents()