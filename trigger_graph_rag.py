#!/usr/bin/env python3
"""
Script to trigger GraphRAG processing of the available documents
"""

import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')

def load_documents():
    """Load documents from documents.json"""
    docs_file = Path('/Users/johninniger/Workspace/line_lead_qsr_mvp/documents.json')
    
    if not docs_file.exists():
        print("❌ documents.json not found")
        return {}
    
    try:
        with open(docs_file, 'r') as f:
            documents = json.load(f)
        print(f"✅ Loaded {len(documents)} documents from documents.json")
        return documents
    except Exception as e:
        print(f"❌ Failed to load documents: {e}")
        return {}

def trigger_graph_rag(documents):
    """Trigger GraphRAG processing"""
    try:
        # Import the GraphRAG service
        from graph_rag_service import initialize_graph_rag_with_documents
        
        print("🚀 Starting GraphRAG processing...")
        success = initialize_graph_rag_with_documents(documents)
        
        if success:
            print("✅ GraphRAG processing completed successfully!")
            return True
        else:
            print("❌ GraphRAG processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during GraphRAG processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_neo4j_status():
    """Check Neo4j status after processing"""
    try:
        from services.neo4j_service import neo4j_service
        
        if neo4j_service and neo4j_service.connected:
            with neo4j_service.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = result.single()["count"]
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = result.single()["count"]
                
                print(f"📊 Neo4j status: {node_count} nodes, {rel_count} relationships")
                return node_count, rel_count
        else:
            print("⚠️ Neo4j not connected")
            return 0, 0
            
    except Exception as e:
        print(f"❌ Error checking Neo4j: {e}")
        return 0, 0

def main():
    print("🚀 TRIGGERING GRAPH RAG PIPELINE")
    print("=" * 50)
    
    # Load available documents
    documents = load_documents()
    if not documents:
        print("❌ No documents to process")
        return
    
    print(f"📄 Processing documents:")
    for doc_id, doc_info in documents.items():
        print(f"  - {doc_info.get('original_filename', doc_id)}")
    
    # Trigger GraphRAG processing
    success = trigger_graph_rag(documents)
    
    if success:
        print("\n🎯 GraphRAG processing completed!")
        
        # Check Neo4j status
        print("\n📊 Checking Neo4j status...")
        node_count, rel_count = check_neo4j_status()
        
        if node_count > 10:  # More than the initial 10 nodes mentioned
            print(f"✅ SUCCESS: Neo4j graph grew from 10 to {node_count} nodes!")
            print(f"🔗 Created {rel_count} relationships")
        else:
            print(f"⚠️ Neo4j has {node_count} nodes - may need manual population")
            
        print("\n🎯 Next steps:")
        print("  1. Check Neo4j browser to verify graph growth")
        print("  2. Test voice queries with graph context") 
        print("  3. Purge stale frontend data")
        print("  4. Re-upload a PDF to test end-to-end flow")
        
    else:
        print("\n❌ GraphRAG processing failed")
        print("Consider checking the backend logs for more details")

if __name__ == "__main__":
    main()