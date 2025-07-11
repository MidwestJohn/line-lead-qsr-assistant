#!/usr/bin/env python3
"""
Neo4j Connection Reality Check - Diagnose Manual vs Automatic Population Failure
===============================================================================

This script will definitively determine why your Neo4j Aura instance still 
shows only 10 nodes despite Memex reporting successful manual population.
"""

import os
from neo4j import GraphDatabase
import json
from datetime import datetime

# Your Neo4j Aura connection details
NEO4J_URI = "neo4j+s://57ed0189.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')  # Set this environment variable

def test_connection_reality():
    """Test what's actually in your Neo4j Aura instance."""
    
    print("🔍 TESTING ACTUAL NEO4J AURA INSTANCE")
    print(f"URI: {NEO4J_URI}")
    print(f"Username: {NEO4J_USERNAME}")
    print(f"Password: {'SET' if NEO4J_PASSWORD else 'NOT SET'}")
    
    if not NEO4J_PASSWORD:
        print("❌ NEO4J_PASSWORD environment variable not set!")
        return
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        with driver.session() as session:
            # Check total nodes
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()["total_nodes"]
            
            print(f"\n📊 ACTUAL NODE COUNT IN AURA: {total_nodes}")
            
            # Get all nodes with details
            result = session.run("""
                MATCH (n) 
                RETURN id(n) as node_id, labels(n) as labels, 
                       n.name as name, n.description as description
                ORDER BY id(n)
            """)
            
            print("\n📋 ALL NODES IN YOUR AURA INSTANCE:")
            nodes = []
            for record in result:
                node = {
                    "id": record["node_id"],
                    "labels": record["labels"],
                    "name": record["name"],
                    "description": record["description"]
                }
                nodes.append(node)
                print(f"  • ID: {node['id']}, Labels: {node['labels']}, Name: {node['name']}")
            
            # Check relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total_rels")
            total_rels = result.single()["total_rels"]
            
            print(f"\n🔗 ACTUAL RELATIONSHIP COUNT: {total_rels}")
            
            # Get relationship types
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\n📋 RELATIONSHIP TYPES:")
            for record in result:
                print(f"  • {record['rel_type']}: {record['count']}")
            
            # Test write capability
            test_node_name = f"connection_test_{datetime.now().strftime('%H%M%S')}"
            session.run("""
                CREATE (n:ConnectionTest {
                    name: $name,
                    created: datetime(),
                    test: 'reality_check'
                })
            """, name=test_node_name)
            
            # Verify test node was created
            result = session.run("""
                MATCH (n:ConnectionTest {name: $name})
                RETURN count(n) as test_created
            """, name=test_node_name)
            
            test_created = result.single()["test_created"]
            
            print(f"\n✅ WRITE TEST: {'SUCCESS' if test_created > 0 else 'FAILED'}")
            
            # Clean up test node
            session.run("MATCH (n:ConnectionTest {name: $name}) DELETE n", name=test_node_name)
            
        driver.close()
        
        return {
            "total_nodes": total_nodes,
            "total_relationships": total_rels,
            "can_write": test_created > 0,
            "nodes": nodes
        }
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")
        return None

def check_manual_script_target():
    """Check where the manual script is actually writing."""
    
    print("\n🔍 CHECKING MANUAL SCRIPT CONFIGURATION")
    
    # Look for manual_neo4j_population.py
    script_locations = [
        "./manual_neo4j_population.py",
        "../manual_neo4j_population.py", 
        "./scripts/manual_neo4j_population.py",
        "./backend/manual_neo4j_population.py"
    ]
    
    for location in script_locations:
        if os.path.exists(location):
            print(f"📄 Found script at: {location}")
            
            # Read the script to check connection details
            with open(location, 'r') as f:
                content = f.read()
                
            # Check for connection strings
            if "57ed0189.databases.neo4j.io" in content:
                print("✅ Script configured for your Aura instance")
            elif "bolt://localhost" in content or "neo4j://localhost" in content:
                print("❌ Script configured for LOCAL Neo4j, not Aura!")
            elif "neo4j+s://" in content:
                print("⚠️ Script has cloud connection but verify URI")
            else:
                print("❓ Cannot determine script connection target")
                
            # Check for hardcoded vs environment variables
            if "os.getenv" in content or "os.environ" in content:
                print("✅ Script uses environment variables")
            else:
                print("⚠️ Script may have hardcoded credentials")
                
            break
    else:
        print("❌ Manual script not found in common locations")

def check_extracted_data():
    """Check what data was actually extracted."""
    
    print("\n🔍 CHECKING EXTRACTED DATA FILES")
    
    # Look for JSON files with extracted data
    data_locations = [
        "./data/rag_storage",
        "./backend/data/rag_storage",
        "./rag_storage",
        "./lightrag_storage", 
        "./extracted_data",
        "./backend/rag_storage"
    ]
    
    for location in data_locations:
        if os.path.exists(location):
            print(f"📁 Found data directory: {location}")
            
            files = os.listdir(location)
            json_files = [f for f in files if f.endswith('.json')]
            
            print(f"📄 JSON files found: {len(json_files)}")
            
            for json_file in json_files[:5]:  # Check first 5 files
                file_path = os.path.join(location, json_file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        print(f"  • {json_file}: {len(data)} items")
                    elif isinstance(data, dict):
                        entities = data.get('entities', [])
                        relationships = data.get('relationships', [])
                        print(f"  • {json_file}: {len(entities)} entities, {len(relationships)} relationships")
                        
                        # Show sample entities
                        if entities:
                            print(f"    Sample entities: {[e.get('name', 'Unknown') for e in entities[:3]]}")
                        
                except Exception as e:
                    print(f"  • {json_file}: Could not read - {e}")
            
            break
    else:
        print("❌ No extracted data directories found")

def check_environment_variables():
    """Check what environment variables are actually set."""
    
    print("\n🔍 CHECKING ENVIRONMENT VARIABLES")
    
    env_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'NEO4J_DATABASE']
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"  • {var}: {'*' * len(value)} (SET)")
            else:
                print(f"  • {var}: {value}")
        else:
            print(f"  • {var}: NOT SET")

if __name__ == "__main__":
    print("NEO4J REALITY CHECK")
    print("==================")
    
    # Test 0: Environment variables
    check_environment_variables()
    
    # Test 1: What's actually in Neo4j Aura
    aura_data = test_connection_reality()
    
    # Test 2: Where is manual script writing
    check_manual_script_target()
    
    # Test 3: What data was extracted
    check_extracted_data()
    
    print("\n🎯 SUMMARY:")
    if aura_data:
        if aura_data["total_nodes"] <= 10:
            print("❌ CONFIRMED: Still only 10 or fewer nodes in Aura")
            print("❌ Manual population is NOT reaching your Aura instance")
        else:
            print(f"✅ Aura has {aura_data['total_nodes']} nodes")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Run this script to see actual Aura contents")
    print("2. Check manual script connection configuration") 
    print("3. Verify environment variables are correct")
    print("4. Test direct write to Aura from this script")