#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def final_database_state_check():
    """Final check of Neo4j database state with corrected queries"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== FINAL NEO4J DATABASE STATE CHECK ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Get all node labels and counts
            query = """
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("NODE COUNTS BY LABEL:")
            total_nodes = 0
            for record in results:
                label = record['label']
                count = record['count']
                total_nodes += count
                print(f"  {label}: {count}")
            
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
            
            # Check entities with semantic relationships (CORRECTED)
            print("\n=== ENTITY CONNECTIVITY CHECK ===")
            
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
            
            # Check truly orphaned entities (CORRECTED)
            query = """
            MATCH (e)
            WHERE (e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS)
            AND NOT EXISTS { (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-() }
            RETURN labels(e)[0] as label, count(e) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("\nORPHANED ENTITIES (CORRECTED QUERY):")
            total_orphaned = 0
            for record in results:
                label = record['label']
                count = record['count']
                total_orphaned += count
                print(f"  {label}: {count}")
            
            print(f"\nTotal orphaned entities: {total_orphaned}")
            
            # Calculate coverage
            entity_types = ["ENTITY", "EQUIPMENT", "LOCATION", "PROCEDURE", "PROCESS"]
            total_target_entities = 0
            
            for entity_type in entity_types:
                query = f"""
                MATCH (e:{entity_type})
                RETURN count(e) as count
                """
                result = session.run(query)
                count = result.single()['count']
                total_target_entities += count
            
            coverage_percentage = (total_connected / total_target_entities) * 100 if total_target_entities > 0 else 0
            
            print(f"\n=== COVERAGE ANALYSIS ===")
            print(f"Target entities: {total_target_entities}")
            print(f"Connected entities: {total_connected}")
            print(f"Orphaned entities: {total_orphaned}")
            print(f"Coverage: {coverage_percentage:.1f}%")
            
            # Success criteria
            if total_orphaned == 0:
                print("\n✅ SUCCESS: All entities have semantic relationships!")
            elif total_orphaned < 10:
                print(f"\n✅ SUCCESS: Only {total_orphaned} orphaned entities remaining")
            else:
                print(f"\n⚠️  WARNING: {total_orphaned} orphaned entities still exist")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    final_database_state_check()