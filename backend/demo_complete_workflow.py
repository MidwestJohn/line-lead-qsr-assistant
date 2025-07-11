#!/usr/bin/env python3
"""
Complete LightRAG → Neo4j Workflow Demo
======================================

Demonstrates the complete workflow from document to Neo4j graph:
1. Create sample QSR documents
2. Extract with any working GraphRAG tool (simulated)
3. Bridge to Neo4j with reliability features
4. Verify results

Author: Generated with Memex (https://memex.tech)
"""

import json
import time
import logging
from pathlib import Path
from lightrag_neo4j_bridge import LightRAGNeo4jBridge
from services.neo4j_service import neo4j_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_comprehensive_qsr_data():
    """Create comprehensive QSR knowledge graph data."""
    
    # Enhanced QSR entities with more realistic data
    entities = [
        # Equipment
        {
            "name": "Taylor C602 Ice Cream Machine",
            "type": "EQUIPMENT",
            "description": "Commercial soft-serve ice cream machine",
            "manufacturer": "Taylor",
            "model": "C602",
            "capacity": "2 flavors + mix",
            "location": "Dessert Station",
            "installation_date": "2024-01-15",
            "maintenance_schedule": "weekly"
        },
        {
            "name": "Frymaster Deep Fryer",
            "type": "EQUIPMENT", 
            "description": "Commercial deep fryer for french fries and chicken",
            "manufacturer": "Frymaster",
            "model": "FM-2000",
            "capacity": "40 lbs oil",
            "location": "Fry Station",
            "temperature_range": "325-375°F"
        },
        {
            "name": "Beverage Dispenser",
            "type": "EQUIPMENT",
            "description": "Multi-flavor beverage dispensing system",
            "manufacturer": "Coca-Cola",
            "model": "Freestyle 7100",
            "capacity": "100+ flavors",
            "location": "Beverage Station"
        },
        
        # Maintenance Procedures
        {
            "name": "Daily Ice Cream Machine Cleaning",
            "type": "MAINTENANCE",
            "description": "Daily cleaning and sanitization of ice cream machine",
            "frequency": "daily",
            "duration": "30 minutes",
            "priority": "high",
            "steps": "disassemble, clean, sanitize, reassemble"
        },
        {
            "name": "Fryer Oil Change",
            "type": "MAINTENANCE",
            "description": "Replace fryer oil and clean fryer components",
            "frequency": "weekly",
            "duration": "45 minutes",
            "priority": "medium",
            "safety_requirement": "allow cooling to 200°F"
        },
        {
            "name": "Beverage Line Cleaning",
            "type": "MAINTENANCE",
            "description": "Clean beverage dispensing lines and nozzles",
            "frequency": "weekly",
            "duration": "20 minutes",
            "priority": "high"
        },
        
        # Safety Requirements
        {
            "name": "Heat Resistant Gloves",
            "type": "SAFETY",
            "description": "Insulated gloves for handling hot equipment",
            "ppe_type": "gloves",
            "temperature_rating": "500°F",
            "required_for": "fryer maintenance"
        },
        {
            "name": "Safety Goggles",
            "type": "SAFETY",
            "description": "Eye protection for chemical cleaning",
            "ppe_type": "eye protection",
            "required_for": "sanitization procedures"
        },
        {
            "name": "Non-Slip Shoes",
            "type": "SAFETY",
            "description": "Slip-resistant footwear for kitchen work",
            "ppe_type": "footwear",
            "required_for": "all kitchen operations"
        },
        
        # Parameters & Specifications
        {
            "name": "Ice Cream Serving Temperature",
            "type": "PARAMETER",
            "description": "Optimal temperature for ice cream dispensing",
            "value": "18-22°F",
            "unit": "fahrenheit",
            "equipment": "Taylor C602"
        },
        {
            "name": "Fryer Oil Temperature",
            "type": "PARAMETER",
            "description": "Optimal oil temperature for frying",
            "value": "350°F",
            "unit": "fahrenheit",
            "equipment": "Frymaster Deep Fryer"
        },
        {
            "name": "Beverage Syrup Ratio",
            "type": "PARAMETER",
            "description": "Syrup to water ratio for beverages",
            "value": "1:5",
            "unit": "ratio",
            "equipment": "Beverage Dispenser"
        },
        
        # Ingredients & Supplies
        {
            "name": "Ice Cream Mix",
            "type": "INGREDIENT",
            "description": "Liquid ice cream base for machine",
            "supplier": "Dairy Fresh",
            "shelf_life": "14 days",
            "storage_temp": "35-40°F"
        },
        {
            "name": "Fryer Oil",
            "type": "INGREDIENT",
            "description": "High-temperature cooking oil",
            "supplier": "Restaurant Supply Co",
            "type_detail": "Canola oil",
            "shelf_life": "6 months unopened"
        },
        {
            "name": "Sanitizer Solution",
            "type": "INGREDIENT",
            "description": "Food-safe sanitizing chemical",
            "supplier": "Clean Solutions",
            "concentration": "200 ppm",
            "usage": "equipment sanitization"
        },
        
        # Procedures & Workflows
        {
            "name": "Opening Checklist",
            "type": "PROCEDURE",
            "description": "Daily opening procedures for restaurant",
            "duration": "60 minutes",
            "priority": "critical",
            "steps": "equipment check, temperature verification, supply inventory"
        },
        {
            "name": "Closing Checklist",
            "type": "PROCEDURE",
            "description": "Daily closing procedures for restaurant",
            "duration": "90 minutes",
            "priority": "critical",
            "steps": "equipment cleaning, sanitization, inventory count"
        }
    ]
    
    # Enhanced relationships with more context
    relationships = [
        # Equipment-Maintenance relationships
        {
            "source": "Taylor C602 Ice Cream Machine",
            "target": "Daily Ice Cream Machine Cleaning",
            "type": "REQUIRES",
            "description": "Ice cream machine requires daily cleaning for food safety",
            "frequency": "daily",
            "compliance": "FDA required"
        },
        {
            "source": "Frymaster Deep Fryer",
            "target": "Fryer Oil Change",
            "type": "REQUIRES",
            "description": "Deep fryer requires regular oil changes for quality",
            "frequency": "weekly",
            "quality_impact": "high"
        },
        {
            "source": "Beverage Dispenser",
            "target": "Beverage Line Cleaning",
            "type": "REQUIRES",
            "description": "Beverage dispenser requires line cleaning to prevent contamination",
            "frequency": "weekly",
            "compliance": "health department required"
        },
        
        # Safety relationships
        {
            "source": "Fryer Oil Change",
            "target": "Heat Resistant Gloves",
            "type": "REQUIRES",
            "description": "Fryer maintenance requires heat-resistant gloves for safety",
            "safety_level": "critical",
            "injury_prevention": "burns"
        },
        {
            "source": "Daily Ice Cream Machine Cleaning",
            "target": "Safety Goggles",
            "type": "REQUIRES",
            "description": "Chemical cleaning requires eye protection",
            "safety_level": "high",
            "injury_prevention": "chemical splash"
        },
        {
            "source": "Opening Checklist",
            "target": "Non-Slip Shoes",
            "type": "REQUIRES",
            "description": "All kitchen operations require non-slip footwear",
            "safety_level": "high",
            "injury_prevention": "slips and falls"
        },
        
        # Parameter relationships
        {
            "source": "Taylor C602 Ice Cream Machine",
            "target": "Ice Cream Serving Temperature",
            "type": "OPERATES_AT",
            "description": "Ice cream machine operates at specific temperature for quality",
            "quality_impact": "critical",
            "customer_satisfaction": "high"
        },
        {
            "source": "Frymaster Deep Fryer",
            "target": "Fryer Oil Temperature",
            "type": "OPERATES_AT",
            "description": "Deep fryer operates at specific temperature for food safety",
            "safety_impact": "high",
            "quality_impact": "high"
        },
        {
            "source": "Beverage Dispenser",
            "target": "Beverage Syrup Ratio",
            "type": "OPERATES_AT",
            "description": "Beverage dispenser uses specific syrup ratio for taste",
            "quality_impact": "high",
            "cost_impact": "medium"
        },
        
        # Supply relationships
        {
            "source": "Taylor C602 Ice Cream Machine",
            "target": "Ice Cream Mix",
            "type": "USES",
            "description": "Ice cream machine uses liquid mix to create soft serve",
            "consumption_rate": "5 gallons/day",
            "cost_impact": "high"
        },
        {
            "source": "Frymaster Deep Fryer",
            "target": "Fryer Oil",
            "type": "USES",
            "description": "Deep fryer uses oil for cooking french fries and chicken",
            "consumption_rate": "40 lbs/week",
            "cost_impact": "medium"
        },
        {
            "source": "Daily Ice Cream Machine Cleaning",
            "target": "Sanitizer Solution",
            "type": "USES",
            "description": "Cleaning procedure uses sanitizer for food safety",
            "consumption_rate": "1 cup/day",
            "safety_impact": "critical"
        },
        
        # Procedure relationships
        {
            "source": "Opening Checklist",
            "target": "Taylor C602 Ice Cream Machine",
            "type": "INCLUDES",
            "description": "Opening checklist includes ice cream machine startup",
            "step_order": "3",
            "time_allocation": "10 minutes"
        },
        {
            "source": "Opening Checklist",
            "target": "Frymaster Deep Fryer",
            "type": "INCLUDES",
            "description": "Opening checklist includes fryer startup and oil check",
            "step_order": "2",
            "time_allocation": "15 minutes"
        },
        {
            "source": "Closing Checklist",
            "target": "Daily Ice Cream Machine Cleaning",
            "type": "INCLUDES",
            "description": "Closing checklist includes ice cream machine cleaning",
            "step_order": "1",
            "time_allocation": "30 minutes"
        },
        
        # Cross-equipment relationships
        {
            "source": "Ice Cream Serving Temperature",
            "target": "Fryer Oil Temperature",
            "type": "TEMPERATURE_CONTRAST",
            "description": "Temperature differential between cold and hot equipment",
            "safety_consideration": "thermal shock prevention",
            "workflow_impact": "staff movement planning"
        },
        {
            "source": "Heat Resistant Gloves",
            "target": "Safety Goggles",
            "type": "COMBINED_PPE",
            "description": "Both PPE items used together for comprehensive protection",
            "usage_scenario": "hot oil maintenance with chemicals",
            "safety_level": "maximum"
        }
    ]
    
    return entities, relationships

