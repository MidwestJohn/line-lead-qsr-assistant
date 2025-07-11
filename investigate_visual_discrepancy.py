#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def investigate_visual_discrepancy():
    """Investigate why visual shows isolated nodes but queries show 100% coverage"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== INVESTIGATING VISUAL DISCREPANCY ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Let's check what the actual node connectivity looks like
            print("1. Checking actual node connectivity...")
            
            # Count nodes with NO relationships at all
            query = """
            MATCH (n)
            WHERE NOT EXISTS { (n)-[]-() }
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("NODES WITH NO RELATIONSHIPS AT ALL:")
            total_isolated = 0
            for record in results:
                labels = record['labels']
                count = record['count']
                total_isolated += count
                print(f"  {labels}: {count}")
            
            print(f"\nTotal completely isolated nodes: {total_isolated}")
            
            # Count nodes WITH relationships
            query = """
            MATCH (n)
            WHERE EXISTS { (n)-[]-() }
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("\nNODES WITH ANY RELATIONSHIPS:")
            total_connected = 0
            for record in results:
                labels = record['labels']
                count = record['count']
                total_connected += count
                print(f"  {labels}: {count}")
            
            print(f"\nTotal connected nodes: {total_connected}")
            
            # Sample isolated nodes to understand what they are
            print("\n2. Sampling isolated nodes...")
            
            query = """
            MATCH (n)
            WHERE NOT EXISTS { (n)-[]-() }
            RETURN labels(n) as labels, 
                   coalesce(n.name, n.text, n.description, 'NO_IDENTIFIER') as identifier,
                   keys(n) as properties
            LIMIT 20
            """
            
            results = session.run(query)
            print("SAMPLE ISOLATED NODES:")
            for record in results:
                labels = record['labels']
                identifier = record['identifier']
                properties = record['properties']
                print(f"  {labels}: '{identifier}' - props: {properties}")
            
            # Check if these are the entity types we care about
            print("\n3. Checking entity types in isolated nodes...")
            
            query = """
            MATCH (n)
            WHERE NOT EXISTS { (n)-[]-() }
            AND (n:ENTITY OR n:EQUIPMENT OR n:LOCATION OR n:PROCEDURE OR n:PROCESS)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("ISOLATED ENTITY-TYPE NODES:")
            total_isolated_entities = 0
            for record in results:
                labels = record['labels']
                count = record['count']
                total_isolated_entities += count
                print(f"  {labels}: {count}")
            
            print(f"\nTotal isolated entity-type nodes: {total_isolated_entities}")
            
            # Check relationship types more carefully
            print("\n4. Detailed relationship analysis...")
            
            # Look at what relationships the "connected" entities actually have
            query = """
            MATCH (n)-[r]-()
            WHERE n:ENTITY OR n:EQUIPMENT OR n:LOCATION OR n:PROCEDURE OR n:PROCESS
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("RELATIONSHIPS INVOLVING ENTITY-TYPE NODES:")
            for record in results:
                rel_type = record['rel_type']
                count = record['count']
                print(f"  {rel_type}: {count}")
            
            # Check if my previous query was wrong - test the exact same query
            print("\n5. Re-testing previous 'corrected' query...")
            
            query = """
            MATCH (e)
            WHERE (e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS)
            AND NOT EXISTS { (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-() }
            RETURN labels(e) as labels, count(e) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("ENTITIES WITHOUT SEMANTIC RELATIONSHIPS (SPECIFIC TYPES):")
            semantic_orphans = 0
            for record in results:
                labels = record['labels']
                count = record['count']
                semantic_orphans += count
                print(f"  {labels}: {count}")
            
            print(f"\nTotal semantic orphans: {semantic_orphans}")
            
            # The key question: Are entities connected only via HAS_VISUAL_REFERENCE?
            print("\n6. Checking if entities only have visual relationships...")
            
            query = """
            MATCH (e)
            WHERE (e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS)
            AND EXISTS { (e)-[:HAS_VISUAL_REFERENCE]-() }
            AND NOT EXISTS { (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-() }
            RETURN labels(e) as labels, count(e) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("ENTITIES WITH ONLY VISUAL RELATIONSHIPS:")
            visual_only = 0
            for record in results:
                labels = record['labels']
                count = record['count']
                visual_only += count
                print(f"  {labels}: {count}")
            
            print(f"\nTotal entities with only visual relationships: {visual_only}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    investigate_visual_discrepancy()