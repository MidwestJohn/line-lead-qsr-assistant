#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def check_neo4j_direct():
    """Check current Neo4j database state directly"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== NEO4J DATABASE STATE CHECK ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Get all node labels and counts
            query = """
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
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
            
            results = session.run(query)
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
            
            results = session.run(query)
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
            
            results = session.run(query)
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
            
            results = session.run(query)
            print("\nSAMPLE ORPHANED ENTITIES:")
            for record in results:
                labels = record['labels']
                text = record['text']
                doc_id = record['doc_id']
                print(f"  {labels}: '{text}' (doc: {doc_id})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    check_neo4j_direct()