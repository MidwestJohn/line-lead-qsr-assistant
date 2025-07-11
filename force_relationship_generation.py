#!/usr/bin/env python3
"""
Force Relationship Generation for Neo4j Database
Critical fix for broken semantic relationships in QSR knowledge graph
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import asyncio
import re
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from services.neo4j_service import Neo4jService
from services.neo4j_relationship_generator import Neo4jRelationshipGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ForceRelationshipGenerator:
    """Forces relationship generation for all entities in Neo4j"""
    
    def __init__(self):
        self.neo4j_service = Neo4jService()
        self.relationship_generator = Neo4jRelationshipGenerator(self.neo4j_service)
        
    def connect_to_neo4j(self) -> bool:
        """Connect to Neo4j database"""
        try:
            success = self.neo4j_service.connect()
            if success:
                logger.info("✅ Connected to Neo4j database")
                return True
            else:
                logger.error("❌ Failed to connect to Neo4j database")
                return False
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def analyze_current_state(self) -> Dict[str, Any]:
        """Analyze current Neo4j database state"""
        try:
            with self.neo4j_service.driver.session() as session:
                # Get total counts
                total_nodes = session.run('MATCH (n) RETURN count(n) as count').single()['count']
                total_relationships = session.run('MATCH ()-[r]->() RETURN count(r) as count').single()['count']
                
                # Get orphaned entities
                orphaned_entities = session.run('MATCH (n) WHERE NOT (n)-[]-() RETURN count(n) as count').single()['count']
                
                # Get node types
                node_types = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC').data()
                
                # Get relationship types
                rel_types = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC').data()
                
                # Get all entities without relationships
                orphaned_entities_list = session.run("""
                    MATCH (n) WHERE NOT (n)-[]-() 
                    RETURN n.name as name, labels(n) as labels, n.description as description
                    LIMIT 50
                """).data()
                
                analysis = {
                    "total_nodes": total_nodes,
                    "total_relationships": total_relationships,
                    "orphaned_entities": orphaned_entities,
                    "node_types": node_types,
                    "relationship_types": rel_types,
                    "orphaned_entities_sample": orphaned_entities_list
                }
                
                logger.info(f"📊 Database Analysis:")
                logger.info(f"   Total nodes: {total_nodes}")
                logger.info(f"   Total relationships: {total_relationships}")
                logger.info(f"   Orphaned entities: {orphaned_entities}")
                logger.info(f"   Relationship density: {total_relationships / max(total_nodes, 1):.2f}")
                
                return analysis
                
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return {}
    
    def extract_entities_for_relationship_generation(self) -> List[Dict]:
        """Extract all entities from Neo4j for relationship generation"""
        try:
            with self.neo4j_service.driver.session() as session:
                # Get all entities with their properties
                entities_result = session.run("""
                    MATCH (n) 
                    WHERE NOT 'VisualCitation' IN labels(n) AND NOT 'Document' IN labels(n)
                    RETURN n.name as name, 
                           labels(n) as labels, 
                           n.description as description,
                           n.document_source as document_source,
                           properties(n) as properties
                """).data()
                
                entities = []
                for record in entities_result:
                    # Convert to the format expected by relationship generator
                    entity = {
                        "name": record["name"] or f"Entity_{len(entities)}",
                        "type": record["labels"][0] if record["labels"] else "ENTITY",
                        "description": record["description"] or "",
                        "document_source": record["document_source"] or "unknown",
                        "properties": record["properties"] or {}
                    }
                    entities.append(entity)
                
                logger.info(f"📋 Extracted {len(entities)} entities for relationship generation")
                return entities
                
        except Exception as e:
            logger.error(f"❌ Entity extraction failed: {e}")
            return []
    
    def generate_semantic_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Generate semantic relationships between entities"""
        try:
            logger.info(f"🔗 Generating semantic relationships for {len(entities)} entities...")
            
            relationships = []
            
            # Generate relationships based on entity pairs
            for i, entity1 in enumerate(entities):
                for j, entity2 in enumerate(entities):
                    if i >= j:  # Avoid duplicates and self-relationships
                        continue
                    
                    # Generate relationship if there's semantic similarity
                    relationship = self._generate_relationship_between_entities(entity1, entity2)
                    if relationship:
                        relationships.append(relationship)
                        
                        # Log progress for large datasets
                        if len(relationships) % 100 == 0:
                            logger.info(f"   Generated {len(relationships)} relationships so far...")
            
            logger.info(f"✅ Generated {len(relationships)} semantic relationships")
            return relationships
            
        except Exception as e:
            logger.error(f"❌ Relationship generation failed: {e}")
            return []
    
    def _generate_relationship_between_entities(self, entity1: Dict, entity2: Dict) -> Dict:
        """Generate a relationship between two entities if semantically related"""
        try:
            name1 = entity1["name"].lower()
            name2 = entity2["name"].lower()
            desc1 = entity1.get("description", "").lower()
            desc2 = entity2.get("description", "").lower()
            type1 = entity1.get("type", "").lower()
            type2 = entity2.get("type", "").lower()
            
            # Combined text for analysis
            combined_text = f"{name1} {desc1} {name2} {desc2}"
            
            # QSR-specific relationship patterns
            relationship_patterns = {
                "PART_OF": [
                    r"part of", r"component of", r"belongs to", r"contained in",
                    r"inside", r"within", r"attached to", r"mounted on"
                ],
                "CONTAINS": [
                    r"contains", r"includes", r"has", r"equipped with",
                    r"fitted with", r"comes with", r"features"
                ],
                "REQUIRES": [
                    r"requires", r"needs", r"must have", r"depends on",
                    r"prerequisite", r"necessary", r"essential"
                ],
                "PROCEDURE_FOR": [
                    r"procedure for", r"process for", r"method for", r"steps for",
                    r"cleaning", r"maintenance", r"servicing", r"operation"
                ],
                "RELATED_TO": [
                    r"related", r"similar", r"connected", r"associated"
                ]
            }
            
            # Check for equipment-procedure relationships
            if ("equipment" in type1 and "procedure" in type2) or ("equipment" in type2 and "procedure" in type1):
                return {
                    "source": entity1["name"],
                    "target": entity2["name"],
                    "type": "PROCEDURE_FOR",
                    "description": f"Procedure relationship between {entity1['name']} and {entity2['name']}",
                    "context": "equipment_procedure_relationship",
                    "confidence": 0.8
                }
            
            # Check for part-of relationships
            if any(word in name1 for word in ["pump", "compressor", "valve", "motor", "sensor"]) and \
               any(word in name2 for word in ["machine", "equipment", "unit", "system"]):
                return {
                    "source": entity1["name"],
                    "target": entity2["name"],
                    "type": "PART_OF",
                    "description": f"{entity1['name']} is part of {entity2['name']}",
                    "context": "component_equipment_relationship",
                    "confidence": 0.9
                }
            
            # Check for semantic similarity in descriptions
            if desc1 and desc2 and len(desc1) > 10 and len(desc2) > 10:
                common_words = set(desc1.split()) & set(desc2.split())
                if len(common_words) > 2:
                    return {
                        "source": entity1["name"],
                        "target": entity2["name"],
                        "type": "RELATED_TO",
                        "description": f"Semantic relationship: {', '.join(list(common_words)[:3])}",
                        "context": "semantic_similarity",
                        "confidence": 0.7
                    }
            
            # Check for brand/model relationships
            if any(brand in name1 for brand in ["taylor", "hobart", "carpigiani"]) and \
               any(brand in name2 for brand in ["taylor", "hobart", "carpigiani"]):
                if name1 != name2:  # Don't relate to self
                    return {
                        "source": entity1["name"],
                        "target": entity2["name"],
                        "type": "RELATED_TO",
                        "description": f"Brand relationship between {entity1['name']} and {entity2['name']}",
                        "context": "brand_relationship",
                        "confidence": 0.8
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Relationship generation failed for {entity1.get('name', 'unknown')} -> {entity2.get('name', 'unknown')}: {e}")
            return None
    
    def create_relationships_in_neo4j(self, relationships: List[Dict]) -> bool:
        """Create relationships in Neo4j database"""
        try:
            logger.info(f"🚀 Creating {len(relationships)} relationships in Neo4j...")
            
            created_count = 0
            failed_count = 0
            
            with self.neo4j_service.driver.session() as session:
                for relationship in relationships:
                    try:
                        source_name = relationship.get("source", "")
                        target_name = relationship.get("target", "")
                        rel_type = relationship.get("type", "RELATED_TO")
                        
                        # Validate relationship type for Cypher
                        rel_type = rel_type.replace(" ", "_").replace("-", "_")
                        
                        if source_name and target_name:
                            # Check if relationship already exists
                            existing = session.run(f"""
                                MATCH (a {{name: $source}})-[r:{rel_type}]->(b {{name: $target}})
                                RETURN count(r) as count
                            """, {
                                "source": source_name,
                                "target": target_name
                            }).single()
                            
                            if existing["count"] == 0:
                                # Create new relationship
                                result = session.run(f"""
                                    MATCH (a {{name: $source}}), (b {{name: $target}})
                                    CREATE (a)-[r:{rel_type} {{
                                        description: $description,
                                        context: $context,
                                        confidence: $confidence,
                                        created_by: 'force_relationship_generation',
                                        created_at: datetime()
                                    }}]->(b)
                                    RETURN count(r) as created
                                """, {
                                    "source": source_name,
                                    "target": target_name,
                                    "description": relationship.get("description", ""),
                                    "context": relationship.get("context", ""),
                                    "confidence": relationship.get("confidence", 0.5)
                                })
                                
                                if result.single()["created"] > 0:
                                    created_count += 1
                                    
                                    # Log progress
                                    if created_count % 50 == 0:
                                        logger.info(f"   Created {created_count} relationships so far...")
                                else:
                                    failed_count += 1
                        else:
                            logger.warning(f"Skipping relationship with missing source/target: {source_name} -> {target_name}")
                            failed_count += 1
                            
                    except Exception as rel_error:
                        logger.error(f"Failed to create relationship {relationship.get('source')} -> {relationship.get('target')}: {rel_error}")
                        failed_count += 1
                        continue
            
            logger.info(f"✅ Relationship creation completed:")
            logger.info(f"   Created: {created_count}")
            logger.info(f"   Failed: {failed_count}")
            
            return created_count > 0
            
        except Exception as e:
            logger.error(f"❌ Relationship creation failed: {e}")
            return False
    
    def update_document_count(self) -> bool:
        """Update document count in documents.json to reflect Neo4j state"""
        try:
            # Get document count from Neo4j
            with self.neo4j_service.driver.session() as session:
                neo4j_doc_count = session.run("""
                    MATCH (d:Document) 
                    RETURN count(d) as count
                """).single()["count"]
            
            # Update documents.json
            documents_path = Path("documents.json")
            if documents_path.exists():
                with open(documents_path, 'r') as f:
                    documents_data = json.load(f)
                
                # Update count
                documents_data["count"] = neo4j_doc_count
                documents_data["last_updated"] = datetime.now().isoformat()
                
                with open(documents_path, 'w') as f:
                    json.dump(documents_data, f, indent=2)
                
                logger.info(f"✅ Updated documents.json count to {neo4j_doc_count}")
                return True
            else:
                logger.warning("documents.json not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Document count update failed: {e}")
            return False
    
    def run_complete_fix(self):
        """Run the complete relationship generation fix"""
        try:
            logger.info("🚀 Starting complete relationship generation fix...")
            
            # Step 1: Connect to Neo4j
            if not self.connect_to_neo4j():
                logger.error("❌ Cannot proceed without Neo4j connection")
                return False
            
            # Step 2: Analyze current state
            logger.info("📊 Analyzing current database state...")
            analysis = self.analyze_current_state()
            
            # Step 3: Extract entities
            logger.info("📋 Extracting entities for relationship generation...")
            entities = self.extract_entities_for_relationship_generation()
            
            if not entities:
                logger.error("❌ No entities found for relationship generation")
                return False
            
            # Step 4: Generate semantic relationships
            logger.info("🔗 Generating semantic relationships...")
            relationships = self.generate_semantic_relationships(entities)
            
            if not relationships:
                logger.warning("⚠️ No relationships generated")
                return False
            
            # Step 5: Create relationships in Neo4j
            logger.info("🚀 Creating relationships in Neo4j...")
            success = self.create_relationships_in_neo4j(relationships)
            
            if not success:
                logger.error("❌ Failed to create relationships in Neo4j")
                return False
            
            # Step 6: Update document count
            logger.info("📝 Updating document count...")
            self.update_document_count()
            
            # Step 7: Final analysis
            logger.info("📊 Final database analysis...")
            final_analysis = self.analyze_current_state()
            
            # Show improvement
            orphaned_before = analysis.get("orphaned_entities", 0)
            orphaned_after = final_analysis.get("orphaned_entities", 0)
            relationships_before = analysis.get("total_relationships", 0)
            relationships_after = final_analysis.get("total_relationships", 0)
            
            logger.info("🎉 RELATIONSHIP GENERATION COMPLETE!")
            logger.info(f"   Orphaned entities: {orphaned_before} → {orphaned_after}")
            logger.info(f"   Total relationships: {relationships_before} → {relationships_after}")
            logger.info(f"   Improvement: {relationships_after - relationships_before} new relationships")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Complete fix failed: {e}")
            return False
        finally:
            # Cleanup
            if self.neo4j_service and self.neo4j_service.driver:
                self.neo4j_service.disconnect()

if __name__ == "__main__":
    print("🔧 Force Relationship Generation - Neo4j Database Fix")
    print("=" * 60)
    
    # Initialize and run the fix
    fix = ForceRelationshipGenerator()
    success = fix.run_complete_fix()
    
    if success:
        print("\n✅ RELATIONSHIP GENERATION COMPLETED SUCCESSFULLY!")
        print("The Neo4j database now has semantic relationships between entities.")
        print("The document count has been updated to reflect the current state.")
    else:
        print("\n❌ RELATIONSHIP GENERATION FAILED!")
        print("Check the logs above for details.")
    
    print("\n" + "=" * 60)