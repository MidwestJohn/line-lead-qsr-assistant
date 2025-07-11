#!/usr/bin/env python3
"""
Test Enhanced System - Create test document and verify structure
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime
import uuid

# Local imports
from services.neo4j_service import Neo4jService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestEnhancedSystem:
    """Test the enhanced system with clean data"""
    
    def __init__(self):
        self.neo4j_service = Neo4jService()
        
    async def test_complete_system(self):
        """Test the complete enhanced system"""
        
        logger.info("🧪 Testing Enhanced Document Context Integration System")
        
        try:
            # 1. Connect to Neo4j
            connected = self.neo4j_service.connect()
            if connected:
                logger.info("✅ Connected to Neo4j")
            else:
                raise Exception("Failed to connect to Neo4j")
            
            # 2. Create test document with hierarchical structure
            test_results = await self.create_test_document_structure()
            
            # 3. Verify the structure
            verification_results = await self.verify_hierarchical_structure()
            
            # 4. Test context-aware queries
            query_results = await self.test_context_queries()
            
            return {
                "status": "success",
                "test_results": test_results,
                "verification_results": verification_results,
                "query_results": query_results
            }
            
        except Exception as e:
            logger.error(f"System test failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def create_test_document_structure(self):
        """Create a test document with proper hierarchical structure"""
        
        logger.info("📄 Creating test document structure...")
        
        # Test document data
        document_id = str(uuid.uuid4())
        
        # Create Document node
        document_node = {
            "document_id": document_id,
            "filename": "Taylor_C602_Service_Manual.pdf",
            "document_type": "service_manual",
            "qsr_category": "ice_cream", 
            "target_audience": "line_leads",
            "brand_context": "McDonald's",
            "equipment_focus": "Taylor C602 Soft Serve Machine",
            "purpose": "Comprehensive service and maintenance manual for Taylor C602 soft serve ice cream equipment",
            "executive_summary": "Service manual for McDonald's Taylor C602 ice cream machine covering daily maintenance, cleaning procedures, and troubleshooting for QSR line leads.",
            "key_procedures": ["Daily Cleaning", "Heat Treatment", "Troubleshooting", "Parts Replacement"],
            "safety_protocols": ["Hot Surface Warning", "Chemical Safety", "Electrical Safety"],
            "critical_temperatures": ["Heat Treatment: 180°F", "Serving Temperature: 36-38°F"],
            "maintenance_schedules": ["Daily: Cleaning cycle", "Weekly: Deep clean", "Monthly: Inspection"],
            "hierarchical_sections": ["Operation", "Maintenance", "Troubleshooting", "Parts"],
            "page_count": 50,
            "confidence_score": 1.0,
            "processing_timestamp": datetime.now().isoformat(),
            "hierarchical_document": True
        }
        
        # Create test entities with hierarchy
        test_entities = [
            # Level 1: Equipment Type
            {
                "canonical_name": "Taylor C602",
                "entity_text": "Taylor C602 Soft Serve Machine",
                "entity_type": "EQUIPMENT",
                "hierarchy_level": 1,
                "parent_entity": None,
                "page_reference": [1, 5, 10],
                "section_context": "Equipment Overview",
                "qsr_context": "Primary ice cream machine for McDonald's restaurants",
                "confidence": 1.0,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            },
            # Level 2: Equipment Components
            {
                "canonical_name": "Compressor",
                "entity_text": "compressor unit",
                "entity_type": "EQUIPMENT",
                "hierarchy_level": 2,
                "parent_entity": "Taylor C602",
                "page_reference": [15, 20],
                "section_context": "Components",
                "qsr_context": "Main cooling component for ice cream production",
                "confidence": 0.9,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            },
            {
                "canonical_name": "Heat Treatment System",
                "entity_text": "heat treatment system",
                "entity_type": "EQUIPMENT", 
                "hierarchy_level": 2,
                "parent_entity": "Taylor C602",
                "page_reference": [25, 30],
                "section_context": "Heat Treatment",
                "qsr_context": "Safety system for pasteurization and cleaning",
                "confidence": 0.9,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            },
            # Level 3: Procedures
            {
                "canonical_name": "Daily Cleaning Procedure",
                "entity_text": "daily cleaning procedure",
                "entity_type": "PROCEDURE",
                "hierarchy_level": 3,
                "parent_entity": "Taylor C602",
                "page_reference": [35, 40],
                "section_context": "Maintenance",
                "qsr_context": "Required daily cleaning for food safety compliance",
                "confidence": 1.0,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            },
            {
                "canonical_name": "Heat Treatment Procedure",
                "entity_text": "heat treatment procedure",
                "entity_type": "PROCEDURE",
                "hierarchy_level": 3,
                "parent_entity": "Heat Treatment System",
                "page_reference": [28, 32],
                "section_context": "Heat Treatment",
                "qsr_context": "Safety procedure for pasteurization",
                "confidence": 1.0,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            },
            # Level 4: Steps
            {
                "canonical_name": "Remove Product Lines",
                "entity_text": "remove product lines",
                "entity_type": "STEP",
                "hierarchy_level": 4,
                "parent_entity": "Daily Cleaning Procedure",
                "page_reference": [36],
                "section_context": "Cleaning Steps",
                "qsr_context": "First step in daily cleaning process",
                "confidence": 0.8,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            },
            {
                "canonical_name": "Run Cleaning Solution",
                "entity_text": "run cleaning solution",
                "entity_type": "STEP",
                "hierarchy_level": 4,
                "parent_entity": "Daily Cleaning Procedure",
                "page_reference": [37],
                "section_context": "Cleaning Steps",
                "qsr_context": "Chemical cleaning step for sanitization",
                "confidence": 0.8,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            },
            # Temperature entities
            {
                "canonical_name": "180°F",
                "entity_text": "180 degrees Fahrenheit",
                "entity_type": "TEMPERATURE",
                "hierarchy_level": 4,
                "parent_entity": "Heat Treatment Procedure",
                "page_reference": [30],
                "section_context": "Temperature Settings",
                "qsr_context": "Required temperature for heat treatment cycle",
                "confidence": 1.0,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            },
            # QSR-specific entities
            {
                "canonical_name": "Food Safety Compliance",
                "entity_text": "food safety compliance",
                "entity_type": "QSR_SPECIFIC",
                "hierarchy_level": 3,
                "parent_entity": "Daily Cleaning Procedure",
                "page_reference": [5, 35],
                "section_context": "Safety Requirements",
                "qsr_context": "McDonald's food safety standards for ice cream equipment",
                "confidence": 1.0,
                "document_id": document_id,
                "document_type": "service_manual",
                "equipment_category": "ice_cream"
            }
        ]
        
        # Store in Neo4j
        with self.neo4j_service.driver.session() as session:
            # Create document node
            doc_query = """
            CREATE (d:Document {
                document_id: $document_id,
                filename: $filename,
                document_type: $document_type,
                qsr_category: $qsr_category,
                target_audience: $target_audience,
                brand_context: $brand_context,
                equipment_focus: $equipment_focus,
                purpose: $purpose,
                executive_summary: $executive_summary,
                key_procedures: $key_procedures,
                safety_protocols: $safety_protocols,
                critical_temperatures: $critical_temperatures,
                maintenance_schedules: $maintenance_schedules,
                hierarchical_sections: $hierarchical_sections,
                page_count: $page_count,
                confidence_score: $confidence_score,
                processing_timestamp: $processing_timestamp,
                hierarchical_document: $hierarchical_document
            })
            RETURN d
            """
            
            session.run(doc_query, **document_node)
            logger.info("✅ Created document node")
            
            # Create entity nodes
            entities_created = 0
            for entity in test_entities:
                entity_type = entity['entity_type']
                
                entity_query = f"""
                CREATE (e:{entity_type} {{
                    canonical_name: $canonical_name,
                    entity_text: $entity_text,
                    entity_type: $entity_type,
                    hierarchy_level: $hierarchy_level,
                    parent_entity: $parent_entity,
                    page_reference: $page_reference,
                    section_context: $section_context,
                    qsr_context: $qsr_context,
                    confidence: $confidence,
                    document_id: $document_id,
                    document_type: $document_type,
                    equipment_category: $equipment_category
                }})
                RETURN e
                """
                
                result = session.run(entity_query, **entity)
                if result.single():
                    entities_created += 1
            
            logger.info(f"✅ Created {entities_created} entity nodes")
            
            # Create hierarchical relationships
            relationships_created = 0
            
            # BELONGS_TO relationships
            belongs_to_relationships = [
                ("Compressor", "Taylor C602", "BELONGS_TO"),
                ("Heat Treatment System", "Taylor C602", "BELONGS_TO"),
                ("Daily Cleaning Procedure", "Taylor C602", "PROCEDURE_FOR"),
                ("Heat Treatment Procedure", "Heat Treatment System", "PROCEDURE_FOR"),
                ("Remove Product Lines", "Daily Cleaning Procedure", "BELONGS_TO"),
                ("Run Cleaning Solution", "Daily Cleaning Procedure", "BELONGS_TO"),
                ("180°F", "Heat Treatment Procedure", "REQUIRES"),
                ("Food Safety Compliance", "Daily Cleaning Procedure", "GOVERNS")
            ]
            
            for source, target, rel_type in belongs_to_relationships:
                rel_query = f"""
                MATCH (source {{canonical_name: $source_name}}), 
                      (target {{canonical_name: $target_name}})
                CREATE (source)-[r:{rel_type} {{
                    document_id: $document_id,
                    confidence: 0.9,
                    relationship_source: 'hierarchical_structure'
                }}]->(target)
                RETURN r
                """
                
                result = session.run(rel_query, 
                                   source_name=source, 
                                   target_name=target,
                                   document_id=document_id)
                if result.single():
                    relationships_created += 1
            
            logger.info(f"✅ Created {relationships_created} hierarchical relationships")
            
            return {
                "document_created": True,
                "entities_created": entities_created,
                "relationships_created": relationships_created,
                "document_id": document_id
            }
    
    async def verify_hierarchical_structure(self):
        """Verify the hierarchical structure was created correctly"""
        
        logger.info("🔍 Verifying hierarchical structure...")
        
        with self.neo4j_service.driver.session() as session:
            # Count nodes by type
            node_query = """
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            node_results = session.run(node_query)
            node_counts = {}
            for record in node_results:
                labels = record['labels']
                count = record['count']
                label = labels[0] if labels else 'Unknown'
                node_counts[label] = count
            
            # Count relationships by type
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            """
            
            rel_results = session.run(rel_query)
            rel_counts = {}
            for record in rel_results:
                rel_type = record['rel_type']
                count = record['count']
                rel_counts[rel_type] = count
            
            # Test hierarchical traversal
            hierarchy_query = """
            MATCH (child)-[r]->(parent)
            WHERE type(r) IN ['BELONGS_TO', 'PROCEDURE_FOR', 'REQUIRES', 'GOVERNS']
            RETURN child.canonical_name as child,
                   type(r) as relationship,
                   parent.canonical_name as parent,
                   child.hierarchy_level as child_level,
                   parent.hierarchy_level as parent_level
            ORDER BY child_level
            """
            
            hierarchy_results = session.run(hierarchy_query)
            hierarchy_paths = []
            for record in hierarchy_results:
                hierarchy_paths.append({
                    "child": record['child'],
                    "relationship": record['relationship'],
                    "parent": record['parent'],
                    "child_level": record['child_level'],
                    "parent_level": record['parent_level']
                })
            
            logger.info(f"✅ Verification complete: {sum(node_counts.values())} nodes, {sum(rel_counts.values())} relationships")
            
            return {
                "node_counts": node_counts,
                "relationship_counts": rel_counts,
                "hierarchy_paths": hierarchy_paths,
                "total_nodes": sum(node_counts.values()),
                "total_relationships": sum(rel_counts.values())
            }
    
    async def test_context_queries(self):
        """Test context-aware queries without AI"""
        
        logger.info("🔍 Testing context queries...")
        
        test_queries = [
            "How do I clean the Taylor C602?",
            "What temperature for heat treatment?",
            "Daily maintenance procedure",
            "Food safety requirements"
        ]
        
        query_results = []
        
        with self.neo4j_service.driver.session() as session:
            for query in test_queries:
                # Simple keyword-based search
                keywords = query.lower().split()
                
                search_query = """
                MATCH (e)
                WHERE any(keyword IN $keywords WHERE 
                    toLower(e.canonical_name) CONTAINS keyword OR
                    toLower(e.entity_text) CONTAINS keyword OR
                    toLower(e.qsr_context) CONTAINS keyword
                )
                OPTIONAL MATCH (d:Document {document_id: e.document_id})
                RETURN e, d
                ORDER BY e.hierarchy_level, e.confidence DESC
                LIMIT 5
                """
                
                results = session.run(search_query, keywords=keywords)
                
                matches = []
                for record in results:
                    entity = dict(record['e']) if record['e'] else {}
                    document = dict(record['d']) if record['d'] else {}
                    
                    matches.append({
                        "entity": entity.get('canonical_name', 'Unknown'),
                        "type": entity.get('entity_type', 'Unknown'),
                        "context": entity.get('qsr_context', 'No context'),
                        "document": document.get('filename', 'Unknown'),
                        "hierarchy_level": entity.get('hierarchy_level', 0)
                    })
                
                query_results.append({
                    "query": query,
                    "matches": matches,
                    "match_count": len(matches)
                })
        
        logger.info(f"✅ Tested {len(test_queries)} queries")
        
        return query_results

async def main():
    """Main test function"""
    
    tester = TestEnhancedSystem()
    results = await tester.test_complete_system()
    
    print("\n" + "="*60)
    print("ENHANCED SYSTEM TEST RESULTS")
    print("="*60)
    
    if results["status"] == "success":
        print("✅ System test PASSED")
        
        print(f"\nDocument Structure:")
        test_results = results["test_results"]
        print(f"  - Document created: {test_results['document_created']}")
        print(f"  - Entities created: {test_results['entities_created']}")
        print(f"  - Relationships created: {test_results['relationships_created']}")
        
        print(f"\nDatabase Verification:")
        verification = results["verification_results"]
        print(f"  - Total nodes: {verification['total_nodes']}")
        print(f"  - Total relationships: {verification['total_relationships']}")
        print(f"  - Node types: {verification['node_counts']}")
        print(f"  - Relationship types: {verification['relationship_counts']}")
        
        print(f"\nHierarchy Paths:")
        for path in verification['hierarchy_paths']:
            print(f"  - {path['child']} -[{path['relationship']}]-> {path['parent']}")
        
        print(f"\nQuery Test Results:")
        for query_result in results["query_results"]:
            print(f"  Query: '{query_result['query']}'")
            print(f"    Found {query_result['match_count']} matches")
            for match in query_result['matches'][:2]:  # Show top 2
                print(f"      - {match['entity']} ({match['type']}) - Level {match['hierarchy_level']}")
        
    else:
        print("❌ System test FAILED")
        print(f"Error: {results['error']}")

if __name__ == "__main__":
    asyncio.run(main())