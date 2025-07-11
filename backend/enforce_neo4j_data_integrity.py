#!/usr/bin/env python3
"""
Enforce Neo4j Data Integrity
============================

This script ensures that only documents confirmed to be in Neo4j graph database
are visible in the UI library and counted in health checks.

Data Integrity Rules:
1. Documents must be in Neo4j to appear in library
2. Health checks only count Neo4j-confirmed documents  
3. Processing status reflects actual Neo4j sync status
"""

import json
import requests
from services.neo4j_service import Neo4jService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_neo4j_documents():
    """Get list of documents that are actually in Neo4j"""
    try:
        neo4j = Neo4jService()
        neo4j.connect()
        
        with neo4j.driver.session() as session:
            result = session.run('''
                MATCH (d:Document)
                RETURN d.filename, d.document_id, d.original_filename
                ORDER BY d.filename
            ''')
            
            neo4j_docs = {}
            for record in result:
                filename = record['d.filename']
                doc_id = record['d.document_id']
                original_filename = record.get('d.original_filename')
                
                # Extract original filename from Neo4j filename if needed
                if '_' in filename and filename.count('_') > 0:
                    # Format: uuid_original-filename.ext
                    parts = filename.split('_', 1)
                    if len(parts) > 1:
                        extracted_original = parts[1]
                    else:
                        extracted_original = filename
                else:
                    extracted_original = filename
                
                neo4j_docs[doc_id] = {
                    'neo4j_filename': filename,
                    'original_filename': extracted_original,
                    'document_id': doc_id
                }
        
        neo4j.disconnect()
        return neo4j_docs
        
    except Exception as e:
        logger.error(f"Error getting Neo4j documents: {e}")
        return {}

def create_document_integrity_filter():
    """Create a mapping of which documents are actually in Neo4j"""
    
    print("🔍 ENFORCING NEO4J DATA INTEGRITY")
    print("=" * 60)
    
    # Get documents from Neo4j
    neo4j_docs = get_neo4j_documents()
    print(f"📊 Documents confirmed in Neo4j: {len(neo4j_docs)}")
    
    # Load current documents.json
    try:
        with open('/Users/johninniger/Workspace/line_lead_qsr_mvp/documents.json', 'r') as f:
            docs_db = json.load(f)
    except:
        docs_db = {}
    
    print(f"📁 Documents in system: {len(docs_db)}")
    print()
    
    # Create mapping of verified documents
    verified_documents = {}
    verified_count = 0
    
    print("✅ DOCUMENTS VERIFIED IN NEO4J:")
    for neo4j_id, neo4j_info in neo4j_docs.items():
        neo4j_original = neo4j_info['original_filename']
        
        # Try to find matching document in docs_db
        found_match = False
        for doc_id, doc_info in docs_db.items():
            system_original = doc_info.get('original_filename', '')
            
            # Check if filenames match (handle variations)
            if (system_original == neo4j_original or 
                system_original in neo4j_original or
                neo4j_original in system_original):
                
                verified_documents[doc_id] = {
                    **doc_info,
                    'neo4j_confirmed': True,
                    'neo4j_document_id': neo4j_id,
                    'status': 'complete',
                    'processing_stage': 'neo4j_synced'
                }
                verified_count += 1
                print(f"  ✅ {system_original} (System ID: {doc_id[:8]}..., Neo4j ID: {neo4j_id})")
                found_match = True
                break
        
        if not found_match:
            # Document in Neo4j but not in current system
            print(f"  ⚠️  {neo4j_original} (Only in Neo4j, ID: {neo4j_id})")
    
    print()
    print("❌ DOCUMENTS NOT IN NEO4J (will be filtered out):")
    for doc_id, doc_info in docs_db.items():
        if doc_id not in verified_documents:
            filename = doc_info.get('original_filename', 'unknown')
            print(f"  ❌ {filename}")
    
    print()
    print(f"📊 SUMMARY:")
    print(f"  - Documents in Neo4j: {len(neo4j_docs)}")
    print(f"  - Documents in system: {len(docs_db)}")
    print(f"  - Verified documents: {verified_count}")
    print(f"  - Will be filtered out: {len(docs_db) - verified_count}")
    
    return verified_documents

def create_integrity_filter_file():
    """Create a filter file that can be used by endpoints"""
    
    verified_docs = create_document_integrity_filter()
    
    # Save verified documents list
    filter_file = '/Users/johninniger/Workspace/line_lead_qsr_mvp/backend/neo4j_verified_documents.json'
    
    with open(filter_file, 'w') as f:
        json.dump(verified_docs, f, indent=2)
    
    print(f"💾 Created integrity filter: {filter_file}")
    print(f"📝 This file contains {len(verified_docs)} Neo4j-verified documents")
    
    return verified_docs

if __name__ == "__main__":
    verified_docs = create_integrity_filter_file()
    
    print()
    print("🎯 NEXT STEPS:")
    print("1. Update endpoints to use neo4j_verified_documents.json")
    print("2. Filter library to show only verified documents")
    print("3. Update health checks to count only verified documents")
    print("4. Ensure data integrity across all UI components")