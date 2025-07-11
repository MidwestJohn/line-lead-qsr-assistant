#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def fix_orphaned_query():
    """Test and fix the orphaned entity query"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== FIXING ORPHANED ENTITY QUERY ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Test the correct orphaned entity query
            print("1. Testing corrected orphaned entity query...")
            
            # The correct query should check for entities without semantic relationships
            # But let's see if the problem is with using (-) instead of (->)
            query = """
            MATCH (e)
            WHERE (e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS)
            AND NOT EXISTS { (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-() }
            RETURN labels(e)[0] as label, count(e) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("ORPHANED ENTITIES (CORRECTED QUERY):")
            total_orphaned = 0
            for record in results:
                label = record['label']
                count = record['count']
                total_orphaned += count
                print(f"  {label}: {count}")
            
            print(f"\nTotal orphaned entities (corrected): {total_orphaned}")
            
            # Compare with entities that DO have semantic relationships
            print("\n2. Entities WITH semantic relationships...")
            
            query = """
            MATCH (e)
            WHERE (e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS)
            AND EXISTS { (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-() }
            RETURN labels(e)[0] as label, count(e) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("ENTITIES WITH SEMANTIC RELATIONSHIPS:")
            total_connected = 0
            for record in results:
                label = record['label']
                count = record['count']
                total_connected += count
                print(f"  {label}: {count}")
            
            print(f"\nTotal connected entities: {total_connected}")
            
            # Test specifically with bidirectional relationships
            print("\n3. Testing bidirectional relationships...")
            
            query = """
            MATCH (e)
            WHERE (e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS)
            AND NOT (EXISTS { (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]->() } 
                     OR EXISTS { (e)<-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-() })
            RETURN labels(e)[0] as label, count(e) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("ENTITIES WITH NO BIDIRECTIONAL SEMANTIC RELATIONSHIPS:")
            total_truly_orphaned = 0
            for record in results:
                label = record['label']
                count = record['count']
                total_truly_orphaned += count
                print(f"  {label}: {count}")
            
            print(f"\nTotal truly orphaned entities: {total_truly_orphaned}")
            
            # Now let's see what the differences are
            print("\n4. Sample truly orphaned entities...")
            
            query = """
            MATCH (e)
            WHERE (e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS)
            AND NOT (EXISTS { (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]->() } 
                     OR EXISTS { (e)<-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-() })
            RETURN labels(e) as labels, 
                   coalesce(e.name, e.text, e.description, 'NO_TEXT') as identifier,
                   properties(e) as props
            LIMIT 10
            """
            
            results = session.run(query)
            print("SAMPLE TRULY ORPHANED ENTITIES:")
            for record in results:
                labels = record['labels']
                identifier = record['identifier']
                props = record['props']
                print(f"  {labels}: '{identifier}' - {len(props)} properties")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    fix_orphaned_query()