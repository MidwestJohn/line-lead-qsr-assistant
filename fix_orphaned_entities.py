#!/usr/bin/env python3
"""
Fix Orphaned Entities - Generate Semantic Relationships
Critical fix for the 502 orphaned entities missing semantic relationships
"""

import os
import re
import json
import time
from typing import Dict, List, Any, Tuple, Set
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrphanedEntityFixer:
    """Fixes orphaned entities by creating semantic relationships"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Neo4j connection
        self.uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        
        # Relationship patterns for semantic analysis
        self.relationship_patterns = {
            "RELATED_TO": [
                r"model\s+(\w+)", r"equipment\s+(\w+)", r"type\s+(\w+)", 
                r"part\s+(\w+)", r"component\s+(\w+)", r"system\s+(\w+)"
            ],
            "PART_OF": [
                r"component.*of", r"part.*of", r"section.*of", r"element.*of"
            ],
            "PROCEDURE_FOR": [
                r"cleaning", r"maintenance", r"service", r"operation", 
                r"startup", r"shutdown", r"inspection", r"calibration"
            ],
            "REQUIRES": [
                r"requires", r"needs", r"must.*have", r"depends.*on"
            ],
            "LOCATED_AT": [
                r"located.*at", r"positioned.*at", r"found.*at", r"installed.*at"
            ],
            "USES": [
                r"uses", r"utilizes", r"employs", r"operates.*with"
            ]
        }
        
        # Common QSR equipment models and types for grouping
        self.equipment_families = {
            "C602": ["C602", "C602X", "C602Bacteria"],
            "Taylor": ["Taylor", "TAYLOR"],
            "Grill": ["grill", "GRILL", "Grill"],
            "Fryer": ["fryer", "FRYER", "Fryer"],
            "Shake": ["shake", "SHAKE", "Shake"],
            "Ice": ["ice", "ICE", "Ice"]
        }
        
    def fix_all_orphaned_entities(self):
        """Main method to fix all orphaned entities"""
        
        logger.info("🔧 Starting orphaned entity fix process...")
        
        # Get all orphaned entities
        orphaned_entities = self.get_orphaned_entities()
        logger.info(f"Found {len(orphaned_entities)} orphaned entities")
        
        # Process in batches to avoid memory issues
        batch_size = 50
        total_relationships_created = 0
        
        for i in range(0, len(orphaned_entities), batch_size):
            batch = orphaned_entities[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} entities)")
            
            relationships_created = self.process_entity_batch(batch)
            total_relationships_created += relationships_created
            
            # Small delay to prevent overwhelming the database
            time.sleep(0.1)
        
        logger.info(f"✅ Created {total_relationships_created} total relationships")
        
        # Final verification
        self.verify_fix()
        
    def get_orphaned_entities(self) -> List[Dict]:
        """Get all orphaned entities from Neo4j"""
        
        query = """
        MATCH (e)
        WHERE e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS
        AND NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
        RETURN e, labels(e) as labels, id(e) as node_id
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            entities = []
            for record in result:
                entity = dict(record['e'])
                entity['labels'] = record['labels']
                entity['node_id'] = record['node_id']
                entities.append(entity)
            
            return entities
    
    def process_entity_batch(self, entities: List[Dict]) -> int:
        """Process a batch of entities and create relationships"""
        
        relationships_created = 0
        
        for entity in entities:
            try:
                # Extract entity properties
                name = entity.get('name', '')
                description = entity.get('description', '')
                entity_type = entity.get('type', '')
                labels = entity.get('labels', [])
                node_id = entity.get('node_id')
                
                # Create text representation for analysis
                text_for_analysis = f"{name} {description} {entity_type}".strip()
                
                if not text_for_analysis:
                    continue
                
                # Find potential relationships
                potential_relationships = self.find_relationships_for_entity(
                    entity, text_for_analysis
                )
                
                # Create relationships in Neo4j
                for rel_type, target_entities in potential_relationships.items():
                    for target_entity in target_entities:
                        if self.create_relationship(node_id, rel_type, target_entity):
                            relationships_created += 1
                
            except Exception as e:
                logger.error(f"Error processing entity {entity.get('name', 'unknown')}: {e}")
                continue
        
        return relationships_created
    
    def find_relationships_for_entity(self, entity: Dict, text: str) -> Dict[str, List[Dict]]:
        """Find potential relationships for an entity"""
        
        relationships = {}
        
        # 1. Find equipment family relationships
        equipment_relationships = self.find_equipment_family_relationships(entity, text)
        if equipment_relationships:
            relationships.update(equipment_relationships)
        
        # 2. Find semantic relationships based on text patterns
        semantic_relationships = self.find_semantic_relationships(entity, text)
        if semantic_relationships:
            relationships.update(semantic_relationships)
        
        # 3. Find document-based relationships
        document_relationships = self.find_document_relationships(entity)
        if document_relationships:
            relationships.update(document_relationships)
        
        return relationships
    
    def find_equipment_family_relationships(self, entity: Dict, text: str) -> Dict[str, List[Dict]]:
        """Find relationships based on equipment families"""
        
        relationships = {}
        
        # Extract equipment family
        for family_name, family_keywords in self.equipment_families.items():
            for keyword in family_keywords:
                if keyword.lower() in text.lower():
                    # Find other entities in the same family
                    related_entities = self.find_entities_in_family(family_name, entity['node_id'])
                    if related_entities:
                        relationships['RELATED_TO'] = related_entities
                    break
        
        return relationships
    
    def find_semantic_relationships(self, entity: Dict, text: str) -> Dict[str, List[Dict]]:
        """Find semantic relationships based on text patterns"""
        
        relationships = {}
        
        # Analyze text for relationship patterns
        for rel_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Find entities that could be targets for this relationship
                    target_entities = self.find_target_entities_for_relationship(
                        rel_type, entity, text
                    )
                    if target_entities:
                        relationships[rel_type] = target_entities
                    break
        
        return relationships
    
    def find_document_relationships(self, entity: Dict) -> Dict[str, List[Dict]]:
        """Find relationships based on common document sources"""
        
        relationships = {}
        
        # Find entities from same document pages
        page_refs = entity.get('page_refs', [])
        if page_refs:
            related_entities = self.find_entities_on_same_pages(page_refs, entity['node_id'])
            if related_entities:
                relationships['RELATED_TO'] = related_entities
        
        return relationships
    
    def find_entities_in_family(self, family_name: str, exclude_node_id: int) -> List[Dict]:
        """Find other entities in the same equipment family"""
        
        family_keywords = self.equipment_families.get(family_name, [])
        if not family_keywords:
            return []
        
        # Build query to find related entities
        keyword_conditions = " OR ".join([f"toLower(e.name) CONTAINS toLower('{kw}')" for kw in family_keywords])
        
        query = f"""
        MATCH (e)
        WHERE id(e) <> {exclude_node_id}
        AND ({keyword_conditions})
        RETURN e, id(e) as node_id
        LIMIT 10
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            entities = []
            for record in result:
                entity = dict(record['e'])
                entity['node_id'] = record['node_id']
                entities.append(entity)
            
            return entities
    
    def find_target_entities_for_relationship(self, rel_type: str, entity: Dict, text: str) -> List[Dict]:
        """Find target entities for a specific relationship type"""
        
        # Simple approach: find entities with similar contexts
        if rel_type == "PROCEDURE_FOR":
            # For procedures, find equipment entities
            query = """
            MATCH (e:EQUIPMENT)
            WHERE id(e) <> $exclude_id
            RETURN e, id(e) as node_id
            LIMIT 5
            """
        elif rel_type == "PART_OF":
            # For part relationships, find larger equipment entities
            query = """
            MATCH (e)
            WHERE (e:EQUIPMENT OR e:ENTITY)
            AND id(e) <> $exclude_id
            AND (toLower(e.name) CONTAINS 'system' OR toLower(e.name) CONTAINS 'machine')
            RETURN e, id(e) as node_id
            LIMIT 5
            """
        else:
            # Generic relationship - find any related entities
            query = """
            MATCH (e)
            WHERE id(e) <> $exclude_id
            AND (e:EQUIPMENT OR e:ENTITY OR e:PROCEDURE)
            RETURN e, id(e) as node_id
            LIMIT 3
            """
        
        with self.driver.session() as session:
            result = session.run(query, exclude_id=entity['node_id'])
            entities = []
            for record in result:
                target_entity = dict(record['e'])
                target_entity['node_id'] = record['node_id']
                entities.append(target_entity)
            
            return entities
    
    def find_entities_on_same_pages(self, page_refs: List[int], exclude_node_id: int) -> List[Dict]:
        """Find entities that appear on the same document pages"""
        
        if not page_refs:
            return []
        
        # Find entities with overlapping page references
        query = """
        MATCH (e)
        WHERE id(e) <> $exclude_id
        AND any(page IN $page_refs WHERE page IN e.page_refs)
        RETURN e, id(e) as node_id
        LIMIT 5
        """
        
        with self.driver.session() as session:
            result = session.run(query, exclude_id=exclude_node_id, page_refs=page_refs)
            entities = []
            for record in result:
                entity = dict(record['e'])
                entity['node_id'] = record['node_id']
                entities.append(entity)
            
            return entities
    
    def create_relationship(self, source_node_id: int, rel_type: str, target_entity: Dict) -> bool:
        """Create a relationship between two entities"""
        
        try:
            query = f"""
            MATCH (source), (target)
            WHERE id(source) = $source_id AND id(target) = $target_id
            CREATE (source)-[r:{rel_type}]->(target)
            RETURN r
            """
            
            with self.driver.session() as session:
                result = session.run(query, 
                                   source_id=source_node_id, 
                                   target_id=target_entity['node_id'])
                
                # Check if relationship was created
                if result.single():
                    logger.debug(f"Created {rel_type} relationship: {source_node_id} -> {target_entity['node_id']}")
                    return True
                
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return False
        
        return False
    
    def verify_fix(self):
        """Verify that the fix worked"""
        
        logger.info("🔍 Verifying fix results...")
        
        # Count remaining orphaned entities
        query = """
        MATCH (e)
        WHERE e:ENTITY OR e:EQUIPMENT OR e:LOCATION OR e:PROCEDURE OR e:PROCESS
        AND NOT (e)-[:RELATED_TO|:PROCEDURE_FOR|:PART_OF|:LOCATED_AT|:REQUIRES|:USES]-()
        RETURN count(e) as orphaned_count
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            orphaned_count = result.single()['orphaned_count']
            
            logger.info(f"Remaining orphaned entities: {orphaned_count}")
            
            if orphaned_count < 50:  # Success threshold
                logger.info("✅ Fix successful - significantly reduced orphaned entities")
            else:
                logger.warning(f"⚠️ Still have {orphaned_count} orphaned entities")
        
        # Count total relationships
        query = """
        MATCH ()-[r]->()
        RETURN count(r) as total_relationships
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            total_relationships = result.single()['total_relationships']
            
            logger.info(f"Total relationships in database: {total_relationships}")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

def main():
    """Main execution function"""
    
    fixer = OrphanedEntityFixer()
    
    try:
        fixer.fix_all_orphaned_entities()
    except KeyboardInterrupt:
        logger.info("Fix interrupted by user")
    except Exception as e:
        logger.error(f"Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        fixer.close()

if __name__ == "__main__":
    main()