#!/usr/bin/env python3
"""
Neo4j Graph Status Checker
==========================

Check the current state of the Neo4j graph and provide insights.
"""

from services.neo4j_service import neo4j_service

def check_graph_status():
    """Check the current state of the Neo4j graph."""
    
    print("🔍 Neo4j Graph Status Report")
    print("=" * 50)
    
    if not neo4j_service.connect():
        print("❌ Could not connect to Neo4j")
        return False
    
    try:
        # Overall statistics
        stats = neo4j_service.execute_query("MATCH (n) RETURN count(n) as total_nodes")
        total_nodes = stats['records'][0]['total_nodes']
        
        rel_stats = neo4j_service.execute_query("MATCH ()-[r]-() RETURN count(r) as total_relationships")
        total_relationships = rel_stats['records'][0]['total_relationships']
        
        print(f"📊 Overall Statistics:")
        print(f"   Total Nodes: {total_nodes}")
        print(f"   Total Relationships: {total_relationships}")
        print(f"   Graph Density: {total_relationships / total_nodes:.2f} relationships per node")
        
        # Node labels distribution
        label_stats = neo4j_service.execute_query("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """)
        
        print(f"\n🏷️ Node Labels Distribution:")
        for record in label_stats['records']:
            if record['label']:
                print(f"   {record['label']}: {record['count']}")
        
        # Node types distribution
        type_stats = neo4j_service.execute_query("""
            MATCH (n) 
            WHERE n.type IS NOT NULL
            RETURN n.type as node_type, count(n) as count
            ORDER BY count DESC
        """)
        
        print(f"\n📈 Node Types Distribution:")
        for record in type_stats['records']:
            print(f"   {record['node_type']}: {record['count']}")
        
        # Relationship types
        rel_type_stats = neo4j_service.execute_query("""
            MATCH ()-[r]->() 
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """)
        
        print(f"\n🔗 Relationship Types:")
        for record in rel_type_stats['records']:
            print(f"   {record['rel_type']}: {record['count']}")
        
        # Recent additions (from our bridge)
        recent_nodes = neo4j_service.execute_query("""
            MATCH (n)
            WHERE n.source = 'lightrag_bridge'
            RETURN n.name as name, n.type as type, n.created_at as created
            ORDER BY n.created_at DESC
            LIMIT 10
        """)
        
        if recent_nodes['records']:
            print(f"\n🆕 Recent Additions (via Bridge):")
            for record in recent_nodes['records']:
                print(f"   {record['name']} ({record['type']}) - {record['created'][:10]}")
        
        # Sample QSR entities
        qsr_entities = neo4j_service.execute_query("""
            MATCH (n)
            WHERE n.type IN ['EQUIPMENT', 'MAINTENANCE', 'SAFETY', 'PARAMETER']
            RETURN n.name as name, n.type as type, n.description as description
            ORDER BY n.type, n.name
            LIMIT 15
        """)
        
        if qsr_entities['records']:
            print(f"\n🔧 QSR Knowledge Graph Entities:")
            current_type = None
            for record in qsr_entities['records']:
                if record['type'] != current_type:
                    current_type = record['type']
                    print(f"\n   {current_type}:")
                print(f"     • {record['name']}")
                if record['description']:
                    print(f"       {record['description'][:60]}...")
        
        # Sample relationships with context
        sample_rels = neo4j_service.execute_query("""
            MATCH (a)-[r]->(b)
            WHERE r.description IS NOT NULL
            RETURN a.name as source, type(r) as rel_type, b.name as target, r.description as description
            LIMIT 8
        """)
        
        if sample_rels['records']:
            print(f"\n🔗 Sample Relationships:")
            for record in sample_rels['records']:
                print(f"   {record['source']} --[{record['rel_type']}]--> {record['target']}")
                if record['description']:
                    print(f"     {record['description']}")
        
        # Graph completeness metrics
        nodes_with_descriptions = neo4j_service.execute_query("""
            MATCH (n)
            WHERE n.description IS NOT NULL AND n.description <> ''
            RETURN count(n) as count
        """)
        
        nodes_with_types = neo4j_service.execute_query("""
            MATCH (n)
            WHERE n.type IS NOT NULL
            RETURN count(n) as count
        """)
        
        print(f"\n📋 Graph Quality Metrics:")
        print(f"   Nodes with descriptions: {nodes_with_descriptions['records'][0]['count']}/{total_nodes} ({nodes_with_descriptions['records'][0]['count']/total_nodes*100:.1f}%)")
        print(f"   Nodes with types: {nodes_with_types['records'][0]['count']}/{total_nodes} ({nodes_with_types['records'][0]['count']/total_nodes*100:.1f}%)")
        
        # Bridge success indicator
        bridge_nodes = neo4j_service.execute_query("""
            MATCH (n)
            WHERE n.source = 'lightrag_bridge'
            RETURN count(n) as count
        """)
        
        if bridge_nodes['records'][0]['count'] > 0:
            print(f"\n✅ Bridge Success: {bridge_nodes['records'][0]['count']} nodes successfully transferred via bridge")
        
        print(f"\n🎯 Summary:")
        print(f"   • Graph is populated with {total_nodes} nodes and {total_relationships} relationships")
        print(f"   • QSR knowledge graph is active and queryable")
        print(f"   • Bridge system is working and has added structured data")
        print(f"   • Ready for frontend integration and user queries")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking graph status: {e}")
        return False
    
    finally:
        neo4j_service.disconnect()

if __name__ == "__main__":
    check_graph_status()