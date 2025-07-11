#!/usr/bin/env python3
"""
Manual Neo4j Population Script
Directly populates Neo4j with the extracted semantic entities and relationships
"""

import json
import os
import sys
from pathlib import Path

# Add the backend path so we can import services
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')

def load_semantic_graph():
    """Load the latest semantic graph file"""
    storage_path = Path('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend/data/rag_storage')
    
    # Find the latest semantic graph file
    graph_files = list(storage_path.glob('semantic_graph_semantic_test_manual.pdf_*.json'))
    if not graph_files:
        print("❌ No semantic graph files found")
        return None
    
    latest_file = max(graph_files, key=lambda p: p.stat().st_mtime)
    print(f"📄 Loading: {latest_file}")
    
    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data.get('entities', []))} entities and {len(data.get('relationships', []))} relationships")
        return data
    except Exception as e:
        print(f"❌ Failed to load semantic graph: {e}")
        return None

def populate_neo4j(data):
    """Manually populate Neo4j with the semantic data"""
    try:
        # Import Neo4j service
        from services.neo4j_service import neo4j_service
        
        if not neo4j_service or not neo4j_service.connected:
            print("❌ Neo4j service not connected")
            print("Attempting to connect...")
            
            # Try to initialize connection
            import os
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv(dotenv_path='/Users/johninniger/Workspace/line_lead_qsr_mvp/backend/.env')
            
            neo4j_uri = os.getenv('NEO4J_URI')
            neo4j_username = os.getenv('NEO4J_USERNAME') 
            neo4j_password = os.getenv('NEO4J_PASSWORD')
            
            print(f"Connecting to: {neo4j_uri}")
            
            if neo4j_service:
                # Try manual connection
                print("Attempting manual connection...")
                success = neo4j_service.connect()
                if success:
                    print("✅ Connected to Neo4j")
                else:
                    print("❌ Manual connection failed")
                    return False
            else:
                print("❌ Neo4j service not available")
                return False
        
        print("🚀 Starting Neo4j population...")
        
        with neo4j_service.driver.session() as session:
            # Check current state
            result = session.run("MATCH (n) RETURN count(n) as count")
            before_count = result.single()["count"]
            print(f"📊 Current nodes in Neo4j: {before_count}")
            
            # Clear existing data (optional - for clean test)
            print("🧹 Clearing existing nodes for clean test...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # Populate entities
            entities = data.get('entities', [])
            print(f"📥 Creating {len(entities)} entities...")
            
            for entity in entities:
                entity_type = entity.get('type', 'Entity')
                query = f"""
                CREATE (n:`{entity_type}` {{
                    name: $name,
                    description: $description,
                    content: $content,
                    document_source: $source,
                    entity_id: $entity_id,
                    classification_confidence: $confidence,
                    qsr_classified: $qsr_classified
                }})
                """
                
                session.run(query, 
                    name=entity['name'],
                    description=entity.get('description', ''),
                    content=entity.get('content', ''),
                    source=entity.get('document_source', ''),
                    entity_id=entity.get('id', ''),
                    confidence=entity.get('classification_confidence', 0.5),
                    qsr_classified=entity.get('qsr_classified', False)
                )
                print(f"  ✅ Created {entity_type}: {entity['name']}")
            
            # Populate relationships
            relationships = data.get('relationships', [])
            print(f"🔗 Creating {len(relationships)} relationships...")
            
            for rel in relationships:
                # Find source and target entities by name
                source_name = rel.get('source_entity', rel.get('source', ''))
                target_name = rel.get('target_entity', rel.get('target', ''))
                rel_type = rel.get('relationship_type', rel.get('type', 'RELATED_TO'))
                
                if source_name and target_name:
                    query = f"""
                    MATCH (source {{name: $source_name}})
                    MATCH (target {{name: $target_name}})
                    CREATE (source)-[r:`{rel_type}` {{
                        confidence: $confidence,
                        semantic_type: $semantic_type,
                        qsr_specific: $qsr_specific,
                        document_source: $source
                    }}]->(target)
                    """
                    
                    session.run(query,
                        source_name=source_name,
                        target_name=target_name,
                        confidence=rel.get('confidence', 0.5),
                        semantic_type=rel.get('semantic_type', ''),
                        qsr_specific=rel.get('qsr_specific', False),
                        source=rel.get('document_source', '')
                    )
                    print(f"  ✅ Created {rel_type}: {source_name} → {target_name}")
            
            # Check final state
            result = session.run("MATCH (n) RETURN count(n) as nodes")
            node_count = result.single()["nodes"]
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rels")
            rel_count = result.single()["rels"]
            
            print(f"🎯 Population complete!")
            print(f"📊 Final state: {node_count} nodes, {rel_count} relationships")
            print(f"📈 Added: {node_count - 0} nodes, {rel_count} relationships")
            
            # Sample query to verify content
            print("\n🔍 Sample entities created:")
            result = session.run("""
                MATCH (n) 
                RETURN labels(n) as labels, n.name as name, n.description as description
                LIMIT 5
            """)
            
            for record in result:
                labels = record["labels"]
                name = record["name"]
                description = record["description"]
                print(f"  {labels}: {name} - {description}")
                
            return True
                
    except Exception as e:
        print(f"❌ Neo4j population failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 MANUAL NEO4J POPULATION")
    print("=" * 50)
    
    # Load semantic graph data
    data = load_semantic_graph()
    if not data:
        return
    
    # Populate Neo4j
    success = populate_neo4j(data)
    
    if success:
        print("\n✅ SUCCESS: Neo4j populated with semantic entities!")
        print("🎯 Next steps:")
        print("  1. Test voice queries with graph context")
        print("  2. Verify multimodal citations work with populated graph")
        print("  3. Run validation endpoint to confirm results")
    else:
        print("\n❌ FAILED: Neo4j population unsuccessful")

if __name__ == "__main__":
    main()