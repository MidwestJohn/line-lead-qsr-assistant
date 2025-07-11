#!/usr/bin/env python3
"""
Test Document Deletion Pipeline
Comprehensive test of document deletion functionality
"""

import asyncio
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.rag')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_document_deletion_pipeline():
    """Test the complete document deletion pipeline."""
    
    print("🧪 TESTING DOCUMENT DELETION PIPELINE")
    print("=" * 50)
    
    try:
        # Import services
        from services.neo4j_service import neo4j_service
        from services.rag_service import rag_service
        from services.document_deletion_service import DocumentDeletionService
        
        # Connect to Neo4j
        print("🔌 Connecting to Neo4j...")
        if not neo4j_service.connected:
            neo4j_service.connect()
        
        if not neo4j_service.connected:
            print("❌ Failed to connect to Neo4j")
            return False
        
        print("✅ Connected to Neo4j")
        
        # Initialize deletion service
        deletion_service = DocumentDeletionService(neo4j_service, rag_service)
        
        # Step 1: Create test data
        print("\n🏗️  STEP 1: Creating test data...")
        await create_test_data()
        
        # Step 2: List documents
        print("\n📋 STEP 2: Listing documents...")
        documents = await deletion_service.list_documents_with_entities()
        
        print(f"Found {len(documents)} documents:")
        for doc in documents:
            print(f"  - Document: {doc.get('document_id', 'Unknown')}")
            print(f"    Entities: {doc.get('entity_count', 0)}")
        
        if not documents:
            print("⚠️  No documents found. Creating sample data...")
            await create_sample_documents()
            documents = await deletion_service.list_documents_with_entities()
        
        # Step 3: Test deletion preview
        if documents:
            test_doc_id = documents[0].get('document_id', '')
            
            print(f"\n🔍 STEP 3: Testing deletion preview for: {test_doc_id}")
            preview = await deletion_service.get_document_preview(test_doc_id)
            
            print(f"Deletion preview:")
            print(f"  - Entities to remove: {preview.get('entities_to_remove', 0)}")
            print(f"  - Entities to preserve: {preview.get('entities_to_preserve', 0)}")
            print(f"  - Relationships to remove: {preview.get('relationships_to_remove', 0)}")
            
            entity_types = preview.get('entity_types', {})
            if entity_types:
                print(f"  - Entity types to remove:")
                for entity_type, count in entity_types.items():
                    print(f"    {entity_type}: {count}")
            
            shared_entities = preview.get('shared_entities', [])
            if shared_entities:
                print(f"  - Shared entities (will be preserved):")
                for entity in shared_entities:
                    print(f"    {entity['name']} ({entity['type']}) - shared with {entity['shared_with']} other documents")
            
            # Step 4: Test actual deletion
            print(f"\n🗑️  STEP 4: Testing actual deletion...")
            print(f"Deleting document: {test_doc_id}")
            
            # Get before stats
            before_stats = await get_graph_stats()
            print(f"Before deletion:")
            print(f"  - Nodes: {before_stats.get('nodes', 0)}")
            print(f"  - Relationships: {before_stats.get('relationships', 0)}")
            
            # Execute deletion
            deletion_result = await deletion_service.delete_document(test_doc_id)
            
            print(f"Deletion result:")
            print(f"  - Success: {deletion_result.success}")
            print(f"  - Entities removed: {deletion_result.entities_removed}")
            print(f"  - Relationships removed: {deletion_result.relationships_removed}")
            print(f"  - Shared entities preserved: {deletion_result.shared_entities_preserved}")
            
            if deletion_result.errors:
                print(f"  - Errors: {deletion_result.errors}")
            
            if deletion_result.rollback_performed:
                print(f"  - Rollback performed: {deletion_result.rollback_performed}")
            
            # Get after stats
            after_stats = await get_graph_stats()
            print(f"After deletion:")
            print(f"  - Nodes: {after_stats.get('nodes', 0)}")
            print(f"  - Relationships: {after_stats.get('relationships', 0)}")
            
            # Verify deletion
            print(f"\n✅ STEP 5: Verifying deletion...")
            remaining_docs = await deletion_service.list_documents_with_entities()
            
            deleted_doc_found = any(doc.get('document_id') == test_doc_id for doc in remaining_docs)
            
            if deleted_doc_found:
                print(f"❌ Document {test_doc_id} still found in graph!")
                return False
            else:
                print(f"✅ Document {test_doc_id} successfully removed from graph")
            
            # Step 6: Test orphaned entity cleanup
            print(f"\n🧹 STEP 6: Testing orphaned entity cleanup...")
            
            # First create some orphaned entities
            await create_orphaned_entities()
            
            # Run cleanup
            orphaned_query = """
            MATCH (n)
            WHERE n.source_document_id IS NULL 
              AND (n.source_documents IS NULL OR size(n.source_documents) = 0)
            RETURN count(n) as orphaned_count
            """
            
            orphaned_result = neo4j_service.execute_query(orphaned_query)
            
            if orphaned_result.get('success'):
                orphaned_count = orphaned_result.get('records', [{}])[0].get('orphaned_count', 0)
                print(f"Found {orphaned_count} orphaned entities")
                
                if orphaned_count > 0:
                    # Clean up orphaned entities
                    cleanup_query = """
                    MATCH (n)
                    WHERE n.source_document_id IS NULL 
                      AND (n.source_documents IS NULL OR size(n.source_documents) = 0)
                    DETACH DELETE n
                    """
                    
                    cleanup_result = neo4j_service.execute_query(cleanup_query)
                    
                    if cleanup_result.get('success'):
                        print(f"✅ Cleaned up {orphaned_count} orphaned entities")
                    else:
                        print(f"❌ Failed to clean up orphaned entities")
                else:
                    print("✅ No orphaned entities found")
            
            print(f"\n🎉 DOCUMENT DELETION PIPELINE TEST COMPLETE")
            return True
        
        else:
            print("❌ No documents available for testing")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_test_data():
    """Create test data for deletion testing."""
    
    from services.neo4j_service import neo4j_service
    
    # Create test entities and relationships
    test_queries = [
        # Document 1 entities
        """
        CREATE (e1:Equipment {
            id: 'fryer_001',
            name: 'Deep Fryer Model X',
            source_document_id: 'doc_fryer_manual_001'
        })
        """,
        
        """
        CREATE (e2:Procedure {
            id: 'fryer_startup_001',
            name: 'Fryer Startup Procedure',
            source_document_id: 'doc_fryer_manual_001'
        })
        """,
        
        # Document 2 entities
        """
        CREATE (e3:Equipment {
            id: 'grill_001',
            name: 'Grill Model Y',
            source_document_id: 'doc_grill_manual_001'
        })
        """,
        
        # Shared entity (appears in both documents)
        """
        CREATE (e4:Safety {
            id: 'fire_safety_001',
            name: 'Fire Safety Protocol',
            source_documents: ['doc_fryer_manual_001', 'doc_grill_manual_001']
        })
        """,
        
        # Create relationships
        """
        MATCH (e1:Equipment {id: 'fryer_001'}), (e2:Procedure {id: 'fryer_startup_001'})
        CREATE (e1)-[:REQUIRES]->(e2)
        """,
        
        """
        MATCH (e1:Equipment {id: 'fryer_001'}), (e4:Safety {id: 'fire_safety_001'})
        CREATE (e1)-[:FOLLOWS]->(e4)
        """,
        
        """
        MATCH (e3:Equipment {id: 'grill_001'}), (e4:Safety {id: 'fire_safety_001'})
        CREATE (e3)-[:FOLLOWS]->(e4)
        """
    ]
    
    for query in test_queries:
        result = neo4j_service.execute_query(query)
        if not result.get('success'):
            print(f"❌ Failed to create test data: {result.get('error', 'Unknown error')}")

