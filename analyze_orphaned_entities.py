#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def analyze_orphaned_entities():
    """Analyze orphaned entities to understand the problem"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== ANALYZING ORPHANED ENTITIES ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Look at the properties of orphaned entities
            query = """
            MATCH (e)
            WHERE e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS
            AND NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
            RETURN labels(e) as labels, 
                   properties(e) as props
            LIMIT 20
            """
            
            results = session.run(query)
            print("SAMPLE ORPHANED ENTITIES WITH PROPERTIES:")
            for record in results:
                labels = record['labels']
                props = record['props']
                print(f"  {labels}: {props}")
            
            # Count entities by their actual property values
            print("\n=== ENTITY ANALYSIS BY PROPERTY VALUES ===")
            
            # Check what properties exist on these entities
            query = """
            MATCH (e:ENTITY)
            WHERE NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
            RETURN count(e) as count, keys(e) as property_keys
            LIMIT 10
            """
            
            results = session.run(query)
            print("ENTITY PROPERTY ANALYSIS:")
            for record in results:
                count = record['count']
                keys = record['property_keys']
                print(f"  Count: {count}, Keys: {keys}")
            
            # Look at specific property values
            query = """
            MATCH (e:ENTITY)
            WHERE NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
            RETURN e.text as text, e.description as description, e.document_id as doc_id, e.name as name
            LIMIT 10
            """
            
            results = session.run(query)
            print("\nENTITY PROPERTY VALUES:")
            for record in results:
                text = record['text']
                description = record['description']
                doc_id = record['doc_id']
                name = record['name']
                print(f"  text: '{text}', description: '{description}', doc_id: {doc_id}, name: '{name}'")
            
            # Check Equipment entities too
            query = """
            MATCH (e:EQUIPMENT)
            WHERE NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
            RETURN e.text as text, e.description as description, e.document_id as doc_id, e.name as name
            LIMIT 10
            """
            
            results = session.run(query)
            print("\nEQUIPMENT PROPERTY VALUES:")
            for record in results:
                text = record['text']
                description = record['description']
                doc_id = record['doc_id']
                name = record['name']
                print(f"  text: '{text}', description: '{description}', doc_id: {doc_id}, name: '{name}'")
            
            # Check if there are any entities WITH relationships to understand the difference
            query = """
            MATCH (e)
            WHERE e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS
            AND (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
            RETURN labels(e) as labels, 
                   properties(e) as props
            LIMIT 10
            """
            
            results = session.run(query)
            print("\nSAMPLE ENTITIES WITH RELATIONSHIPS:")
            for record in results:
                labels = record['labels']
                props = record['props']
                print(f"  {labels}: {props}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    analyze_orphaned_entities()