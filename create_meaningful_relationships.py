#!/usr/bin/env python3
"""
Create Meaningful Relationships Between Isolated Nodes
Focus on Entity, Equipment, QSR-Specific, and Temperature nodes
"""

import os
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeaningfulRelationshipCreator:
    """Creates meaningful semantic relationships between isolated nodes"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Neo4j connection
        self.uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        
        # QSR-specific relationship patterns
        self.equipment_patterns = {
            "fryer": ["oil", "temperature", "basket", "heating", "cooking", "filter"],
            "grill": ["temperature", "cooking", "heating", "surface", "plate"],
            "shake": ["mixing", "blending", "motor", "speed", "cup"],
            "ice": ["freezing", "temperature", "cooling", "storage"],
            "taylor": ["model", "machine", "equipment", "c602", "soft serve"],
            "cleaning": ["sanitizer", "wash", "rinse", "procedure", "maintenance"],
            "maintenance": ["service", "repair", "replacement", "inspection", "cleaning"],
            "temperature": ["heating", "cooling", "setting", "control", "monitor"],
            "safety": ["warning", "caution", "protective", "equipment", "procedure"]
        }
        
        # Temperature relationships
        self.temperature_contexts = {
            "cooking": ["grill", "fryer", "heating", "food", "cooking"],
            "storage": ["refrigerator", "freezer", "cooling", "storage"],
            "cleaning": ["wash", "rinse", "sanitizer", "cleaning"],
            "safety": ["warning", "caution", "hot", "cold", "danger"]
        }
        
    def create_all_meaningful_relationships(self):
        """Main method to create all meaningful relationships"""
        
        logger.info("🔗 Creating meaningful relationships between isolated nodes...")
        
        total_created = 0
        
        # 1. Create Equipment-Entity relationships
        logger.info("Creating Equipment-Entity relationships...")
        total_created += self.create_equipment_entity_relationships()
        
        # 2. Create Temperature-Equipment relationships
        logger.info("Creating Temperature-Equipment relationships...")
        total_created += self.create_temperature_equipment_relationships()
        
        # 3. Create QSR_SPECIFIC-Equipment relationships
        logger.info("Creating QSR_SPECIFIC-Equipment relationships...")
        total_created += self.create_qsr_equipment_relationships()
        
        # 4. Create Entity-Entity relationships (parts/components)
        logger.info("Creating Entity-Entity relationships...")
        total_created += self.create_entity_entity_relationships()
        
        # 5. Create procedure-based relationships
        logger.info("Creating procedure-based relationships...")
        total_created += self.create_procedure_relationships()
        
        # 6. Create document-based relationships
        logger.info("Creating document-based relationships...")
        total_created += self.create_document_based_relationships()
        
        logger.info(f"✅ Created {total_created} meaningful relationships")
        
        # Verify improvements
        self.verify_improvements()
        
    def create_equipment_entity_relationships(self):
        """Create relationships between Equipment and Entity nodes based on semantic similarity"""
        
        created = 0
        
        with self.driver.session() as session:
            # Get all Equipment nodes
            query = """
            MATCH (e:EQUIPMENT)
            RETURN e, elementId(e) as equipment_id
            """
            
            equipment_nodes = session.run(query).data()
            
            for equipment in equipment_nodes:
                equipment_node = equipment['e']
                equipment_id = equipment['equipment_id']
                equipment_name = equipment_node.get('name', '').lower()
                equipment_desc = equipment_node.get('description', '').lower()
                
                # Find related entities based on semantic patterns
                for pattern, keywords in self.equipment_patterns.items():
                    if pattern in equipment_name or pattern in equipment_desc:
                        # Find entities that match the keywords
                        for keyword in keywords:
                            query = f"""
                            MATCH (entity:ENTITY)
                            WHERE toLower(entity.name) CONTAINS $keyword
                            OR toLower(entity.description) CONTAINS $keyword
                            AND elementId(entity) <> $equipment_id
                            RETURN entity, elementId(entity) as entity_id
                            LIMIT 5
                            """
                            
                            entities = session.run(query, keyword=keyword, equipment_id=equipment_id).data()
                            
                            for entity in entities:
                                entity_id = entity['entity_id']
                                
                                # Create appropriate relationship
                                if keyword in ["part", "component", "blade", "motor"]:
                                    rel_type = "PART_OF"
                                elif keyword in ["temperature", "setting", "control"]:
                                    rel_type = "REQUIRES"
                                elif keyword in ["cleaning", "maintenance", "service"]:
                                    rel_type = "PROCEDURE_FOR"
                                else:
                                    rel_type = "RELATED_TO"
                                
                                if self.create_relationship(entity_id, rel_type, equipment_id):
                                    created += 1
        
        return created
    
    def create_temperature_equipment_relationships(self):
        """Create relationships between Temperature and Equipment nodes"""
        
        created = 0
        
        with self.driver.session() as session:
            # Get all Temperature nodes
            query = """
            MATCH (t:TEMPERATURE)
            RETURN t, elementId(t) as temp_id
            """
            
            temp_nodes = session.run(query).data()
            
            for temp in temp_nodes:
                temp_node = temp['t']
                temp_id = temp['temp_id']
                temp_name = temp_node.get('name', '').lower()
                temp_desc = temp_node.get('description', '').lower()
                
                # Find equipment that uses this temperature
                for context, keywords in self.temperature_contexts.items():
                    if any(keyword in temp_name or keyword in temp_desc for keyword in keywords):
                        # Find matching equipment
                        for keyword in keywords:
                            query = f"""
                            MATCH (e:EQUIPMENT)
                            WHERE toLower(e.name) CONTAINS $keyword
                            OR toLower(e.description) CONTAINS $keyword
                            AND elementId(e) <> $temp_id
                            RETURN e, elementId(e) as equipment_id
                            LIMIT 3
                            """
                            
                            equipment_nodes = session.run(query, keyword=keyword, temp_id=temp_id).data()
                            
                            for equipment in equipment_nodes:
                                equipment_id = equipment['equipment_id']
                                
                                # Temperature is required by equipment
                                if self.create_relationship(equipment_id, "REQUIRES", temp_id):
                                    created += 1
        
        return created
    
    def create_qsr_equipment_relationships(self):
        """Create relationships between QSR_SPECIFIC and Equipment nodes"""
        
        created = 0
        
        with self.driver.session() as session:
            # Get all QSR_SPECIFIC nodes
            query = """
            MATCH (q:QSR_SPECIFIC)
            RETURN q, elementId(q) as qsr_id
            """
            
            qsr_nodes = session.run(query).data()
            
            for qsr in qsr_nodes:
                qsr_node = qsr['q']
                qsr_id = qsr['qsr_id']
                qsr_name = qsr_node.get('name', '').lower()
                qsr_desc = qsr_node.get('description', '').lower()
                
                # QSR-specific patterns
                equipment_matches = []
                
                # Match based on QSR context
                if any(term in qsr_name or term in qsr_desc for term in ["cleaning", "maintenance", "service"]):
                    equipment_matches.extend(["taylor", "fryer", "grill", "shake"])
                elif any(term in qsr_name or term in qsr_desc for term in ["temperature", "cooking", "heating"]):
                    equipment_matches.extend(["grill", "fryer", "taylor"])
                elif any(term in qsr_name or term in qsr_desc for term in ["safety", "warning", "caution"]):
                    equipment_matches.extend(["equipment", "machine", "taylor"])
                
                # Find matching equipment
                for match in equipment_matches:
                    query = f"""
                    MATCH (e:EQUIPMENT)
                    WHERE toLower(e.name) CONTAINS $match
                    OR toLower(e.description) CONTAINS $match
                    AND elementId(e) <> $qsr_id
                    RETURN e, elementId(e) as equipment_id
                    LIMIT 3
                    """
                    
                    equipment_nodes = session.run(query, match=match, qsr_id=qsr_id).data()
                    
                    for equipment in equipment_nodes:
                        equipment_id = equipment['equipment_id']
                        
                        # Determine relationship type
                        if "procedure" in qsr_name or "cleaning" in qsr_name:
                            rel_type = "PROCEDURE_FOR"
                        elif "safety" in qsr_name or "warning" in qsr_name:
                            rel_type = "GOVERNS"
                        else:
                            rel_type = "RELATED_TO"
                        
                        if self.create_relationship(qsr_id, rel_type, equipment_id):
                            created += 1
        
        return created
    
    def create_entity_entity_relationships(self):
        """Create relationships between Entity nodes based on part/component relationships"""
        
        created = 0
        
        with self.driver.session() as session:
            # Get entities that are parts/components
            query = """
            MATCH (e:ENTITY)
            WHERE toLower(e.name) IN ['blade', 'motor', 'guard', 'housing', 'component', 'part']
            OR toLower(e.description) CONTAINS 'part'
            OR toLower(e.description) CONTAINS 'component'
            RETURN e, elementId(e) as entity_id
            """
            
            part_entities = session.run(query).data()
            
            for part in part_entities:
                part_node = part['e']
                part_id = part['entity_id']
                part_name = part_node.get('name', '').lower()
                
                # Find larger entities/systems this could be part of
                if part_name in ['blade', 'motor', 'guard']:
                    parent_terms = ['machine', 'equipment', 'system', 'taylor']
                elif part_name in ['housing', 'component']:
                    parent_terms = ['equipment', 'machine', 'system']
                else:
                    parent_terms = ['machine', 'equipment']
                
                for parent_term in parent_terms:
                    query = f"""
                    MATCH (parent:ENTITY)
                    WHERE toLower(parent.name) CONTAINS $parent_term
                    OR toLower(parent.description) CONTAINS $parent_term
                    AND elementId(parent) <> $part_id
                    RETURN parent, elementId(parent) as parent_id
                    LIMIT 2
                    """
                    
                    parent_entities = session.run(query, parent_term=parent_term, part_id=part_id).data()
                    
                    for parent in parent_entities:
                        parent_id = parent['parent_id']
                        
                        # Part is part of parent
                        if self.create_relationship(part_id, "PART_OF", parent_id):
                            created += 1
        
        return created
    
    def create_procedure_relationships(self):
        """Create relationships for procedure-based nodes"""
        
        created = 0
        
        with self.driver.session() as session:
            # Get all PROCEDURE nodes
            query = """
            MATCH (p:PROCEDURE)
            RETURN p, elementId(p) as proc_id
            """
            
            procedure_nodes = session.run(query).data()
            
            for proc in procedure_nodes:
                proc_node = proc['p']
                proc_id = proc['proc_id']
                proc_name = proc_node.get('name', '').lower()
                proc_desc = proc_node.get('description', '').lower()
                
                # Find equipment this procedure applies to
                equipment_types = []
                
                if any(term in proc_name or term in proc_desc for term in ["cleaning", "sanitize", "wash"]):
                    equipment_types.extend(["taylor", "fryer", "grill", "shake"])
                elif any(term in proc_name or term in proc_desc for term in ["maintenance", "service", "repair"]):
                    equipment_types.extend(["equipment", "machine", "taylor"])
                elif any(term in proc_name or term in proc_desc for term in ["cooking", "operation"]):
                    equipment_types.extend(["grill", "fryer", "taylor"])
                
                for equipment_type in equipment_types:
                    query = f"""
                    MATCH (e:EQUIPMENT)
                    WHERE toLower(e.name) CONTAINS $equipment_type
                    OR toLower(e.description) CONTAINS $equipment_type
                    AND elementId(e) <> $proc_id
                    RETURN e, elementId(e) as equipment_id
                    LIMIT 3
                    """
                    
                    equipment_nodes = session.run(query, equipment_type=equipment_type, proc_id=proc_id).data()
                    
                    for equipment in equipment_nodes:
                        equipment_id = equipment['equipment_id']
                        
                        # Procedure is for equipment
                        if self.create_relationship(proc_id, "PROCEDURE_FOR", equipment_id):
                            created += 1
        
        return created
    
    def create_document_based_relationships(self):
        """Create relationships based on document co-occurrence"""
        
        created = 0
        
        with self.driver.session() as session:
            # Find entities that appear in the same document pages
            query = """
            MATCH (e1:ENTITY), (e2:EQUIPMENT)
            WHERE e1.page_refs IS NOT NULL AND e2.page_refs IS NOT NULL
            AND any(page IN e1.page_refs WHERE page IN e2.page_refs)
            AND elementId(e1) <> elementId(e2)
            AND NOT EXISTS { (e1)-[]-(e2) }
            RETURN e1, e2, elementId(e1) as e1_id, elementId(e2) as e2_id
            LIMIT 50
            """
            
            co_occurrences = session.run(query).data()
            
            for co_occ in co_occurrences:
                e1_id = co_occ['e1_id']
                e2_id = co_occ['e2_id']
                
                # Create co-occurrence relationship
                if self.create_relationship(e1_id, "RELATED_TO", e2_id):
                    created += 1
        
        return created
    
    def create_relationship(self, source_id: str, rel_type: str, target_id: str) -> bool:
        """Create a relationship between two nodes using elementId"""
        
        try:
            query = f"""
            MATCH (source), (target)
            WHERE elementId(source) = $source_id AND elementId(target) = $target_id
            AND NOT EXISTS {{ (source)-[:{rel_type}]-(target) }}
            CREATE (source)-[r:{rel_type}]->(target)
            RETURN r
            """
            
            with self.driver.session() as session:
                result = session.run(query, source_id=source_id, target_id=target_id)
                
                if result.single():
                    return True
                
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return False
        
        return False
    
    def verify_improvements(self):
        """Verify that the improvements worked"""
        
        logger.info("🔍 Verifying relationship improvements...")
        
        with self.driver.session() as session:
            # Check isolation of key node types
            node_types = ["ENTITY", "EQUIPMENT", "QSR_SPECIFIC", "TEMPERATURE"]
            
            for node_type in node_types:
                # Count nodes with very few relationships
                query = f"""
                MATCH (n:{node_type})
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) as rel_count
                WHERE rel_count <= 3
                RETURN count(n) as weakly_connected_count
                """
                
                result = session.run(query)
                weakly_connected = result.single()['weakly_connected_count']
                logger.info(f"{node_type} nodes with ≤3 relationships: {weakly_connected}")
            
            # Check total relationships
            query = """
            MATCH ()-[r]->()
            RETURN count(r) as total_relationships
            """
            
            result = session.run(query)
            total_relationships = result.single()['total_relationships']
            logger.info(f"Total relationships in database: {total_relationships}")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

def main():
    """Main execution function"""
    
    creator = MeaningfulRelationshipCreator()
    
    try:
        creator.create_all_meaningful_relationships()
    except KeyboardInterrupt:
        logger.info("Relationship creation interrupted by user")
    except Exception as e:
        logger.error(f"Relationship creation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        creator.close()

if __name__ == "__main__":
    main()