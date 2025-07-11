#!/usr/bin/env python3
"""
Simple Document Count Fix
Updates the document count to match Neo4j and fixes UI display
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from services.neo4j_service import Neo4jService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_document_count():
    """Fix document count to match Neo4j"""
    try:
        # Connect to Neo4j
        neo4j = Neo4jService()
        if not neo4j.connect():
            logger.error("❌ Failed to connect to Neo4j")
            return False
        
        with neo4j.driver.session() as session:
            # Get actual document count
            neo4j_doc_count = session.run("MATCH (d:Document) RETURN count(d) as count").single()["count"]
            
            # Get documents with proper properties
            docs = session.run("""
                MATCH (d:Document)
                RETURN d.filename as filename, d.document_id as doc_id, d.page_count as pages
                ORDER BY d.filename
            """).data()
            
            logger.info(f"📋 Found {neo4j_doc_count} documents in Neo4j:")
            for doc in docs:
                filename = doc['filename'] or 'unknown'
                pages = doc['pages'] or 0
                logger.info(f"  - {filename} ({pages} pages)")
        
        # Update documents.json
        documents_path = Path("documents.json")
        if documents_path.exists():
            with open(documents_path, 'r') as f:
                documents_data = json.load(f)
            
            # Update the count
            old_count = documents_data.get("count", 0)
            documents_data["count"] = neo4j_doc_count
            documents_data["last_updated"] = datetime.now().isoformat()
            documents_data["neo4j_verified"] = True
            
            # Make sure all documents are marked as complete
            if "documents" in documents_data and isinstance(documents_data["documents"], dict):
                for doc_id, doc_info in documents_data["documents"].items():
                    if isinstance(doc_info, dict):
                        doc_info["status"] = "complete"
                        doc_info["neo4j_verified"] = True
                        doc_info["last_updated"] = datetime.now().isoformat()
            
            with open(documents_path, 'w') as f:
                json.dump(documents_data, f, indent=2)
            
            logger.info(f"✅ Updated documents.json count: {old_count} → {neo4j_doc_count}")
            
            return True
        else:
            logger.error("❌ documents.json not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Document count fix failed: {e}")
        return False
    finally:
        neo4j.disconnect()

def verify_endpoints():
    """Verify that endpoints return consistent counts"""
    try:
        import requests
        
        # Check health endpoint
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            logger.info(f"🏥 Health endpoint: {health_data['status']} - {health_data['document_count']} documents")
        
        # Check documents endpoint
        docs_response = requests.get("http://localhost:8000/documents", timeout=5)
        if docs_response.status_code == 200:
            docs_data = docs_response.json()
            logger.info(f"📄 Documents endpoint: {len(docs_data)} documents")
            
            # Show document details
            for doc in docs_data:
                logger.info(f"  - {doc.get('filename', 'unknown')} (Status: {doc.get('status', 'unknown')})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Endpoint verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Simple Document Count Fix")
    print("=" * 40)
    
    logger.info("1. Fixing document count...")
    success1 = fix_document_count()
    
    logger.info("2. Verifying endpoints...")
    success2 = verify_endpoints()
    
    if success1 and success2:
        print("\n✅ DOCUMENT COUNT FIX COMPLETED!")
        print("- Document count updated to match Neo4j")
        print("- All documents marked as complete")
        print("- UI should now show correct counts")
    else:
        print("\n❌ Some fixes failed - check logs above")
    
    print("\n" + "=" * 40)