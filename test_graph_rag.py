#!/usr/bin/env python3
"""
Test Graph RAG implementation with existing QSR documents
Validates entity extraction and knowledge graph construction
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from graph_rag_service import graph_rag_service, initialize_graph_rag_with_documents

def load_documents():
    """Load documents from documents.json"""
    try:
        with open('documents.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading documents: {e}")
        return {}

def test_entity_extraction():
    """Test entity extraction for common QSR queries"""
    test_queries = [
        "How do I clean the ice cream machine?",
        "What's wrong with the fryer temperature?",
        "Ice machine not making ice",
        "Grill cleaning procedure",
        "Dishwasher maintenance steps",
        "Taylor ice cream machine troubleshooting",
        "Change the oil in the fryer"
    ]
    
    print("\n🔍 Testing Entity Extraction:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        entities = graph_rag_service.extract_entities_from_query(query)
        
        if entities:
            for entity_info in entities:
                print(f"  - {entity_info['entity']} ({entity_info['type']}) - {entity_info['confidence']:.2f}")
        else:
            print("  - No entities extracted")

def test_disambiguation():
    """Test entity disambiguation, especially ice cream machine vs ice machine"""
    print("\n🧠 Testing Entity Disambiguation:")
    print("=" * 50)
    
    test_cases = [
        {
            "query": "ice cream machine cleaning",
            "candidates": ["ice machine", "ice cream machine"],
            "expected": "ice cream machine"
        },
        {
            "query": "ice machine not working", 
            "candidates": ["ice machine", "ice cream machine"],
            "expected": "ice machine"
        },
        {
            "query": "soft serve machine maintenance",
            "candidates": ["ice machine", "ice cream machine"],
            "expected": "ice cream machine"
        }
    ]
    
    for case in test_cases:
        result = graph_rag_service.disambiguate_entity(
            case["query"], 
            case["candidates"]
        )
        status = "✅" if result == case["expected"] else "❌"
        print(f"{status} '{case['query']}' -> '{result}' (expected: '{case['expected']}')")

def test_knowledge_graph_queries():
    """Test knowledge graph querying"""
    print("\n📊 Testing Knowledge Graph Queries:")
    print("=" * 50)
    
    test_queries = [
        "What equipment needs daily cleaning?",
        "Show me Taylor ice cream machine procedures",
        "What are the safety requirements for fryer maintenance?",
        "How often should I change fryer oil?",
        "What components does a commercial grill have?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        start_time = time.time()
        result = graph_rag_service.query_knowledge_graph(query)
        end_time = time.time()
        
        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            print(f"  ⏱️  Response time: {end_time - start_time:.2f}s")
            print(f"  📝 Response: {result['response'][:200]}...")
            if result.get('entities_mentioned'):
                print(f"  🏷️  Entities: {[e['entity'] for e in result['entities_mentioned'][:3]]}")

def test_statistics():
    """Test Graph RAG statistics and health"""
    print("\n📈 Graph RAG Statistics:")
    print("=" * 50)
    
    stats = graph_rag_service.get_statistics()
    
    if "error" in stats:
        print(f"❌ Error getting statistics: {stats['error']}")
        return
    
    print(f"📄 Documents processed: {stats.get('documents_processed', 0)}")
    print(f"🏷️  Total entities cached: {stats.get('entities_cached', 0)}")
    print(f"🔗 Knowledge triplets: {stats.get('knowledge_triplets', 0)}")
    print(f"🎯 Graph initialized: {stats.get('graph_initialized', False)}")
    
    print("\n📊 Entities by type:")
    entities_by_type = stats.get('entities_by_type', {})
    for entity_type, count in entities_by_type.items():
        if count > 0:
            print(f"  - {entity_type}: {count}")

def main():
    """Main test function"""
    print("🚀 Graph RAG Implementation Test")
    print("=" * 50)
    
    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set. Please set your OpenAI API key.")
        sys.exit(1)
    
    # Load documents
    print("📚 Loading documents...")
    documents = load_documents()
    
    if not documents:
        print("❌ No documents found in documents.json")
        sys.exit(1)
    
    print(f"✅ Loaded {len(documents)} documents")
    
    # Initialize Graph RAG
    print("\n🔧 Initializing Graph RAG...")
    start_time = time.time()
    
    success = initialize_graph_rag_with_documents(documents)
    
    end_time = time.time()
    
    if not success:
        print("❌ Failed to initialize Graph RAG")
        sys.exit(1)
    
    print(f"✅ Graph RAG initialized in {end_time - start_time:.2f}s")
    
    # Run tests
    test_statistics()
    test_entity_extraction()
    test_disambiguation()
    test_knowledge_graph_queries()
    
    print(f"\n🎉 Graph RAG tests completed!")
    print("\nNext steps:")
    print("1. Review entity extraction accuracy")
    print("2. Test ice cream machine vs ice machine disambiguation")
    print("3. Validate knowledge graph query responses")
    print("4. Integrate with voice_agent.py")

if __name__ == "__main__":
    main()