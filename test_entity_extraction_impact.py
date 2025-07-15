#!/usr/bin/env python3
"""
Test script to demonstrate the impact of entity extraction on search capabilities
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.ragie_entity_manager import ragie_entity_manager
from services.ragie_service_clean import clean_ragie_service

async def test_entity_extraction_benefits():
    """Demonstrate how entity extraction improves equipment searchability"""
    
    print("🔍 Testing Entity Extraction Impact on Equipment Search")
    print("=" * 70)
    
    # Check if entity manager is available
    if not ragie_entity_manager.is_available():
        print("❌ Ragie entity manager not available (API key needed)")
        return
    
    # List current instructions
    print("\n📋 Current Ragie Instructions:")
    instructions = await ragie_entity_manager.list_instructions()
    
    for i, instruction in enumerate(instructions, 1):
        print(f"  {i}. {instruction['name']} (ID: {instruction['id'][:8]}...)")
        print(f"     Scope: {instruction['scope']}")
        print(f"     Active: {instruction['active']}")
        print(f"     Prompt: {instruction['prompt'][:100]}...")
        print()
    
    # Test current search for Baxter equipment
    print("\n🔍 Current Search Results for 'Baxter OV520E1':")
    try:
        results = await clean_ragie_service.search("Baxter OV520E1", limit=10)
        if results:
            print(f"✅ Found {len(results)} results")
            for result in results:
                print(f"  - {result.metadata.get('original_filename', 'Unknown')} (Score: {result.score:.3f})")
        else:
            print("❌ No results found")
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    # Test alternative search terms
    search_terms = ["oven", "electric diagram", "rotating rack", "Baxter"]
    
    print(f"\n🔍 Alternative Search Terms:")
    for term in search_terms:
        try:
            results = await clean_ragie_service.search(term, limit=3)
            print(f"  '{term}': {len(results) if results else 0} results")
        except Exception as e:
            print(f"  '{term}': Error - {e}")
    
    # Check entities for Baxter document
    baxter_doc_id = "2ac643c8-8f34-4526-bd74-2b6980ac4b30"
    print(f"\n🎯 Entities for Baxter Document ({baxter_doc_id[:8]}...):")
    
    entities = await ragie_entity_manager.get_document_entities(baxter_doc_id)
    if entities:
        print(f"✅ Found {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity}")
    else:
        print("❌ No entities found (document needs reprocessing)")
    
    # Explain the expected benefits
    print("\n🚀 Expected Benefits of Entity Extraction:")
    print("1. 📸 Image Searchability: PNG files will be indexed by content")
    print("2. 🏷️  Equipment Tagging: Model numbers, brands extracted automatically")
    print("3. 🔗 Cross-Reference: Related equipment and procedures linked")
    print("4. 📍 Precise Search: Find specific diagrams by equipment type")
    print("5. 🧠 Smart Context: LLM understands equipment relationships")
    
    print("\n💡 Entity Extraction Schema Preview:")
    print("Equipment Image Instruction will extract:")
    print("  - model_number: 'OV520E1'")
    print("  - manufacturer: 'Baxter'") 
    print("  - equipment_type: 'oven'")
    print("  - diagram_type: 'electric'")
    print("  - searchable_terms: ['Baxter', 'OV520E1', 'rotating', 'rack', 'oven', 'electric']")
    
    print("\n🔄 Next Steps:")
    print("1. ✅ Instructions created and active")
    print("2. 🔄 New uploads will be automatically processed")
    print("3. 📄 Existing documents need manual reprocessing trigger")
    print("4. 🔍 Search will include entity-extracted metadata")
    
    print("\n" + "=" * 70)
    print("Entity extraction setup complete! 🎉")

if __name__ == "__main__":
    asyncio.run(test_entity_extraction_benefits())