async def create_sample_documents():
    """Create sample documents for testing."""
    
    from services.neo4j_service import neo4j_service
    
    sample_queries = [
        """
        CREATE (e1:EQUIPMENT {
            id: 'sample_fryer',
            name: 'Sample Fryer Equipment',
            source_document_id: 'sample_document_001'
        })
        """,
        
        """
        CREATE (e2:PROCEDURE {
            id: 'sample_procedure',
            name: 'Sample Procedure',
            source_document_id: 'sample_document_001'
        })
        """,
        
        """
        MATCH (e1:EQUIPMENT {id: 'sample_fryer'}), (e2:PROCEDURE {id: 'sample_procedure'})
        CREATE (e1)-[:REQUIRES]->(e2)
        """
    ]
    
    for query in sample_queries:
        result = neo4j_service.execute_query(query)
        if not result.get('success'):
            print(f"❌ Failed to create sample data: {result.get('error', 'Unknown error')}")

async def create_orphaned_entities():
    """Create orphaned entities for cleanup testing."""
    
    from services.neo4j_service import neo4j_service
    
    orphaned_queries = [
        """
        CREATE (o1:ORPHANED {
            id: 'orphaned_001',
            name: 'Orphaned Entity 1'
        })
        """,
        
        """
        CREATE (o2:ORPHANED {
            id: 'orphaned_002',
            name: 'Orphaned Entity 2'
        })
        """
    ]
    
    for query in orphaned_queries:
        result = neo4j_service.execute_query(query)
        if not result.get('success'):
            print(f"❌ Failed to create orphaned entities: {result.get('error', 'Unknown error')}")

async def get_graph_stats():
    """Get current graph statistics."""
    
    from services.neo4j_service import neo4j_service
    
    stats_query = """
    MATCH (n)
    OPTIONAL MATCH (n)-[r]-()
    RETURN count(distinct n) as nodes, count(r) as relationships
    """
    
    result = neo4j_service.execute_query(stats_query)
    
    if result.get('success') and result.get('records'):
        return result['records'][0]
    else:
        return {'nodes': 0, 'relationships': 0}

async def main():
    """Main test function."""
    
    print("🧪 DOCUMENT DELETION PIPELINE TEST")
    print("=" * 50)
    
    success = await test_document_deletion_pipeline()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Document deletion pipeline is working correctly")
        return True
    else:
        print("\n❌ TESTS FAILED!")
        print("⚠️  Document deletion pipeline has issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)