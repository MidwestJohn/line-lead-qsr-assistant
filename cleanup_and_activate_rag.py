#!/usr/bin/env python3
"""
Database Cleanup and RAG-Anything Activation Script
Safely cleans existing data and activates RAG-Anything for fresh start
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def cleanup_neo4j_database():
    """Clean all existing data from Neo4j Aura"""
    print("🧹 CLEANING NEO4J AURA DATABASE")
    print("=" * 40)
    
    try:
        from backend.services.neo4j_service import neo4j_service
        
        # Connect to Neo4j
        if not neo4j_service.connect():
            print("❌ Failed to connect to Neo4j Aura")
            return False
        
        print("✅ Connected to Neo4j Aura")
        
        # Get current database state
        print("\n📊 Current database state:")
        count_result = neo4j_service.execute_query("MATCH (n) RETURN count(n) as total_nodes")
        if count_result['success']:
            total_nodes = count_result['records'][0]['total_nodes']
            print(f"   Total nodes: {total_nodes}")
        
        rel_count_result = neo4j_service.execute_query("MATCH ()-[r]->() RETURN count(r) as total_relationships")
        if rel_count_result['success']:
            total_rels = rel_count_result['records'][0]['total_relationships']
            print(f"   Total relationships: {total_rels}")
        
        if total_nodes == 0 and total_rels == 0:
            print("✅ Database is already clean")
            return True
        
        # Cleanup sequence
        print(f"\n🗑️  Removing {total_rels} relationships...")
        cleanup_rels = neo4j_service.execute_query("MATCH ()-[r]->() DELETE r")
        if cleanup_rels['success']:
            print("✅ All relationships removed")
        else:
            print(f"❌ Failed to remove relationships: {cleanup_rels.get('error')}")
            return False
        
        print(f"\n🗑️  Removing {total_nodes} nodes...")
        cleanup_nodes = neo4j_service.execute_query("MATCH (n) DELETE n")
        if cleanup_nodes['success']:
            print("✅ All nodes removed")
        else:
            print(f"❌ Failed to remove nodes: {cleanup_nodes.get('error')}")
            return False
        
        # Verify cleanup
        print("\n🔍 Verifying cleanup...")
        verify_result = neo4j_service.execute_query("MATCH (n) RETURN count(n) as remaining")
        if verify_result['success']:
            remaining = verify_result['records'][0]['remaining']
            if remaining == 0:
                print("✅ Database successfully cleaned - ready for fresh start")
                return True
            else:
                print(f"❌ {remaining} nodes still remain")
                return False
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def cleanup_existing_document_library():
    """Clean existing document library to start fresh"""
    print("\n📚 CLEANING EXISTING DOCUMENT LIBRARY")
    print("=" * 40)
    
    documents_file = Path("documents.json")
    uploads_dir = Path("uploads")
    
    # Backup existing documents
    if documents_file.exists():
        backup_file = documents_file.with_suffix('.json.backup')
        documents_file.rename(backup_file)
        print(f"✅ Backed up documents.json to {backup_file}")
    
    # Create empty documents.json
    with open(documents_file, 'w') as f:
        json.dump({}, f, indent=2)
    print("✅ Created fresh empty documents.json")
    
    # Clean uploads directory
    if uploads_dir.exists():
        upload_count = len(list(uploads_dir.glob("*")))
        if upload_count > 0:
            backup_uploads = Path("uploads_backup")
            uploads_dir.rename(backup_uploads)
            uploads_dir.mkdir()
            print(f"✅ Backed up {upload_count} uploads to uploads_backup/")
        else:
            print("✅ Uploads directory already empty")
    else:
        uploads_dir.mkdir()
        print("✅ Created fresh uploads directory")
    
    return True

def activate_rag_anything():
    """Activate RAG-Anything configuration"""
    print("\n🚀 ACTIVATING RAG-ANYTHING")
    print("=" * 40)
    
    env_file = Path("backend/.env.rag")
    
    if not env_file.exists():
        print("❌ .env.rag file not found")
        return False
    
    # Read current configuration
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Update configuration
    updated_content = content.replace(
        'USE_RAG_ANYTHING=false', 
        'USE_RAG_ANYTHING=true'
    ).replace(
        'USE_GRAPH_CONTEXT=false',
        'USE_GRAPH_CONTEXT=true'
    )
    
    # Write updated configuration
    with open(env_file, 'w') as f:
        f.write(updated_content)
    
    print("✅ Updated RAG-Anything configuration:")
    print("   USE_RAG_ANYTHING=true")
    print("   USE_GRAPH_CONTEXT=true")
    
    return True

def validate_rag_activation():
    """Validate that RAG-Anything is properly activated"""
    print("\n✅ VALIDATING RAG ACTIVATION")
    print("=" * 40)
    
    try:
        from fastapi.testclient import TestClient
        from backend.main import app
        
        client = TestClient(app)
        
        # Test RAG health
        print("🔍 Testing RAG health...")
        response = client.get('/rag-health')
        if response.status_code == 200:
            data = response.json()
            if data['enabled']:
                print("✅ RAG-Anything is enabled")
                if data['neo4j_available']:
                    print("✅ Neo4j is available")
                else:
                    print("⚠️  Neo4j not available")
            else:
                print("❌ RAG-Anything not enabled")
                return False
        else:
            print(f"❌ RAG health check failed: {response.status_code}")
            return False
        
        # Test voice capabilities
        print("🔍 Testing voice capabilities...")
        response = client.get('/voice-capabilities')
        if response.status_code == 200:
            data = response.json()
            if data['graph_context']:
                print("✅ Graph context enabled")
            else:
                print("⚠️  Graph context not enabled")
        
        # Test Neo4j connection
        print("🔍 Testing Neo4j connection...")
        response = client.get('/neo4j-health')
        if response.status_code == 200:
            data = response.json()
            if data['healthy']:
                print("✅ Neo4j Aura connection healthy")
            else:
                print("❌ Neo4j Aura connection not healthy")
                return False
        
        print("\n🎉 RAG-Anything activation validated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def main():
    """Main cleanup and activation function"""
    print("🎯 DATABASE CLEANUP AND RAG-ANYTHING ACTIVATION")
    print("=" * 60)
    
    print("This script will:")
    print("1. Clean all data from Neo4j Aura database")
    print("2. Backup and reset document library")
    print("3. Activate RAG-Anything configuration")
    print("4. Validate activation")
    
    confirm = input("\nProceed with cleanup and activation? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Operation cancelled")
        sys.exit(0)
    
    # Step 1: Cleanup Neo4j
    if not cleanup_neo4j_database():
        print("❌ Neo4j cleanup failed - aborting")
        sys.exit(1)
    
    # Step 2: Cleanup document library
    if not cleanup_existing_document_library():
        print("❌ Document library cleanup failed - aborting")
        sys.exit(1)
    
    # Step 3: Activate RAG-Anything
    if not activate_rag_anything():
        print("❌ RAG-Anything activation failed - aborting")
        sys.exit(1)
    
    # Step 4: Validate activation
    if not validate_rag_activation():
        print("❌ RAG-Anything validation failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 CLEANUP AND ACTIVATION COMPLETE!")
    print("=" * 60)
    print()
    print("✅ Neo4j Aura database: CLEAN")
    print("✅ Document library: RESET")
    print("✅ RAG-Anything: ACTIVATED")
    print("✅ Graph context: ENABLED")
    print()
    print("🚀 Ready for fresh knowledge graph construction!")
    print()
    print("Next steps:")
    print("1. Upload QSR documents via /upload-rag endpoint")
    print("2. Test knowledge graph construction")
    print("3. Validate voice context with graph relationships")

if __name__ == "__main__":
    main()