"""
Complete Neo4j Aura Connection Test - Ready to Execute
=====================================================

Now we have all the connection details needed for testing.
"""

import os
from neo4j import GraphDatabase

def test_complete_aura_connection():
    """Test connection with the actual Aura credentials."""
    
    # Complete connection details
    URI = "neo4j+s://57ed0189.databases.neo4j.io"
    USERNAME = "neo4j"
    PASSWORD = "lOQ5gQFSW2WcCJhfRoJog6mV_ac_z8Gmf6POO-ra-EA"
    
    print("🔍 Testing Neo4j Aura Connection with Actual Credentials")
    print(f"URI: {URI}")
    print(f"Username: {USERNAME}")
    print(f"Password: {'*' * 20}...{PASSWORD[-4:]}")  # Show last 4 chars for verification
    print("-" * 60)
    
    try:
        # Test connection using Neo4j Aura recommended pattern
        with GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD)) as driver:
            # Verify connectivity first
            driver.verify_connectivity()
            print("✅ Driver connectivity verified")
            
            # Test database operations
            with driver.session() as session:
                # Basic connection test
                result = session.run("RETURN 'Neo4j Aura Connected!' as message, datetime() as timestamp")
                record = result.single()
                print(f"✅ Query successful: {record['message']}")
                print(f"📅 Server timestamp: {record['timestamp']}")
                
                # Check database content
                result = session.run("MATCH (n) RETURN count(n) as total_nodes")
                node_count = result.single()["total_nodes"]
                print(f"📊 Current nodes in database: {node_count}")
                
                # Check relationships
                result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
                rel_count = result.single()["total_relationships"]
                print(f"🔗 Current relationships: {rel_count}")
                
                # Get node type breakdown
                result = session.run("""
                    MATCH (n) 
                    RETURN labels(n) as labels, count(n) as count 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                
                print("\n📋 Current Knowledge Graph Content:")
                node_types = list(result)
                if node_types:
                    for record in node_types:
                        labels = record["labels"]
                        count = record["count"]
                        print(f"  • {labels}: {count} nodes")
                else:
                    print("  (No nodes found - empty database)")
                
                # Test write capability
                test_node_id = f"connection_test_{int(__import__('time').time())}"
                session.run("""
                    CREATE (test:ConnectionTest {
                        id: $test_id,
                        message: 'LightRAG connection test',
                        timestamp: datetime()
                    })
                """, test_id=test_node_id)
                print(f"✅ Write test successful: Created test node {test_node_id}")
                
                # Verify test node was created
                result = session.run("""
                    MATCH (test:ConnectionTest {id: $test_id})
                    RETURN test.message as message
                """, test_id=test_node_id)
                
                test_record = result.single()
                if test_record:
                    print(f"✅ Read test successful: {test_record['message']}")
                
                # Cleanup test node
                session.run("MATCH (test:ConnectionTest {id: $test_id}) DELETE test", test_id=test_node_id)
                print("🧹 Test node cleaned up")
        
        print("\n🎉 NEO4J AURA CONNECTION FULLY WORKING!")
        print("✅ Ready to proceed with LightRAG integration")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def create_environment_file():
    """Create .env file with working credentials."""
    
    env_content = """# Disable PWA/Service Worker features in Create React App
GENERATE_SOURCEMAP=false
DISABLE_ESM_NODE_MODULES=false
SKIP_PREFLIGHT_CHECK=true

# Explicitly disable PWA features
REACT_APP_SW_DISABLED=true

# API Configuration
REACT_APP_API_URL=http://localhost:8000

# Neo4j Aura Connection - WORKING CREDENTIALS
NEO4J_URI=neo4j+s://57ed0189.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=lOQ5gQFSW2WcCJhfRoJog6mV_ac_z8Gmf6POO-ra-EA
NEO4J_DATABASE=neo4j

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key_here

# LightRAG Configuration
LIGHTRAG_WORKING_DIR=./rag_storage
"""
    
    try:
        with open('../.env', 'w') as f:
            f.write(env_content)
        print("📄 Updated .env file with working Neo4j credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")
        return False

def set_environment_variables():
    """Set environment variables for immediate use."""
    
    os.environ['NEO4J_URI'] = 'neo4j+s://57ed0189.databases.neo4j.io'
    os.environ['NEO4J_USERNAME'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'lOQ5gQFSW2WcCJhfRoJog6mV_ac_z8Gmf6POO-ra-EA'
    os.environ['NEO4J_DATABASE'] = 'neo4j'
    
    print("✅ Environment variables set for current session")

if __name__ == "__main__":
    print("Line Lead - Neo4j Aura Connection Test")
    print("=" * 60)
    
    # Set environment variables
    set_environment_variables()
    
    # Create .env file
    create_environment_file()
    
    # Test connection
    success = test_complete_aura_connection()
    
    if success:
        print("\n" + "=" * 60)
        print("🚀 READY FOR NEXT PHASE: LIGHTRAG VERSION TESTING")
        print("=" * 60)
        print("\nNext steps:")
        print("1. ✅ Neo4j authentication working")
        print("2. 🧪 Test LightRAG versions for async bug")
        print("3. 🎯 Implement enhanced extraction")
        print("4. 📄 Process QSR documents")
        print("5. 🎉 Achieve 200+ entities target")
    else:
        print("\n❌ Neo4j connection issues need resolution first")