def simulate_graph_extraction():
    """Simulate GraphRAG extraction (normally done by LightRAG or similar)."""
    
    logger.info("🔄 Simulating GraphRAG extraction...")
    
    # Create comprehensive QSR data
    entities, relationships = create_comprehensive_qsr_data()
    
    # Save to JSON files (simulating LightRAG output)
    with open("qsr_entities.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    
    with open("qsr_relationships.json", "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ GraphRAG extraction complete:")
    logger.info(f"   - Entities: {len(entities)}")
    logger.info(f"   - Relationships: {len(relationships)}")
    
    return entities, relationships

def run_reliable_bridge():
    """Run the reliable Neo4j bridge."""
    
    logger.info("🌉 Starting reliable Neo4j bridge...")
    
    # Create bridge instance
    bridge = LightRAGNeo4jBridge(
        entities_file="qsr_entities.json",
        relationships_file="qsr_relationships.json",
        batch_size=10,  # Smaller batches for demo
        checkpoint_file="qsr_checkpoint.json"
    )
    
    # Run the bridge
    result = bridge.run_bridge()
    
    if result["success"]:
        logger.info("✅ Bridge completed successfully!")
        logger.info(f"📊 Results:")
        logger.info(f"   - Entities processed: {result['entities_processed']}")
        logger.info(f"   - Relationships processed: {result['relationships_processed']}")
        logger.info(f"   - Entities failed: {result['entities_failed']}")
        logger.info(f"   - Relationships failed: {result['relationships_failed']}")
        
        if "summary" in result:
            summary = result["summary"]
            logger.info(f"📈 Performance:")
            logger.info(f"   - Processing rate: {summary['entities']['rate_per_second']:.2f} entities/sec")
            logger.info(f"   - Total time: {summary['elapsed_seconds']:.2f} seconds")
    else:
        logger.error(f"❌ Bridge failed: {result['error']}")
        return False
    
    return True

def verify_neo4j_results():
    """Verify the results in Neo4j."""
    
    logger.info("🔍 Verifying Neo4j results...")
    
    if not neo4j_service.connect():
        logger.error("❌ Could not connect to Neo4j for verification")
        return False
    
    try:
        # Get overall statistics
        stats = neo4j_service.execute_query("MATCH (n) RETURN count(n) as total_nodes")
        total_nodes = stats['records'][0]['total_nodes']
        
        rel_stats = neo4j_service.execute_query("MATCH ()-[r]-() RETURN count(r) as total_relationships")
        total_relationships = rel_stats['records'][0]['total_relationships']
        
        logger.info(f"📊 Graph Statistics:")
        logger.info(f"   - Total nodes: {total_nodes}")
        logger.info(f"   - Total relationships: {total_relationships}")
        
        # Get node type distribution
        type_stats = neo4j_service.execute_query("""
            MATCH (n) 
            WHERE n.type IS NOT NULL
            RETURN n.type as node_type, count(n) as count
            ORDER BY count DESC
        """)
        
        logger.info(f"📈 Node Type Distribution:")
        for record in type_stats['records']:
            logger.info(f"   - {record['node_type']}: {record['count']}")
        
        # Get relationship type distribution
        rel_type_stats = neo4j_service.execute_query("""
            MATCH ()-[r]->() 
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        logger.info(f"🔗 Top Relationship Types:")
        for record in rel_type_stats['records']:
            logger.info(f"   - {record['rel_type']}: {record['count']}")
        
        # Sample some QSR entities
        sample_entities = neo4j_service.execute_query("""
            MATCH (n)
            WHERE n.type IN ['EQUIPMENT', 'MAINTENANCE', 'SAFETY']
            RETURN n.name as name, n.type as type, n.description as description
            LIMIT 5
        """)
        
        logger.info(f"🔧 Sample QSR Entities:")
        for record in sample_entities['records']:
            logger.info(f"   - {record['name']} ({record['type']})")
            logger.info(f"     Description: {record['description']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying results: {e}")
        return False

def demo_complete_workflow():
    """Run the complete workflow demo."""
    
    print("🎯 LightRAG → Neo4j Complete Workflow Demo")
    print("=" * 60)
    
    # Step 1: Simulate GraphRAG extraction
    print("\n📖 Step 1: Document Processing & GraphRAG Extraction")
    entities, relationships = simulate_graph_extraction()
    
    # Wait a moment for dramatic effect
    time.sleep(1)
    
    # Step 2: Bridge to Neo4j
    print("\n🌉 Step 2: Reliable Bridge to Neo4j")
    if not run_reliable_bridge():
        print("❌ Bridge failed - stopping demo")
        return False
    
    # Wait a moment
    time.sleep(1)
    
    # Step 3: Verify results
    print("\n🔍 Step 3: Verification & Analysis")
    if not verify_neo4j_results():
        print("❌ Verification failed")
        return False
    
    # Summary
    print("\n🎉 Demo Complete!")
    print("=" * 60)
    print("✅ Successfully demonstrated:")
    print("   - GraphRAG extraction (simulated)")
    print("   - Reliable Neo4j bridge with enterprise features")
    print("   - Comprehensive QSR knowledge graph")
    print("   - Data verification and analysis")
    print(f"   - {len(entities)} entities and {len(relationships)} relationships processed")
    
    print("\n🚀 Next Steps:")
    print("   - Replace simulated extraction with real LightRAG (once fixed)")
    print("   - Process actual QSR manuals and documents")
    print("   - Scale up to hundreds of entities and relationships")
    print("   - Integrate with frontend for user queries")
    
    return True

if __name__ == "__main__":
    success = demo_complete_workflow()
    
    if success:
        print("\n🏆 Demo completed successfully!")
    else:
        print("\n💥 Demo failed!")