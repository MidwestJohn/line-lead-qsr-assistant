#!/usr/bin/env python3
"""
Test LightRAG with Neo4j directly to see if it populates the database
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(dotenv_path='.env.rag')

# Set Neo4j environment variables
os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', '')
os.environ['NEO4J_USERNAME'] = os.getenv('NEO4J_USERNAME', '')  
os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD', '')

print(f"Neo4j URI: {os.getenv('NEO4J_URI')}")
print(f"Neo4j Username: {os.getenv('NEO4J_USERNAME')}")

async def test_lightrag_neo4j():
    """Test LightRAG with Neo4j storage directly."""
    
    from lightrag import LightRAG
    from lightrag.llm.openai import openai_complete_if_cache, openai_embed
    from lightrag.utils import EmbeddingFunc
    
    # Create LightRAG with Neo4j storage
    rag = LightRAG(
        working_dir="./test_neo4j_storage",
        llm_model_func=openai_complete_if_cache,
        llm_model_name="gpt-4o-mini",
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=8192,
            func=lambda texts: openai_embed(texts, model="text-embedding-3-small")
        ),
        graph_storage="Neo4JStorage"  # This should use Neo4j
    )
    
    print("LightRAG initialized with Neo4JStorage")
    
    # Insert test content
    test_content = """
    The Taylor C602 ice cream machine contains a compressor component.
    The compressor requires daily maintenance procedures.
    Safety warnings apply to the mix pump operation.
    The cleaning procedure involves three steps.
    """
    
    print("Inserting test content...")
    await rag.ainsert(test_content)
    print("Content inserted successfully")
    
    # Check what was created
    print("\nChecking storage locations...")
    
    # Check local storage
    local_path = Path("./test_neo4j_storage")
    if local_path.exists():
        files = list(local_path.rglob("*"))
        print(f"Local files created: {len(files)}")
        for f in files[:5]:  # Show first 5 files
            print(f"  {f}")
    
    # Check Neo4j (we'll need to query it separately)
    print("\nTo check Neo4j, run:")
    print("  MATCH (n) RETURN count(n) as nodes")
    print("  MATCH ()-[r]->() RETURN count(r) as relationships")

if __name__ == "__main__":
    asyncio.run(test_lightrag_neo4j())