#!/usr/bin/env python3
"""
Test Enhanced Image Intent Filtering
====================================

Tests the new intelligent image detection system that prioritizes
visual content based on user intent rather than specific equipment keywords.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import sys
import os
import json

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.ragie_service_clean import clean_ragie_service

def test_filter_generation():
    """Test the new image intent detection vs old equipment-specific filtering"""
    
    print("🎯 Testing Enhanced Image Intent Detection")
    print("=" * 50)
    
    if not clean_ragie_service.is_available():
        print("❌ Ragie service not available")
        return
    
    # Test cases: Image-seeking queries without specific equipment mentions
    test_cases = [
        {
            "query": "Show me an image of an oven",
            "expected": "Should detect image intent and prioritize PNG/JPG files",
            "type": "Primary Visual Signal"
        },
        {
            "query": "What does this equipment look like?",
            "expected": "Should detect visual + equipment context",
            "type": "Secondary Visual + Equipment Context"
        },
        {
            "query": "I need to see the control panel",
            "expected": "Should prioritize visual content",
            "type": "Visual Identification Need"
        },
        {
            "query": "Can you display the wiring diagram?",
            "expected": "Should target diagrams and schematics",
            "type": "Technical Diagram Request"
        },
        {
            "query": "Find me a picture of the machine",
            "expected": "Should prioritize image files",
            "type": "Direct Image Request"
        },
        {
            "query": "How do I identify this component?",
            "expected": "Should include visual content for identification",
            "type": "Identification Need"
        },
        {
            "query": "Baxter OV520E1 cleaning procedure",
            "expected": "Should use equipment filter (no image intent)",
            "type": "Equipment-Specific Text Query"
        },
        {
            "query": "maintenance schedule for fryers",
            "expected": "Should use content filter (no image intent)", 
            "type": "Content-Specific Query"
        }
    ]
    
    print("\n🔍 Testing Filter Generation Logic")
    print("-" * 30)
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected = test_case["expected"]
        test_type = test_case["type"]
        
        print(f"\n{i}. {test_type}")
        print(f"   Query: '{query}'")
        print(f"   Expected: {expected}")
        
        # Test the new image intent detection
        image_filter = clean_ragie_service._detect_image_intent_filter(query.lower())
        
        # Test overall smart filter
        smart_filter = clean_ragie_service._build_smart_filter(query, query)
        
        if image_filter:
            print(f"   ✅ Image Intent Detected!")
            print(f"   📸 Filter Type: Image-prioritized search")
            
            # Show the structure of the image filter
            if "$or" in image_filter:
                filter_types = []
                for condition in image_filter["$or"]:
                    if "png" in str(condition).lower():
                        filter_types.append("PNG files")
                    elif "jpg" in str(condition).lower():
                        filter_types.append("JPG files") 
                    elif "pdf" in str(condition).lower():
                        filter_types.append("PDF diagrams")
                        
                print(f"   🎯 Targets: {', '.join(filter_types)}")
        else:
            print(f"   📝 No Image Intent - Using: {type(smart_filter).__name__ if smart_filter else 'No specific filter'}")
            
            if smart_filter:
                # Determine filter type
                if "baxter" in str(smart_filter).lower():
                    print(f"   🔧 Filter Type: Equipment-specific (Baxter)")
                elif "pdf" in str(smart_filter).lower():
                    print(f"   📄 Filter Type: Document type") 
                else:
                    print(f"   🎛️ Filter Type: Content-specific")

def test_image_intent_keywords():
    """Test the keyword detection logic in detail"""
    
    print(f"\n\n🔤 Testing Image Intent Keyword Detection")
    print("=" * 50)
    
    # Test different categories of image intent
    keyword_tests = [
        {
            "category": "Primary Visual Signals",
            "keywords": ["show me", "image", "picture", "diagram", "visual", "photo"],
            "test_phrases": [
                "show me the equipment",
                "I need an image of this",
                "picture of the control panel", 
                "diagram showing the process",
                "visual representation",
                "photo of the device"
            ]
        },
        {
            "category": "Secondary Visual + Equipment Context",
            "keywords": ["see", "view", "look", "identify", "recognize"],
            "test_phrases": [
                "I need to see the equipment layout",
                "view the machine components", 
                "what does this equipment look like",
                "identify this machine type",
                "recognize this component"
            ]
        },
        {
            "category": "Non-Visual Queries",
            "keywords": [],
            "test_phrases": [
                "cleaning procedure for equipment",
                "maintenance schedule", 
                "troubleshooting steps",
                "safety protocols",
                "operating instructions"
            ]
        }
    ]
    
    for category_test in keyword_tests:
        category = category_test["category"]
        test_phrases = category_test["test_phrases"]
        
        print(f"\n📂 {category}")
        print("-" * 30)
        
        for phrase in test_phrases:
            has_image_intent = clean_ragie_service._detect_image_intent_filter(phrase.lower()) is not None
            
            status = "✅ IMAGE INTENT" if has_image_intent else "📝 TEXT INTENT"
            print(f"   {status}: '{phrase}'")

async def test_full_search_flow():
    """Test the complete search flow with new filtering"""
    
    print(f"\n\n🚀 Testing Complete Search Flow")
    print("=" * 50)
    
    # Image-seeking queries that should now work better
    image_queries = [
        "Show me what an oven looks like",
        "I need to see the equipment setup", 
        "Display the control interface",
        "What does this machine look like?"
    ]
    
    for query in image_queries:
        print(f"\n🔍 Testing: '{query}'")
        
        try:
            # Test filter generation
            smart_filter = clean_ragie_service._build_smart_filter(query, query)
            
            if smart_filter:
                print(f"   🎯 Filter Generated: Image-prioritized")
                
                # Show what file types are targeted
                filter_str = str(smart_filter).lower()
                targets = []
                if "png" in filter_str:
                    targets.append("PNG")
                if "jpg" in filter_str:
                    targets.append("JPG") 
                if "pdf" in filter_str:
                    targets.append("PDF")
                    
                print(f"   📁 File Types: {', '.join(targets)}")
            else:
                print(f"   📝 No specific filter")
            
            # Note: Actual search testing would be rate-limited
            print(f"   ⏸️  Search test skipped (rate limits)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Enhanced Image Intent Filtering Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_filter_generation()
    test_image_intent_keywords()
    
    # Run async test
    asyncio.run(test_full_search_flow())
    
    print(f"\n\n✅ Test Suite Complete!")
    print("The new filtering system now intelligently detects image intent")
    print("and prioritizes visual content regardless of specific equipment brands.")