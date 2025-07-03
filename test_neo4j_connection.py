#!/usr/bin/env python3
"""
Test Neo4j connection for RAG-Anything setup
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_neo4j_basic():
    """Test basic Neo4j connection without our services"""
    print("🔧 Testing basic Neo4j connection...")
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
        username = os.getenv('NEO4J_USERNAME', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'password123')
        
        print(f"Connecting to: {uri}")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password)}")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        
        # Test a simple query
        with driver.session() as session:
            result = session.run("RETURN 'Hello Neo4j!' as message")
            record = result.single()
            print(f"✅ Neo4j Response: {record['message']}")
        
        driver.close()
        return True
        
    except ImportError:
        print("❌ Neo4j Python driver not installed")
        print("Install with: pip install neo4j")
        return False
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if Neo4j is running")
        print("2. Verify connection details")
        print("3. Check firewall settings")
        return False

def test_rag_service_health():
    """Test our RAG service health check"""
    print("\n🔧 Testing RAG service health...")
    
    try:
        from services.rag_service import rag_service
        
        # Check health without initialization
        health = rag_service.health_check()
        print(f"RAG Service Status: {health}")
        
        if health.get('neo4j_available'):
            print("✅ Neo4j detected by RAG service")
        else:
            print("❌ Neo4j not detected by RAG service")
            
        return health.get('neo4j_available', False)
        
    except Exception as e:
        print(f"❌ RAG service test failed: {e}")
        return False

def test_rag_service_initialization():
    """Test RAG service initialization"""
    print("\n🔧 Testing RAG service initialization...")
    
    try:
        from services.rag_service import rag_service
        import asyncio
        
        async def init_test():
            # Enable RAG for testing
            original_enabled = rag_service.enabled
            rag_service.enabled = True
            
            try:
                result = await rag_service.initialize()
                if result:
                    print("✅ RAG service initialized successfully!")
                    
                    # Test a simple operation
                    health = rag_service.health_check()
                    print(f"Final status: {health}")
                    
                else:
                    print("❌ RAG service initialization failed")
                    
                return result
                
            finally:
                # Restore original setting
                rag_service.enabled = original_enabled
        
        return asyncio.run(init_test())
        
    except ImportError as e:
        print(f"❌ Missing RAG dependencies: {e}")
        print("Note: RAG-Anything packages not installed - this is expected")
        return False
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        return False

def setup_environment():
    """Guide user through environment setup"""
    print("🔧 Environment Setup Check...")
    
    required_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {missing_vars}")
        print("\nSet them with:")
        for var in missing_vars:
            if var == 'NEO4J_URI':
                print(f"export {var}=neo4j://localhost:7687")
            elif var == 'NEO4J_USERNAME':
                print(f"export {var}=neo4j")
            elif var == 'NEO4J_PASSWORD':
                print(f"export {var}=password123")
        
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 Neo4j Connection Test for RAG-Anything")
    print("=" * 50)
    
    # Check environment
    if not setup_environment():
        print("\n❌ Environment setup incomplete")
        return
    
    # Test basic Neo4j connection
    neo4j_works = test_neo4j_basic()
    
    # Test RAG service health
    rag_health_works = test_rag_service_health()
    
    # Test RAG service initialization (if packages available)
    rag_init_works = test_rag_service_initialization()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Neo4j Basic Connection: {'✅' if neo4j_works else '❌'}")
    print(f"RAG Service Health: {'✅' if rag_health_works else '❌'}")
    print(f"RAG Service Init: {'✅' if rag_init_works else '❌ (expected if packages not installed)'}")
    
    if neo4j_works and rag_health_works:
        print("\n🎉 Neo4j is ready for RAG-Anything!")
        print("\nNext steps:")
        print("1. Install RAG-Anything packages:")
        print("   pip install raganything lightrag-hku")
        print("2. Enable RAG-Anything:")
        print("   export USE_RAG_ANYTHING=true")
        print("3. Test the full pipeline!")
    else:
        print("\n❌ Setup needs attention. Check the errors above.")

if __name__ == "__main__":
    main()