#!/usr/bin/env python3

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from shared_neo4j_service import UnifiedNeo4jService
from collections import defaultdict

def check_neo4j_state():
    """Check current Neo4j database state"""
    
    # Initialize connector
    connector = UnifiedNeo4jService()
    
    # Try to connect
    try:
        connector.initialize_from_backend_config()
        if not connector.connected:
            print("Failed to connect to Neo4j")
            return
            
        print("=== NEO4J DATABASE STATE CHECK ===\n")
        
        # Get all node labels and counts
        query = """
        MATCH (n)
        RETURN labels(n) as labels, count(n) as count
        ORDER BY count DESC
        """
        
        results = connector.execute_query(query)
        print("NODE COUNTS BY LABEL:")
        total_nodes = 0
        for record in results:
            labels = record['labels']
            count = record['count']
            total_nodes += count
            print(f"  {labels}: {count}")
        
        print(f"\nTotal nodes: {total_nodes}")
        
        # Get relationship counts
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
        """
        
        results = connector.execute_query(query)
        print("\nRELATIONSHIP COUNTS BY TYPE:")
        total_relationships = 0
        for record in results:
            rel_type = record['rel_type']
            count = record['count']
            total_relationships += count
            print(f"  {rel_type}: {count}")
        
        print(f"\nTotal relationships: {total_relationships}")
        
        # Find orphaned entities (entities with no semantic relationships)
        print("\n=== ORPHANED ENTITIES CHECK ===")
        
        # Check entities with no outgoing relationships
        query = """
        MATCH (e)
        WHERE e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS
        AND NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]->()
        RETURN labels(e) as labels, count(e) as count
        ORDER BY count DESC
        """
        
        results = connector.execute_query(query)
        print("ENTITIES WITH NO OUTGOING SEMANTIC RELATIONSHIPS:")
        total_orphaned = 0
        for record in results:
            labels = record['labels']
            count = record['count']
            total_orphaned += count
            print(f"  {labels}: {count}")
        
        print(f"\nTotal orphaned entities: {total_orphaned}")
        
        # Check entities with no incoming relationships either
        query = """
        MATCH (e)
        WHERE e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS
        AND NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
        RETURN labels(e) as labels, count(e) as count
        ORDER BY count DESC
        """
        
        results = connector.execute_query(query)
        print("\nENTITIES WITH NO SEMANTIC RELATIONSHIPS AT ALL:")
        total_isolated = 0
        for record in results:
            labels = record['labels']
            count = record['count']
            total_isolated += count
            print(f"  {labels}: {count}")
        
        print(f"\nTotal completely isolated entities: {total_isolated}")
        
        # Sample some orphaned entities to understand the issue
        query = """
        MATCH (e)
        WHERE e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS
        AND NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
        RETURN labels(e) as labels, e.text as text, e.document_id as doc_id
        LIMIT 10
        """
        
        results = connector.execute_query(query)
        print("\nSAMPLE ORPHANED ENTITIES:")
        for record in results:
            labels = record['labels']
            text = record['text']
            doc_id = record['doc_id']
            print(f"  {labels}: '{text}' (doc: {doc_id})")
        
        connector.close()
        
    except Exception as e:
        print(f"Error checking Neo4j state: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_neo4j_state()