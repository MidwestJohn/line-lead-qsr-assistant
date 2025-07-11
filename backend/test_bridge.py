#!/usr/bin/env python3
"""
Test script for LightRAG → Neo4j Bridge
"""

import json
import os
from pathlib import Path
from lightrag_neo4j_bridge import LightRAGNeo4jBridge

def create_sample_data():
    """Create sample LightRAG JSON data for testing"""
    
    # Sample entities data
    entities = [
        {
            "name": "French Fry Station",
            "type": "EQUIPMENT",
            "description": "Deep fryer station for cooking french fries",
            "location": "Kitchen Area A",
            "model": "FRY-2000X",
            "capacity": "30 lbs"
        },
        {
            "name": "Daily Cleaning",
            "type": "MAINTENANCE",
            "description": "Daily cleaning procedure for kitchen equipment",
            "frequency": "daily",
            "duration": "15 minutes"
        },
        {
            "name": "Oil Temperature",
            "type": "PARAMETER",
            "description": "Optimal oil temperature for frying",
            "value": "350°F",
            "unit": "fahrenheit"
        },
        {
            "name": "Safety Gloves",
            "type": "SAFETY",
            "description": "Heat-resistant gloves for hot oil handling",
            "ppe_type": "gloves",
            "required": True
        },
        {
            "name": "Fry Basket",
            "type": "EQUIPMENT",
            "description": "Wire basket for holding fries during cooking",
            "material": "stainless steel",
            "capacity": "2 lbs"
        }
    ]
    
    # Sample relationships data
    relationships = [
        {
            "source": "French Fry Station",
            "target": "Daily Cleaning",
            "type": "REQUIRES",
            "description": "French fry station requires daily cleaning"
        },
        {
            "source": "French Fry Station",
            "target": "Oil Temperature",
            "type": "OPERATES_AT",
            "description": "French fry station operates at specific oil temperature"
        },
        {
            "source": "Daily Cleaning",
            "target": "Safety Gloves",
            "type": "REQUIRES",
            "description": "Daily cleaning requires safety gloves"
        },
        {
            "source": "French Fry Station",
            "target": "Fry Basket",
            "type": "USES",
            "description": "French fry station uses fry basket for cooking"
        },
        {
            "source": "Oil Temperature",
            "target": "Safety Gloves",
            "type": "SAFETY_REQUIRES",
            "description": "High oil temperature requires safety gloves"
        }
    ]
    
    # Write sample data to files
    with open("test_entities.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    
    with open("test_relationships.json", "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=2, ensure_ascii=False)
    
    print("✅ Sample data created:")
    print(f"   - test_entities.json: {len(entities)} entities")
    print(f"   - test_relationships.json: {len(relationships)} relationships")
    
    return entities, relationships

def test_bridge():
    """Test the LightRAG → Neo4j Bridge"""
    
    print("🧪 Testing LightRAG → Neo4j Bridge")
    print("=" * 50)
    
    # Create sample data
    entities, relationships = create_sample_data()
    
    # Create bridge instance with small batch size for testing
    bridge = LightRAGNeo4jBridge(
        entities_file="test_entities.json",
        relationships_file="test_relationships.json",
        batch_size=2,  # Small batch size for testing
        checkpoint_file="test_checkpoint.json"
    )
    
    # Run the bridge
    result = bridge.run_bridge()
    
    # Print results
    if result["success"]:
        print("\n✅ Bridge test completed successfully!")
        print(f"📊 Results:")
        print(f"   - Entities processed: {result['entities_processed']}")
        print(f"   - Relationships processed: {result['relationships_processed']}")
        print(f"   - Entities failed: {result['entities_failed']}")
        print(f"   - Relationships failed: {result['relationships_failed']}")
        
        if "summary" in result:
            summary = result["summary"]
            print(f"\n📈 Performance:")
            print(f"   - Entities rate: {summary['entities']['rate_per_second']:.2f} per second")
            print(f"   - Relationships rate: {summary['relationships']['rate_per_second']:.2f} per second")
            print(f"   - Total time: {summary['elapsed_seconds']:.2f} seconds")
    else:
        print(f"\n❌ Bridge test failed: {result['error']}")
    
    return result

if __name__ == "__main__":
    test_bridge()