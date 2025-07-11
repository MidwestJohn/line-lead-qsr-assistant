#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def investigate_actual_isolation():
    """Investigate the actual isolation of Entity, Equipment, QSR-Specific, and Temperature nodes"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== INVESTIGATING ACTUAL ISOLATION OF KEY NODE TYPES ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Check isolation of each key node type
            node_types = ["ENTITY", "EQUIPMENT", "QSR_SPECIFIC", "TEMPERATURE"]
            
            for node_type in node_types:
                print(f"=== {node_type} NODE ANALYSIS ===")
                
                # Check nodes with no relationships at all
                query = f"""
                MATCH (n:{node_type})
                WHERE NOT EXISTS {{ (n)-[]-() }}
                RETURN count(n) as isolated_count
                """
                
                result = session.run(query)
                isolated_count = result.single()['isolated_count']
                print(f"Completely isolated {node_type} nodes: {isolated_count}")
                
                # Check nodes with very few relationships (1-3)
                query = f"""
                MATCH (n:{node_type})
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) as rel_count
                WHERE rel_count >= 1 AND rel_count <= 3
                RETURN count(n) as weakly_connected_count
                """
                
                result = session.run(query)
                weakly_connected = result.single()['weakly_connected_count']
                print(f"Weakly connected {node_type} nodes (1-3 rels): {weakly_connected}")
                
                # Sample isolated/weakly connected nodes
                query = f"""
                MATCH (n:{node_type})
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) as rel_count
                WHERE rel_count <= 3
                RETURN coalesce(n.name, n.text, n.description, 'NO_IDENTIFIER') as identifier,
                       rel_count,
                       keys(n) as properties
                ORDER BY rel_count
                LIMIT 10
                """
                
                results = session.run(query)
                print(f"Sample isolated/weakly connected {node_type} nodes:")
                for record in results:
                    identifier = record['identifier']
                    rel_count = record['rel_count']
                    properties = record['properties']
                    print(f"  '{identifier}': {rel_count} rels, props: {properties}")
                
                # Check what types of relationships these nodes have
                query = f"""
                MATCH (n:{node_type})-[r]-()
                WITH n, count(r) as rel_count
                WHERE rel_count <= 3
                MATCH (n)-[r2]-()
                RETURN type(r2) as relationship_type, count(r2) as count
                ORDER BY count DESC
                """
                
                results = session.run(query)
                print(f"Relationship types for weakly connected {node_type} nodes:")
                for record in results:
                    rel_type = record['relationship_type']
                    count = record['count']
                    print(f"  {rel_type}: {count}")
                
                print()
            
            # Check for meaningful semantic relationships between these node types
            print("=== SEMANTIC RELATIONSHIP ANALYSIS ===")
            
            # Check Equipment-Entity relationships
            query = """
            MATCH (e:EQUIPMENT)-[r:RELATED_TO|:PART_OF|:REQUIRES|:USES]-(n:ENTITY)
            RETURN count(r) as equipment_entity_rels
            """
            
            result = session.run(query)
            equipment_entity_rels = result.single()['equipment_entity_rels']
            print(f"Equipment-Entity semantic relationships: {equipment_entity_rels}")
            
            # Check QSR_SPECIFIC connections
            query = """
            MATCH (q:QSR_SPECIFIC)-[r:RELATED_TO|:PART_OF|:REQUIRES|:USES]-(n)
            WHERE n:ENTITY OR n:EQUIPMENT OR n:TEMPERATURE
            RETURN count(r) as qsr_semantic_rels
            """
            
            result = session.run(query)
            qsr_semantic_rels = result.single()['qsr_semantic_rels']
            print(f"QSR_SPECIFIC semantic relationships: {qsr_semantic_rels}")
            
            # Check Temperature connections
            query = """
            MATCH (t:TEMPERATURE)-[r:RELATED_TO|:PART_OF|:REQUIRES|:USES]-(n)
            WHERE n:ENTITY OR n:EQUIPMENT OR n:QSR_SPECIFIC
            RETURN count(r) as temperature_semantic_rels
            """
            
            result = session.run(query)
            temperature_semantic_rels = result.single()['temperature_semantic_rels']
            print(f"Temperature semantic relationships: {temperature_semantic_rels}")
            
            # Check cross-type connectivity
            print("\n=== CROSS-TYPE CONNECTIVITY ===")
            
            cross_type_queries = [
                ("ENTITY", "EQUIPMENT", "Entity-Equipment"),
                ("ENTITY", "QSR_SPECIFIC", "Entity-QSR_Specific"),
                ("ENTITY", "TEMPERATURE", "Entity-Temperature"),
                ("EQUIPMENT", "QSR_SPECIFIC", "Equipment-QSR_Specific"),
                ("EQUIPMENT", "TEMPERATURE", "Equipment-Temperature"),
                ("QSR_SPECIFIC", "TEMPERATURE", "QSR_Specific-Temperature")
            ]
            
            for type1, type2, description in cross_type_queries:
                query = f"""
                MATCH (n1:{type1})-[r]-(n2:{type2})
                RETURN count(r) as cross_type_rels
                """
                
                result = session.run(query)
                cross_rels = result.single()['cross_type_rels']
                print(f"{description} relationships: {cross_rels}")
            
            # Check if relationships are meaningful or just generic
            print("\n=== RELATIONSHIP QUALITY CHECK ===")
            
            # Are most relationships just generic RELATED_TO?
            query = """
            MATCH (n)-[r]-(m)
            WHERE (n:ENTITY OR n:EQUIPMENT OR n:QSR_SPECIFIC OR n:TEMPERATURE)
            AND (m:ENTITY OR m:EQUIPMENT OR m:QSR_SPECIFIC OR m:TEMPERATURE)
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            """
            
            results = session.run(query)
            print("Relationship distribution between key node types:")
            for record in results:
                rel_type = record['rel_type']
                count = record['count']
                print(f"  {rel_type}: {count}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    investigate_actual_isolation()