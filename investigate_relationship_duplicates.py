#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def investigate_relationship_duplicates():
    """Investigate why we have so many relationships but nodes still appear isolated"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== INVESTIGATING RELATIONSHIP DUPLICATES ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # 1. Check for duplicate relationships between same nodes
            print("1. Checking for duplicate relationships...")
            
            query = """
            MATCH (a)-[r]->(b)
            WITH a, b, type(r) as rel_type, count(r) as rel_count
            WHERE rel_count > 1
            RETURN rel_type, rel_count, count(*) as pairs_with_duplicates
            ORDER BY rel_count DESC
            LIMIT 10
            """
            
            results = session.run(query)
            print("DUPLICATE RELATIONSHIPS:")
            total_duplicates = 0
            for record in results:
                rel_type = record['rel_type']
                rel_count = record['rel_count']
                pairs = record['pairs_with_duplicates']
                total_duplicates += (rel_count - 1) * pairs
                print(f"  {rel_type}: {rel_count} duplicates between {pairs} node pairs")
            
            print(f"Total duplicate relationships: {total_duplicates}")
            
            # 2. Check for self-referential relationships
            print("\n2. Checking for self-referential relationships...")
            
            query = """
            MATCH (n)-[r]->(n)
            RETURN type(r) as rel_type, count(r) as self_refs
            ORDER BY self_refs DESC
            """
            
            results = session.run(query)
            print("SELF-REFERENTIAL RELATIONSHIPS:")
            total_self_refs = 0
            for record in results:
                rel_type = record['rel_type']
                self_refs = record['self_refs']
                total_self_refs += self_refs
                print(f"  {rel_type}: {self_refs}")
            
            print(f"Total self-referential relationships: {total_self_refs}")
            
            # 3. Check actual connectivity of specific node types
            print("\n3. Checking actual connectivity by node type...")
            
            node_types = ["ENTITY", "EQUIPMENT", "TEMPERATURE", "PROCESS", "QSR_SPECIFIC", "Document"]
            
            for node_type in node_types:
                # Count completely isolated nodes
                query = f"""
                MATCH (n:{node_type})
                WHERE NOT EXISTS {{ (n)-[]-() }}
                RETURN count(n) as isolated_count
                """
                
                result = session.run(query)
                isolated_count = result.single()['isolated_count']
                
                # Count total nodes
                query = f"""
                MATCH (n:{node_type})
                RETURN count(n) as total_count
                """
                
                result = session.run(query)
                total_count = result.single()['total_count']
                
                connected_count = total_count - isolated_count
                print(f"{node_type}: {connected_count}/{total_count} connected ({isolated_count} isolated)")
            
            # 4. Sample truly isolated nodes
            print("\n4. Sampling truly isolated nodes...")
            
            query = """
            MATCH (n)
            WHERE NOT EXISTS { (n)-[]-() }
            RETURN labels(n) as labels, 
                   coalesce(n.name, n.description, 'NO_IDENTIFIER') as identifier,
                   elementId(n) as node_id
            LIMIT 20
            """
            
            results = session.run(query)
            print("TRULY ISOLATED NODES:")
            for record in results:
                labels = record['labels']
                identifier = record['identifier']
                node_id = record['node_id']
                print(f"  {labels}: '{identifier}' (ID: {node_id})")
            
            # 5. Check relationship density by examining a sample
            print("\n5. Checking relationship density...")
            
            query = """
            MATCH (n:ENTITY)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as rel_count
            RETURN 
                min(rel_count) as min_rels,
                max(rel_count) as max_rels,
                avg(rel_count) as avg_rels,
                count(n) as total_entities
            """
            
            result = session.run(query)
            record = result.single()
            print(f"ENTITY relationship density:")
            print(f"  Min: {record['min_rels']}, Max: {record['max_rels']}, Avg: {record['avg_rels']:.1f}")
            print(f"  Total entities: {record['total_entities']}")
            
            # 6. Check if relationships are between different node types
            print("\n6. Checking cross-type relationships...")
            
            query = """
            MATCH (a)-[r]->(b)
            WHERE labels(a) <> labels(b)
            RETURN 
                labels(a)[0] as source_type,
                labels(b)[0] as target_type,
                type(r) as rel_type,
                count(r) as cross_type_rels
            ORDER BY cross_type_rels DESC
            LIMIT 10
            """
            
            results = session.run(query)
            print("CROSS-TYPE RELATIONSHIPS:")
            for record in results:
                source = record['source_type']
                target = record['target_type']
                rel_type = record['rel_type']
                count = record['cross_type_rels']
                print(f"  {source} -[{rel_type}]-> {target}: {count}")
            
            # 7. Check what's causing the high relationship count
            print("\n7. Analyzing high relationship count...")
            
            query = """
            MATCH (n)-[r]-()
            WITH n, count(r) as rel_count
            WHERE rel_count > 100
            RETURN labels(n) as labels, 
                   coalesce(n.name, n.description, 'HIGH_DEGREE_NODE') as identifier,
                   rel_count
            ORDER BY rel_count DESC
            LIMIT 10
            """
            
            results = session.run(query)
            print("HIGH-DEGREE NODES (>100 relationships):")
            for record in results:
                labels = record['labels']
                identifier = record['identifier']
                rel_count = record['rel_count']
                print(f"  {labels}: '{identifier}' has {rel_count} relationships")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    investigate_relationship_duplicates()