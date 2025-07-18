#!/usr/bin/env python3
"""Check what documents are in the Ragie partition"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv()

async def check_ragie_documents():
    """Check what documents are available in Ragie"""
    
    print("=== Checking Ragie Documents ===")
    
    # Import the Ragie client directly
    from ragie import Ragie
    
    ragie_client = Ragie(auth=os.getenv('RAGIE_API_KEY'))
    
    # List all documents
    print("Fetching document list...")
    try:
        documents = ragie_client.documents.list()
        print(f"Found documents in partition 'qsr_manuals':")
        
        for i, doc in enumerate(documents.documents):
            print(f"  {i+1}. {doc.name} (ID: {doc.id})")
            print(f"     Status: {doc.status}")
            print(f"     Created: {doc.created_at}")
            print()
    except Exception as e:
        print(f"Error fetching documents: {e}")
    
    # Try a simpler search
    print("\n=== Testing Simple Searches ===")
    
    simple_queries = [
        "oven",
        "Baxter",
        "equipment",
        "manual",
        "diagram"
    ]
    
    for query in simple_queries:
        try:
            results = ragie_client.retrievals.retrieve(request={
                "query": query,
                "partition": "qsr_manuals",
                "top_k": 3
            })
            print(f"Query '{query}': {len(results.scored_chunks)} results")
            if results.scored_chunks:
                for chunk in results.scored_chunks[:2]:  # Show first 2
                    print(f"  - Score: {chunk.score:.3f}, Doc: {getattr(chunk, 'document_name', 'unknown')}")
        except Exception as e:
            print(f"Query '{query}' failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_ragie_documents())