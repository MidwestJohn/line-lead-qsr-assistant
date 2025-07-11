#!/usr/bin/env python3
"""
Check Neo4j graph status and document processing pipeline
"""

import sys
import os
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')

from services.neo4j_service import Neo4jService
import json

def check_neo4j_status():
    print("🔍 Checking Neo4j status and document processing pipeline...")
    
    neo4j = Neo4jService()
    connected = neo4j.connect()
    
    if not connected:
        print("❌ Cannot connect to Neo4j")
        return
    
    try:
        with neo4j.driver.session() as session:
            # Check overall graph stats
            print("\n📊 Graph Statistics:")
            result = session.run('MATCH (n) RETURN count(n) as total_nodes')
            total_nodes = result.single()['total_nodes']
            print(f"  Total nodes: {total_nodes}")
            
            result = session.run('MATCH ()-[r]->() RETURN count(r) as total_relationships')
            total_relationships = result.single()['total_relationships']
            print(f"  Total relationships: {total_relationships}")
            
            # Check node types
            print("\n🏷️  Node Types:")
            result = session.run('MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC')
            for record in result:
                labels = record['labels']
                count = record['count']
                if labels:
                    print(f"  {', '.join(labels)}: {count}")
            
            # Check relationship types
            print("\n🔗 Relationship Types:")
            result = session.run('MATCH ()-[r]->() RETURN type(r) as rel_type, count(*) as count ORDER BY count DESC')
            for record in result:
                rel_type = record['rel_type']
                count = record['count']
                print(f"  {rel_type}: {count}")
            
            # Check for QSR-related content
            print("\n🏭 QSR Equipment and Procedures:")
            equipment_query = """
            MATCH (n) 
            WHERE n.name CONTAINS 'machine' OR n.name CONTAINS 'equipment' OR 
                  n.name CONTAINS 'ice cream' OR n.name CONTAINS 'freezer' OR
                  n.name CONTAINS 'Taylor' OR n.name CONTAINS 'C602'
            RETURN n.name as name, labels(n) as labels
            LIMIT 10
            """
            result = session.run(equipment_query)
            equipment_found = False
            for record in result:
                if not equipment_found:
                    equipment_found = True
                name = record['name']
                labels = record['labels']
                print(f"  {name} ({', '.join(labels)})")
            
            if not equipment_found:
                print("  No QSR equipment found in graph")
            
            # Check for document sources
            print("\n📄 Document Sources:")
            docs_query = """
            MATCH (n) 
            WHERE n.source IS NOT NULL OR n.document_id IS NOT NULL
            RETURN DISTINCT coalesce(n.source, n.document_id) as source
            LIMIT 10
            """
            result = session.run(docs_query)
            sources_found = False
            for record in result:
                if not sources_found:
                    sources_found = True
                source = record['source']
                print(f"  {source}")
            
            if not sources_found:
                print("  No document sources found in graph")
                
            # Check for recent additions
            print("\n⏰ Recent Activity:")
            recent_query = """
            MATCH (n) 
            WHERE n.created_at IS NOT NULL OR n.timestamp IS NOT NULL
            WITH n, coalesce(n.created_at, n.timestamp) as time_field
            WHERE time_field IS NOT NULL
            RETURN n.name as name, time_field
            ORDER BY time_field DESC
            LIMIT 5
            """
            result = session.run(recent_query)
            recent_found = False
            for record in result:
                if not recent_found:
                    recent_found = True
                name = record['name']
                timestamp = record['time_field']
                print(f"  {name} - {timestamp}")
            
            if not recent_found:
                print("  No timestamped content found")
                
    except Exception as e:
        print(f"❌ Error querying Neo4j: {e}")
    finally:
        neo4j.driver.close()

def check_processing_files():
    print("\n🔄 Processing Pipeline Status:")
    
    # Check processing files
    backend_dir = "/Users/johninniger/Workspace/line_lead_qsr_mvp/backend"
    
    # Check temp extraction files
    import glob
    temp_files = glob.glob(f"{backend_dir}/temp_extraction_*.json")
    print(f"\n📁 Temporary extraction files: {len(temp_files)}")
    for file in temp_files[-3:]:  # Show last 3
        filename = os.path.basename(file)
        size = os.path.getsize(file)
        print(f"  {filename} ({size} bytes)")
    
    # Check checkpoint files
    checkpoint_files = glob.glob(f"{backend_dir}/checkpoint_*.json")
    print(f"\n💾 Checkpoint files: {len(checkpoint_files)}")
    for file in checkpoint_files[-3:]:  # Show last 3
        filename = os.path.basename(file)
        size = os.path.getsize(file)
        print(f"  {filename} ({size} bytes)")

if __name__ == "__main__":
    check_neo4j_status()
    check_processing_files()