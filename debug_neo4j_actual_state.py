"""
Debug Neo4j Actual State vs Backend Reporting
Check what's really in Neo4j versus what the backend thinks is there
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'backend', '.env.rag'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_neo4j_state():
    """Debug actual Neo4j state vs backend reporting"""
    
    print("🔍 Debugging Neo4j State vs Backend Reporting")
    print("=" * 60)
    
    try:
        # Test 1: Direct Neo4j connection
        print("\n1. 📊 Direct Neo4j Query:")
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI')
        username = os.getenv('NEO4J_USERNAME') 
        password = os.getenv('NEO4J_PASSWORD')
        
        if not all([uri, username, password]):
            print("❌ Neo4j credentials not found in environment")
            return
            
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Count all nodes
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()["total_nodes"]
            print(f"   Total Nodes: {total_nodes}")
            
            # Count all relationships  
            result = session.run("MATCH ()-[r]-() RETURN count(r) as total_relationships")
            total_relationships = result.single()["total_relationships"]
            print(f"   Total Relationships: {total_relationships}")
            
            # Get node labels
            result = session.run("CALL db.labels() YIELD label RETURN label")
            labels = [record["label"] for record in result]
            print(f"   Node Labels: {labels}")
            
            # Count nodes by label
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()["count"]
                print(f"   {label}: {count} nodes")
            
            # Get recent nodes (if any have timestamps)
            result = session.run("""
                MATCH (n) 
                WHERE EXISTS(n.created_at) OR EXISTS(n.timestamp) OR EXISTS(n.upload_timestamp)
                RETURN n 
                ORDER BY COALESCE(n.created_at, n.timestamp, n.upload_timestamp) DESC 
                LIMIT 10
            """)
            recent_nodes = list(result)
            print(f"   Recent Nodes with Timestamps: {len(recent_nodes)}")
            
            # Check for Manager.pdf related nodes
            result = session.run("""
                MATCH (n) 
                WHERE toLower(toString(n)) CONTAINS 'manager' 
                   OR toLower(toString(n)) CONTAINS 'cheeseburger'
                   OR toLower(toString(n)) CONTAINS 'bobby'
                RETURN n LIMIT 10
            """)
            manager_nodes = list(result)
            print(f"   Manager.pdf Related Nodes: {len(manager_nodes)}")
            if manager_nodes:
                for i, record in enumerate(manager_nodes[:3]):
                    node = record["n"]
                    print(f"     Node {i+1}: {dict(node)}")
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Direct Neo4j query failed: {e}")
    
    try:
        # Test 2: Backend Neo4j Service
        print("\n2. 🔧 Backend Neo4j Service:")
        from services.neo4j_service import neo4j_service
        
        if neo4j_service.connect():
            print("   ✅ Backend service connected")
            nodes = neo4j_service.get_node_count()
            relationships = neo4j_service.get_relationship_count()
            print(f"   Backend Reports - Nodes: {nodes}, Relationships: {relationships}")
            
            # Get sample entities
            try:
                sample_entities = neo4j_service.get_sample_entities(5)
                print(f"   Sample Entities: {len(sample_entities)}")
                for i, entity in enumerate(sample_entities[:3]):
                    print(f"     Entity {i+1}: {entity}")
            except Exception as e:
                print(f"   Sample entities error: {e}")
        else:
            print("   ❌ Backend service connection failed")
            
    except Exception as e:
        print(f"❌ Backend service test failed: {e}")
    
    try:
        # Test 3: Check uploaded documents processing status
        print("\n3. 📄 Document Processing Status:")
        
        import json
        docs_file = "documents.json"
        if os.path.exists(docs_file):
            with open(docs_file, 'r') as f:
                docs = json.load(f)
            
            print(f"   Documents in documents.json: {len(docs)}")
            
            # Look for Manager.pdf entries
            manager_docs = [doc for doc_id, doc in docs.items() 
                          if isinstance(doc, dict) and 'Manager.pdf' in doc.get('original_filename', '')]
            print(f"   Manager.pdf entries: {len(manager_docs)}")
            
            for i, doc in enumerate(manager_docs):
                print(f"     Manager.pdf {i+1}:")
                print(f"       ID: {doc.get('id', 'N/A')}")
                print(f"       Upload Time: {doc.get('upload_timestamp', 'N/A')}")
                print(f"       Pages: {doc.get('pages_count', 'N/A')}")
                print(f"       Text Length: {len(doc.get('text_content', ''))}")
        else:
            print("   ❌ documents.json not found")
            
    except Exception as e:
        print(f"❌ Document processing status check failed: {e}")
    
    try:
        # Test 4: Check Neo4j verification file
        print("\n4. ✅ Neo4j Verification Status:")
        
        neo4j_verified_file = "backend/neo4j_verified_documents.json"
        if os.path.exists(neo4j_verified_file):
            with open(neo4j_verified_file, 'r') as f:
                verified_docs = json.load(f)
            print(f"   Verified documents: {len(verified_docs)}")
            
            # Check if our Manager.pdf docs are verified
            if isinstance(verified_docs, dict):
                manager_verified = [doc for doc_id, doc in verified_docs.items() 
                                  if isinstance(doc, dict) and 'Manager.pdf' in doc.get('original_filename', '')]
                print(f"   Manager.pdf verified: {len(manager_verified)}")
            else:
                print(f"   Verified docs format: {type(verified_docs)}")
        else:
            print("   ❌ neo4j_verified_documents.json not found")
            
    except Exception as e:
        print(f"❌ Verification status check failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Summary: Compare the numbers above to identify the discrepancy!")

if __name__ == "__main__":
    debug_neo4j_state()