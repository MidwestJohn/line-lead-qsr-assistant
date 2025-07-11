#!/usr/bin/env python3
"""
Manual Neo4j Database Cleanup
Force complete wipe of Neo4j database to ensure clean slate
"""

import asyncio
import logging
from dotenv import load_dotenv
import sys

# Load environment
load_dotenv('.env.rag')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def force_neo4j_cleanup():
    """Force complete Neo4j database cleanup."""
    
    print("🔥 MANUAL NEO4J DATABASE CLEANUP")
    print("=" * 50)
    
    try:
        from services.neo4j_service import neo4j_service
        
        # Connect to Neo4j
        print("🔌 Connecting to Neo4j...")
        if not neo4j_service.connected:
            neo4j_service.connect()
        
        if not neo4j_service.connected:
            print("❌ Failed to connect to Neo4j")
            return False
        
        print("✅ Connected to Neo4j")
        
        # Get current statistics
        print("\n📊 CURRENT DATABASE STATE:")
        stats = await neo4j_service.get_graph_statistics()
        print(f"   Nodes: {stats.get('total_nodes', 0):,}")
        print(f"   Relationships: {stats.get('total_relationships', 0):,}")
        
        node_types = stats.get('node_types', {})
        if node_types:
            print("   Node Types:")
            for node_type, count in node_types.items():
                print(f"     {node_type}: {count:,}")
        
        if stats.get('total_nodes', 0) == 0:
            print("✅ Database is already empty!")
            return True
        
        # Confirm cleanup
        print(f"\n⚠️  WARNING: This will permanently delete ALL data in Neo4j!")
        print(f"   - {stats.get('total_nodes', 0):,} nodes will be deleted")
        print(f"   - {stats.get('total_relationships', 0):,} relationships will be deleted")
        print(f"   - All indexes and constraints will be dropped")
        
        confirm = input("\nType 'DELETE ALL' to confirm: ").strip()
        if confirm != 'DELETE ALL':
            print("❌ Cleanup cancelled")
            return False
        
        print("\n🔥 STARTING COMPLETE DATABASE WIPE...")
        print("-" * 50)
        
        # Step 1: Delete all relationships first
        print("🔄 Step 1: Deleting all relationships...")
        rel_result = neo4j_service.execute_query("""
            MATCH ()-[r]-() 
            DELETE r
        """)
        
        if rel_result.get('success'):
            print("✅ All relationships deleted")
        else:
            print(f"❌ Failed to delete relationships: {rel_result.get('error', 'Unknown error')}")
        
        # Step 2: Delete all nodes
        print("🔄 Step 2: Deleting all nodes...")
        node_result = neo4j_service.execute_query("""
            MATCH (n) 
            DELETE n
        """)
        
        if node_result.get('success'):
            print("✅ All nodes deleted")
        else:
            print(f"❌ Failed to delete nodes: {node_result.get('error', 'Unknown error')}")
        
        # Step 3: Drop all constraints
        print("🔄 Step 3: Dropping all constraints...")
        
        # Get all constraints
        constraints_result = neo4j_service.execute_query("SHOW CONSTRAINTS YIELD name")
        
        if constraints_result.get('success'):
            constraints = constraints_result.get('records', [])
            print(f"   Found {len(constraints)} constraints to drop")
            
            for constraint in constraints:
                constraint_name = constraint.get('name', '')
                if constraint_name:
                    try:
                        drop_result = neo4j_service.execute_query(f"DROP CONSTRAINT {constraint_name}")
                        if drop_result.get('success'):
                            print(f"   ✅ Dropped constraint: {constraint_name}")
                        else:
                            print(f"   ❌ Failed to drop constraint: {constraint_name}")
                    except Exception as e:
                        print(f"   ❌ Error dropping constraint {constraint_name}: {e}")
        
        # Step 4: Drop all indexes
        print("🔄 Step 4: Dropping all indexes...")
        
        # Get all indexes
        indexes_result = neo4j_service.execute_query("SHOW INDEXES YIELD name")
        
        if indexes_result.get('success'):
            indexes = indexes_result.get('records', [])
            print(f"   Found {len(indexes)} indexes to drop")
            
            for index in indexes:
                index_name = index.get('name', '')
                # Skip system indexes
                if index_name and not index_name.startswith('system'):
                    try:
                        drop_result = neo4j_service.execute_query(f"DROP INDEX {index_name}")
                        if drop_result.get('success'):
                            print(f"   ✅ Dropped index: {index_name}")
                        else:
                            print(f"   ❌ Failed to drop index: {index_name}")
                    except Exception as e:
                        print(f"   ❌ Error dropping index {index_name}: {e}")
        
        # Step 5: Verify cleanup
        print("🔄 Step 5: Verifying cleanup...")
        
        final_stats = await neo4j_service.get_graph_statistics()
        
        print(f"\n📊 FINAL DATABASE STATE:")
        print(f"   Nodes: {final_stats.get('total_nodes', 0):,}")
        print(f"   Relationships: {final_stats.get('total_relationships', 0):,}")
        
        # Check if cleanup was successful
        if final_stats.get('total_nodes', 0) == 0 and final_stats.get('total_relationships', 0) == 0:
            print("\n🎉 DATABASE CLEANUP SUCCESSFUL!")
            print("✅ Neo4j database is now completely empty")
            print("✅ Ready for clean slate testing")
            return True
        else:
            print("\n❌ DATABASE CLEANUP INCOMPLETE!")
            print("⚠️  Some data may still remain")
            print("⚠️  Manual intervention may be required")
            return False
            
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_empty_database():
    """Verify the database is truly empty."""
    
    print("\n🔍 VERIFYING EMPTY DATABASE...")
    
    try:
        from services.neo4j_service import neo4j_service
        
        # Multiple verification queries
        verification_queries = [
            ("Node count", "MATCH (n) RETURN count(n) as count"),
            ("Relationship count", "MATCH ()-[r]-() RETURN count(r) as count"),
            ("Any data", "MATCH (n) OPTIONAL MATCH (n)-[r]-() RETURN count(n) + count(r) as total")
        ]
        
        all_empty = True
        
        for query_name, query in verification_queries:
            result = neo4j_service.execute_query(query)
            
            if result.get('success') and result.get('records'):
                count = result['records'][0].get('count', 0) or result['records'][0].get('total', 0)
                print(f"   {query_name}: {count}")
                
                if count > 0:
                    all_empty = False
            else:
                print(f"   {query_name}: Query failed")
                all_empty = False
        
        if all_empty:
            print("✅ Database verification passed - completely empty")
        else:
            print("❌ Database verification failed - data still present")
            
        return all_empty
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

async def main():
    """Main cleanup function."""
    
    print("🔥 MANUAL NEO4J CLEANUP UTILITY")
    print("=" * 50)
    print("This utility will PERMANENTLY DELETE all data in Neo4j")
    print("Use this to ensure a clean slate for testing")
    print("=" * 50)
    
    # Execute cleanup
    cleanup_success = await force_neo4j_cleanup()
    
    if cleanup_success:
        # Verify cleanup
        verification_success = await verify_empty_database()
        
        if verification_success:
            print("\n🎉 CLEANUP COMPLETE AND VERIFIED!")
            print("✅ Neo4j database is completely empty")
            print("✅ Ready for clean slate testing")
            print("\n🚀 You can now run:")
            print("   ./run_memex_test.sh")
            print("   python backend/e2e_test.py")
            return True
        else:
            print("\n⚠️  CLEANUP COMPLETE BUT VERIFICATION FAILED")
            print("❌ Some data may still remain")
            return False
    else:
        print("\n❌ CLEANUP FAILED")
        print("⚠️  Manual intervention required")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)