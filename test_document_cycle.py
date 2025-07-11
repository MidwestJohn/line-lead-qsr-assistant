#!/usr/bin/env python3
"""Test the complete document upload and deletion cycle"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_document_cycle():
    """Test upload, list, and delete operations"""
    print("🧪 Testing Document Lifecycle")
    print("=" * 50)
    
    # Step 1: Check initial state
    print("\n1️⃣ Checking initial document state...")
    response = requests.get(f"{BASE_URL}/documents")
    if response.status_code == 200:
        initial_docs = response.json()
        print(f"   Initial documents: {initial_docs['total_count']}")
        for doc in initial_docs['documents']:
            print(f"   - {doc['original_filename']} (ID: {doc['id']})")
    else:
        print(f"   ❌ Failed to get initial documents: {response.status_code}")
        return False
    
    # Step 2: Create a test PDF
    print("\n2️⃣ Creating test PDF...")
    test_pdf_path = Path("/tmp/test_document.pdf")
    
    # Simple PDF creation (minimal valid PDF)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000215 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
309
%%EOF"""
    
    with open(test_pdf_path, 'wb') as f:
        f.write(pdf_content)
    print(f"   Created test PDF at {test_pdf_path}")
    
    # Step 3: Upload the test document
    print("\n3️⃣ Uploading test document...")
    try:
        with open(test_pdf_path, 'rb') as f:
            files = {'file': ('test_document.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"   ✅ Upload successful: {upload_result.get('message', 'No message')}")
            uploaded_doc_id = upload_result.get('document_id')
            if uploaded_doc_id:
                print(f"   Document ID: {uploaded_doc_id}")
            else:
                print("   ⚠️ No document ID returned")
        else:
            print(f"   ❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return False
    
    # Step 4: List documents after upload
    print("\n4️⃣ Listing documents after upload...")
    time.sleep(2)  # Allow processing time
    response = requests.get(f"{BASE_URL}/documents")
    if response.status_code == 200:
        docs_after_upload = response.json()
        print(f"   Documents after upload: {docs_after_upload['total_count']}")
        uploaded_doc_found = None
        for doc in docs_after_upload['documents']:
            print(f"   - {doc['original_filename']} (ID: {doc['id']})")
            if doc['original_filename'] == 'test_document.pdf':
                uploaded_doc_found = doc
        
        if uploaded_doc_found:
            print(f"   ✅ Test document found in listing")
            doc_id_to_delete = uploaded_doc_found['id']
        else:
            print(f"   ❌ Test document not found in listing")
            return False
    else:
        print(f"   ❌ Failed to list documents: {response.status_code}")
        return False
    
    # Step 5: Delete the test document
    print(f"\n5️⃣ Deleting test document (ID: {doc_id_to_delete})...")
    response = requests.delete(f"{BASE_URL}/documents/{doc_id_to_delete}")
    if response.status_code == 200:
        delete_result = response.json()
        print(f"   ✅ Delete successful: {delete_result.get('message', 'No message')}")
    else:
        print(f"   ❌ Delete failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Step 6: Verify deletion
    print("\n6️⃣ Verifying deletion...")
    time.sleep(1)  # Allow processing time
    response = requests.get(f"{BASE_URL}/documents")
    if response.status_code == 200:
        docs_after_delete = response.json()
        print(f"   Documents after deletion: {docs_after_delete['total_count']}")
        test_doc_still_exists = any(doc['original_filename'] == 'test_document.pdf' 
                                   for doc in docs_after_delete['documents'])
        
        if test_doc_still_exists:
            print(f"   ❌ Test document still exists after deletion")
            return False
        else:
            print(f"   ✅ Test document successfully deleted")
    else:
        print(f"   ❌ Failed to verify deletion: {response.status_code}")
        return False
    
    # Cleanup
    test_pdf_path.unlink(missing_ok=True)
    
    print("\n🎉 Document lifecycle test PASSED!")
    return True

if __name__ == "__main__":
    success = test_document_cycle()
    exit(0 if success else 1)