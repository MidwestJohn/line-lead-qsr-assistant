#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def debug_orphaned_relationships():
    """Debug why orphaned entities still exist despite creating relationships"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== DEBUGGING ORPHANED RELATIONSHIPS ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Check if any of the allegedly orphaned entities actually have relationships
            print("1. Checking if 'orphaned' entities actually have relationships...")
            
            query = """
            MATCH (e:EQUIPMENT)
            WHERE e.name IS NOT NULL
            OPTIONAL MATCH (e)-[r1:RELATED_TO]-()
            OPTIONAL MATCH (e)-[r2:PROCEDURE_FOR]-()
            OPTIONAL MATCH (e)-[r3:PART_OF]-()
            OPTIONAL MATCH (e)-[r4:LOCATED_AT]-()
            OPTIONAL MATCH (e)-[r5:REQUIRES]-()
            OPTIONAL MATCH (e)-[r6:USES]-()
            RETURN e.name as name, 
                   count(r1) as related_to_count,
                   count(r2) as procedure_for_count,
                   count(r3) as part_of_count,
                   count(r4) as located_at_count,
                   count(r5) as requires_count,
                   count(r6) as uses_count
            LIMIT 10
            """
            
            results = session.run(query)
            print("RELATIONSHIP COUNTS FOR EQUIPMENT ENTITIES:")
            for record in results:
                name = record['name']
                related_to = record['related_to_count']
                procedure_for = record['procedure_for_count']
                part_of = record['part_of_count']
                located_at = record['located_at_count']
                requires = record['requires_count']
                uses = record['uses_count']
                total = related_to + procedure_for + part_of + located_at + requires + uses
                print(f"  {name}: RELATED_TO={related_to}, PROCEDURE_FOR={procedure_for}, PART_OF={part_of}, LOCATED_AT={located_at}, REQUIRES={requires}, USES={uses}, TOTAL={total}")
            
            print("\n2. Checking what types of relationships exist...")
            
            # Get all relationship types
            query = """
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("ALL RELATIONSHIP TYPES:")
            for record in results:
                rel_type = record['rel_type']
                count = record['count']
                print(f"  {rel_type}: {count}")
            
            print("\n3. Checking if the orphaned entities are involved in ANY relationships...")
            
            # Check if orphaned entities have any relationships at all
            query = """
            MATCH (e:EQUIPMENT)
            WHERE e.name IS NOT NULL
            OPTIONAL MATCH (e)-[r]-()
            RETURN e.name as name, collect(type(r)) as relationship_types, count(r) as total_relationships
            LIMIT 10
            """
            
            results = session.run(query)
            print("ALL RELATIONSHIPS FOR EQUIPMENT ENTITIES:")
            for record in results:
                name = record['name']
                rel_types = record['relationship_types']
                total = record['total_relationships']
                print(f"  {name}: {total} relationships - {set(rel_types)}")
            
            print("\n4. Let's check specifically for entities with the exact names we saw...")
            
            # Check specific entities we know exist
            query = """
            MATCH (e)
            WHERE e.name = 'Model C602Bacteria'
            OPTIONAL MATCH (e)-[r]-()
            RETURN e, labels(e) as labels, collect(type(r)) as relationship_types, count(r) as total_relationships
            """
            
            results = session.run(query)
            print("SPECIFIC ENTITY CHECK (Model C602Bacteria):")
            for record in results:
                entity = record['e']
                labels = record['labels']
                rel_types = record['relationship_types']
                total = record['total_relationships']
                print(f"  Labels: {labels}")
                print(f"  Properties: {dict(entity)}")
                print(f"  Relationships: {total} - {set(rel_types)}")
            
            print("\n5. Let's see what makes an entity 'orphaned' according to our query...")
            
            # Test our orphaned entity query on a specific entity
            query = """
            MATCH (e)
            WHERE e.name = 'Model C602Bacteria'
            RETURN e.name as name,
                   (e)-[:RELATED_TO]-() as has_related_to,
                   (e)-[:PROCEDURE_FOR]-() as has_procedure_for,
                   (e)-[:PART_OF]-() as has_part_of,
                   (e)-[:LOCATED_AT]-() as has_located_at,
                   (e)-[:REQUIRES]-() as has_requires,
                   (e)-[:USES]-() as has_uses
            """
            
            results = session.run(query)
            print("ORPHANED ENTITY QUERY TEST:")
            for record in results:
                name = record['name']
                has_related_to = record['has_related_to']
                has_procedure_for = record['has_procedure_for']
                has_part_of = record['has_part_of']
                has_located_at = record['has_located_at']
                has_requires = record['has_requires']
                has_uses = record['has_uses']
                print(f"  {name}:")
                print(f"    RELATED_TO: {has_related_to}")
                print(f"    PROCEDURE_FOR: {has_procedure_for}")
                print(f"    PART_OF: {has_part_of}")
                print(f"    LOCATED_AT: {has_located_at}")
                print(f"    REQUIRES: {has_requires}")
                print(f"    USES: {has_uses}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    debug_orphaned_relationships()