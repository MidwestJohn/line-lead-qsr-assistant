#!/usr/bin/env python3
"""
Process QSR documents directly with RAG-Anything to populate Neo4j with semantic relationships
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.true_rag_service import true_rag_service
from services.neo4j_service import neo4j_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path='.env.rag')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_qsr_documents():
    """Process QSR documents with true RAG-Anything."""
    
    print("🚀 RAG-Anything QSR Document Processing")
    print("=" * 50)
    
    # Initialize services
    print("📋 Step 1: Initializing services...")
    
    # Initialize RAG-Anything
    rag_success = await true_rag_service.initialize()
    print(f"   RAG-Anything: {'✅ Success' if rag_success else '❌ Failed'}")
    
    if not rag_success:
        print("❌ Cannot proceed without RAG-Anything")
        return
    
    # Initialize Neo4j
    neo4j_service.connect()
    neo4j_success = neo4j_service.connected
    print(f"   Neo4j: {'✅ Connected' if neo4j_success else '❌ Failed'}")
    
    # Load documents
    print("\n📁 Step 2: Loading documents...")
    documents_path = "../documents.json"
    if not os.path.exists(documents_path):
        print(f"❌ Documents file not found: {documents_path}")
        return
    
    with open(documents_path, 'r') as f:
        documents = json.load(f)
    
    print(f"   Found {len(documents)} documents:")
    for doc_id, doc_info in documents.items():
        print(f"   📄 {doc_info.get('original_filename', 'unknown')}")
    
    # Process each document
    print("\n🔄 Step 3: Processing documents with RAG-Anything...")
    results = []
    
    for i, (doc_id, doc_info) in enumerate(documents.items(), 1):
        filename = doc_info.get('original_filename', 'unknown')
        filepath = f"../uploads/{doc_info.get('filename', f'{doc_id}.pdf')}"
        
        print(f"\n   📖 Processing {i}/{len(documents)}: {filename}")
        print(f"      File: {filepath}")
        
        if not os.path.exists(filepath):
            print(f"      ❌ File not found: {filepath}")
            continue
        
        try:
            # Process with RAG-Anything
            print(f"      🔄 Running RAG-Anything processing...")
            result = await true_rag_service.process_document(filepath)
            
            success = result.get('success', False)
            status_message = "success" if success else result.get('error', 'unknown error')
            print(f"      {'✅ Success' if success else '❌ Failed'}: {status_message}")
            
            if success:
                entities_count = result.get('entities_count', 0)
                relationships_count = result.get('relationships_count', 0)
                print(f"      📊 Extracted: {entities_count} entities, {relationships_count} relationships")
            else:
                print(f"      Error: {result.get('error', 'unknown error')}")
            
            results.append({
                'filename': filename,
                'success': success,
                'result': result
            })
            
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            results.append({
                'filename': filename,
                'success': False,
                'error': str(e)
            })
    
    # Check Neo4j results
    print("\n🔍 Step 4: Checking Neo4j results...")
    
    if neo4j_success:
        try:
            with neo4j_service.driver.session() as session:
                # Check nodes and relationships
                result = session.run("""
                    MATCH (n)
                    OPTIONAL MATCH ()-[r]->()
                    RETURN count(DISTINCT n) as nodes, count(r) as relationships
                """).single()
                
                nodes = result['nodes']
                relationships = result['relationships']
                
                print(f"   📊 Neo4j Graph Status:")
                print(f"      Nodes: {nodes}")
                print(f"      Relationships: {relationships}")
                
                # Check for semantic relationship types
                rel_types = session.run("""
                    MATCH ()-[r]->()
                    RETURN DISTINCT type(r) as rel_type, count(r) as count
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                print(f"   🔗 Relationship Types:")
                for record in rel_types:
                    rel_type = record['rel_type']
                    count = record['count']
                    print(f"      {rel_type}: {count}")
                
        except Exception as e:
            print(f"   ❌ Neo4j query failed: {e}")
    
    # Summary
    print("\n📈 Summary:")
    successful = sum(1 for r in results if r.get('success', False))
    print(f"   Documents processed: {successful}/{len(results)}")
    
    if successful > 0:
        print("   ✅ Success! Check Neo4j Browser for semantic relationships:")
        print("      - CONTAINS, PART_OF, REQUIRES relationships")
        print("      - Equipment unification (Taylor nodes connected)")
        print("      - Multi-modal content from images and tables")
    else:
        print("   ❌ No documents processed successfully")
        print("   🔧 Check RAG-Anything configuration and dependencies")

if __name__ == "__main__":
    asyncio.run(process_qsr_documents())