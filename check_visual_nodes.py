#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def check_visual_nodes():
    """Check what nodes might be appearing as isolated in the visual"""
    
    # Load environment variables
    load_dotenv()
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        print("NEO4J_PASSWORD not found in environment")
        return
    
    print("=== CHECKING VISUAL NODES ===\n")
    
    # Create driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Check all node types and their relationship counts
            print("1. Comprehensive node analysis...")
            
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            RETURN labels(n) as labels,
                   count(DISTINCT n) as node_count,
                   count(r) as total_relationships,
                   count(r) / count(DISTINCT n) as avg_relationships_per_node
            ORDER BY node_count DESC
            """
            
            results = session.run(query)
            print("NODE ANALYSIS (with relationship density):")
            for record in results:
                labels = record['labels']
                node_count = record['node_count']
                total_rels = record['total_relationships']
                avg_rels = record['avg_relationships_per_node']
                print(f"  {labels}: {node_count} nodes, {total_rels} total rels, {avg_rels:.1f} avg rels/node")
            
            # Check if there are nodes with very few relationships (might appear isolated)
            print("\n2. Nodes with very few relationships...")
            
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, labels(n) as labels, count(r) as rel_count
            WHERE rel_count <= 5
            RETURN labels, count(n) as node_count, rel_count
            ORDER BY rel_count, node_count DESC
            """
            
            results = session.run(query)
            print("NODES WITH ≤5 RELATIONSHIPS:")
            for record in results:
                labels = record['labels']
                node_count = record['node_count']
                rel_count = record['rel_count']
                print(f"  {labels}: {node_count} nodes with {rel_count} relationships")
            
            # Check the visual citation nodes specifically
            print("\n3. Visual citation node analysis...")
            
            query = """
            MATCH (v:VisualCitation)
            OPTIONAL MATCH (v)-[r]-()
            RETURN count(DISTINCT v) as total_visual_citations,
                   count(r) as total_relationships,
                   count(r) / count(DISTINCT v) as avg_rels_per_visual
            """
            
            results = session.run(query)
            for record in results:
                total_visual = record['total_visual_citations']
                total_rels = record['total_relationships']
                avg_rels = record['avg_rels_per_visual']
                print(f"VisualCitation nodes: {total_visual} total, {total_rels} total rels, {avg_rels:.1f} avg rels/node")
            
            # Sample visual citations to see their connectivity
            query = """
            MATCH (v:VisualCitation)
            OPTIONAL MATCH (v)-[r]-()
            WITH v, count(r) as rel_count
            RETURN v.citation_id as citation_id, rel_count
            ORDER BY rel_count
            LIMIT 10
            """
            
            results = session.run(query)
            print("\nSAMPLE VISUAL CITATIONS (lowest relationship counts):")
            for record in results:
                citation_id = record['citation_id']
                rel_count = record['rel_count']
                print(f"  Citation {citation_id}: {rel_count} relationships")
            
            # Check if some entities have only self-referential relationships
            print("\n4. Checking relationship patterns...")
            
            # Are there nodes that connect only to themselves or to very few other nodes?
            query = """
            MATCH (n)-[r]-(m)
            WHERE n <> m
            WITH n, count(DISTINCT m) as distinct_connections
            WHERE distinct_connections <= 2
            RETURN labels(n) as labels, count(n) as node_count, distinct_connections
            ORDER BY distinct_connections, node_count DESC
            LIMIT 10
            """
            
            results = session.run(query)
            print("NODES WITH ≤2 DISTINCT CONNECTIONS:")
            for record in results:
                labels = record['labels']
                node_count = record['node_count']
                connections = record['distinct_connections']
                print(f"  {labels}: {node_count} nodes with {connections} distinct connections")
            
            # Check the actual graph structure - are there disconnected components?
            print("\n5. Checking graph components...")
            
            # Simple check for nodes that are not connected to the main component
            query = """
            MATCH (start:Document)
            WHERE EXISTS { (start)-[]-() }
            CALL apoc.path.expand(start, "", "", 0, -1) YIELD path
            WITH collect(DISTINCT nodes(path)) as reachable_nodes
            UNWIND reachable_nodes as node_list
            UNWIND node_list as node
            WITH collect(DISTINCT node) as main_component
            
            MATCH (all_nodes)
            WHERE NOT all_nodes IN main_component
            RETURN labels(all_nodes) as labels, count(all_nodes) as unreachable_count
            ORDER BY unreachable_count DESC
            """
            
            # If APOC is not available, let's use a simpler approach
            try:
                results = session.run(query)
                print("NODES NOT REACHABLE FROM MAIN COMPONENT:")
                for record in results:
                    labels = record['labels']
                    count = record['unreachable_count']
                    print(f"  {labels}: {count} nodes")
            except:
                print("APOC not available, skipping component analysis")
            
            # Final check: what might the browser be showing?
            print("\n6. Browser visualization hypothesis...")
            
            # The browser might be showing all nodes but some appear isolated due to layout
            # Let's check if there are many weak connections
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, labels(n) as labels, count(r) as rel_count
            WHERE rel_count >= 1 AND rel_count <= 10
            RETURN labels, count(n) as node_count, rel_count
            ORDER BY rel_count, node_count DESC
            """
            
            results = session.run(query)
            print("NODES WITH 1-10 RELATIONSHIPS (might appear isolated in layout):")
            for record in results:
                labels = record['labels']
                node_count = record['node_count']
                rel_count = record['rel_count']
                print(f"  {labels}: {node_count} nodes with {rel_count} relationships")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()

if __name__ == "__main__":
    check_visual_nodes()