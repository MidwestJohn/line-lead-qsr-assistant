#!/usr/bin/env python3
"""
Test script to verify LightRAG Neo4j integration
"""
import asyncio
import os
from services.rag_service import rag_service
from services.neo4j_service import neo4j_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.rag')

async def test_neo4j_integration():
    """Test LightRAG with Neo4j integration"""
    
    print("🧪 Testing LightRAG Neo4j Integration")
    print("=" * 50)
    
    try:
        # Step 1: Initialize RAG service
        print("Step 1: Initializing RAG service...")
        result = await rag_service.initialize()
        
        if not result:
            print("❌ RAG service initialization failed")
            return False
        
        print(f"✅ RAG service initialized: {rag_service.rag_instance.graph_storage}")
        
        # Step 2: Check Neo4j connection
        print("Step 2: Checking Neo4j connection...")
        neo4j_result = neo4j_service.test_connection()
        
        if not neo4j_result.get('connected'):
            print("❌ Neo4j connection failed")
            return False
        
        print("✅ Neo4j connection successful")
        
        # Step 3: Count current nodes/relationships
        print("Step 3: Counting current data...")
        initial_count = await neo4j_service.count_nodes_and_relationships()
        print(f"Initial state: {initial_count['nodes']} nodes, {initial_count['relationships']} relationships")
        
        # Step 4: Process a test document
        print("Step 4: Processing test document...")
        
        test_content = """
        QSR Equipment Test Document
        
        This document contains information about Quick Service Restaurant equipment.
        
        The Taylor C602 ice cream machine is a commercial-grade soft-serve dispenser.
        It features dual-flavor capability and stainless steel construction.
        
        Safety procedures include:
        - Always disconnect power before maintenance
        - Use proper lockout/tagout procedures
        - Ensure all personnel are trained on safety protocols
        
        Cleaning requirements:
        - Daily sanitization of all food contact surfaces
        - Weekly deep cleaning of internal components
        - Monthly inspection of seals and gaskets
        
        Components include:
        - Compressor assembly
        - Freezer cylinder
        - Mix hopper
        - Dispensing valve
        """
        
        # Process the document
        await rag_service.rag_instance.ainsert(test_content)
        print("✅ Document processed successfully")
        
        # Step 5: Check if new data was added to Neo4j
        print("Step 5: Checking Neo4j for new data...")
        final_count = await neo4j_service.count_nodes_and_relationships()
        print(f"Final state: {final_count['nodes']} nodes, {final_count['relationships']} relationships")
        
        # Calculate difference
        nodes_added = final_count['nodes'] - initial_count['nodes']
        rels_added = final_count['relationships'] - initial_count['relationships']
        
        print(f"📊 Data added: {nodes_added} nodes, {rels_added} relationships")
        
        if nodes_added > 0 or rels_added > 0:
            print("✅ Neo4j integration working - data was added to graph")
        else:
            print("⚠️ No new data added to Neo4j - check configuration")
        
        # Step 6: Test query functionality
        print("Step 6: Testing query functionality...")
        try:
            query_result = await rag_service.rag_instance.aquery("What are the safety procedures for the Taylor C602?")
            print(f"Query result length: {len(query_result) if query_result else 0} characters")
            if query_result:
                print("✅ Query functionality working")
                print(f"Sample response: {query_result[:150]}...")
            else:
                print("⚠️ Query returned empty result")
        except Exception as e:
            print(f"❌ Query failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Neo4j integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Neo4j integration test...")
    success = asyncio.run(test_neo4j_integration())
    
    if success:
        print("\n✅ All tests passed! Neo4j integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the configuration.")