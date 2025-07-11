#!/usr/bin/env python3
"""
Debug Citation Extraction
=========================

This script helps debug why visual citations aren't being extracted properly.
"""

import sys
import os
sys.path.append('backend')
sys.path.append('backend/services')

import asyncio
from services.multimodal_citation_service import multimodal_citation_service

async def test_citation_extraction():
    """Test the citation extraction process"""
    
    print("🔍 DEBUGGING CITATION EXTRACTION")
    print("=" * 40)
    
    # Test with a simple response and equipment context
    response_text = "For the Taylor C602, ensure that the oil temperature is maintained at a minimum of 350 degrees Fahrenheit for optimal cooking. This temperature helps ensure food safety and quality."
    equipment_context = "Taylor C602"
    
    print(f"Response text: {response_text[:100]}...")
    print(f"Equipment context: {equipment_context}")
    print()
    
    try:
        result = await multimodal_citation_service.extract_citations_from_response(
            response_text, equipment_context
        )
        
        print("✅ Citation extraction completed!")
        print(f"Result keys: {list(result.keys())}")
        print(f"Visual citations: {len(result.get('visual_citations', []))}")
        print(f"Manual references: {len(result.get('manual_references', []))}")
        print(f"Citation count: {result.get('citation_count', 0)}")
        
        if result.get('visual_citations'):
            print("\n📸 Visual Citations:")
            for i, citation in enumerate(result['visual_citations'], 1):
                print(f"  {i}. Type: {citation.get('type', 'unknown')}")
                print(f"     Reference: {citation.get('reference', 'no ref')}")
                print(f"     Source: {citation.get('source_document', 'unknown')}")
                print(f"     Page: {citation.get('page_number', '?')}")
        
        if result.get('manual_references'):
            print("\n📚 Manual References:")
            for i, ref in enumerate(result['manual_references'], 1):
                print(f"  {i}. Document: {ref.get('document', 'unknown')}")
                print(f"     Page: {ref.get('page', '?')}")
                print(f"     Section: {ref.get('section', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Citation extraction failed: {e}")
        import traceback
        traceback.print_exc()

async def test_document_availability():
    """Check what documents are available for citation extraction"""
    
    print("\n🗂️ DOCUMENT AVAILABILITY CHECK")
    print("=" * 40)
    
    # Check uploaded documents
    docs_dir = "uploaded_docs"
    if os.path.exists(docs_dir):
        docs = os.listdir(docs_dir)
        print(f"Documents in {docs_dir}: {len(docs)}")
        for doc in docs:
            print(f"  - {doc}")
    else:
        print(f"❌ {docs_dir} directory not found")
    
    # Check if multimodal citation service has access
    print(f"\nCitation service documents path: {multimodal_citation_service.documents_path}")
    if hasattr(multimodal_citation_service, 'citation_cache'):
        print(f"Citation cache: {len(multimodal_citation_service.citation_cache)} documents")
        for doc_path in multimodal_citation_service.citation_cache.keys():
            print(f"  - {doc_path}")

async def test_simple_citation_creation():
    """Test creating a simple citation without image extraction"""
    
    print("\n🧪 SIMPLE CITATION CREATION TEST")
    print("=" * 40)
    
    try:
        # Create a simple manual reference without image content
        manual_ref = {
            "document": "Taylor C602 Manual",
            "page": 15,
            "section": "Temperature Guidelines",
            "content_preview": "Oil temperature should be maintained at 350°F"
        }
        
        simple_result = {
            "visual_citations": [],
            "manual_references": [manual_ref],
            "citation_count": 1
        }
        
        print(f"✅ Simple citation created:")
        print(f"   Document: {manual_ref['document']}")
        print(f"   Page: {manual_ref['page']}")
        print(f"   Section: {manual_ref['section']}")
        
        return simple_result
        
    except Exception as e:
        print(f"❌ Simple citation creation failed: {e}")
        return None

async def main():
    """Run all debug tests"""
    
    await test_document_availability()
    await test_citation_extraction()
    simple_result = await test_simple_citation_creation()
    
    print("\n📋 RECOMMENDATIONS")
    print("=" * 40)
    
    if simple_result:
        print("✅ Basic citation structure works")
        print("🔧 Issue is likely in PDF image extraction")
        print("💡 Consider returning text-based citations as fallback")
    else:
        print("❌ Basic citation creation failed")
        print("🔧 Issue is in core citation service logic")

if __name__ == "__main__":
    asyncio.run(main())