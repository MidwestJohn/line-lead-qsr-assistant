import logging
from typing import Dict, List, Any, Tuple
import re
import os

logger = logging.getLogger(__name__)

class Neo4jRelationshipGenerator:
    """Generates semantic relationships for Neo4j integration with RAG-Anything."""
    
    def __init__(self, neo4j_service):
        self.neo4j_service = neo4j_service
        
        # QSR-specific relationship patterns for semantic classification
        self.relationship_patterns = {
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
            "SAFETY_WARNING_FOR": [
                r"warning", r"caution", r"danger", r"safety", r"hazard",
                r"risk", r"avoid", r"never", r"do not"
            ],
            "FOLLOWED_BY": [
                r"followed by", r"then", r"next", r"after", r"subsequently",
                r"step.*step", r"before.*after"
            ],
            "APPLIES_TO": [
                r"applies to", r"used for", r"intended for", r"designed for",
                r"suitable for", r"compatible with"
            ],
            "GOVERNS": [
                r"governs", r"controls", r"regulates", r"manages",
                r"operates", r"runs", r"handles"
            ],
            "PARAMETER_OF": [
                r"temperature of", r"pressure of", r"speed of", r"setting for",
                r"parameter", r"specification", r"measurement"
            ],
            "DOCUMENTS": [
                r"documented in", r"described in", r"manual", r"guide",
                r"instruction", r"reference", r"specification"
            ]
        }
        
        # Equipment type classification for better node labeling
        self.equipment_types = {
            "Equipment": ["taylor", "machine", "equipment", "unit", "system", "device"],
            "Component": ["compressor", "pump", "motor", "valve", "sensor", "control"],
            "Procedure": ["cleaning", "maintenance", "service", "operation", "startup", "shutdown"],
            "Safety": ["warning", "caution", "safety", "hazard", "guideline", "protocol"],
            "Parameter": ["temperature", "pressure", "speed", "time", "setting", "specification"],
            "Document": ["manual", "guide", "instruction", "reference", "specification", "diagram"]
        }
    
    def process_rag_anything_entities(self, entities: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """Process entities and relationships from RAG-Anything with semantic classification."""
        
        try:
            # Step 1: Classify and create entities with proper labels
            processed_entities = self._classify_entities(entities)
            
            # Step 2: Generate semantic relationships
            semantic_relationships = self._generate_semantic_relationships(relationships)
            
            # Step 3: Create equipment hierarchies (Taylor equipment unification)
            equipment_hierarchies = self._create_equipment_hierarchies(processed_entities)
            
            # Step 4: Add cross-modal relationships (text-image-table connections)
            cross_modal_relationships = self._generate_cross_modal_relationships(entities)
            
            return {
                "entities": processed_entities,
                "semantic_relationships": semantic_relationships,
                "equipment_hierarchies": equipment_hierarchies,
                "cross_modal_relationships": cross_modal_relationships,
                "processing_method": "neo4j_semantic_generation"
            }
            
        except Exception as e:
            logger.error(f"Neo4j relationship generation failed: {e}")
            return {"error": str(e)}
    
    def _classify_entities(self, entities: List[Dict]) -> List[Dict]:
        """Classify entities with appropriate Neo4j labels."""
        
        classified_entities = []
        
        for entity in entities:
            entity_name = entity.get("name", "").lower()
            entity_description = entity.get("description", "").lower()
            combined_text = f"{entity_name} {entity_description}"
            
            # Determine entity type based on content (use exact matching for better accuracy)
            entity_type = "Entity"  # Default
            
            # Check specific patterns first (most specific to least specific)
            if any(word in combined_text for word in ["temperature", "pressure", "speed", "setting", "parameter", "control"]):
                entity_type = "Parameter"
            elif any(word in combined_text for word in ["safety", "warning", "caution", "hazard", "guideline"]):
                entity_type = "Safety"  
            elif any(word in combined_text for word in ["cleaning", "maintenance", "procedure", "service", "operation"]):
                entity_type = "Procedure"
            elif any(word in combined_text for word in ["compressor", "pump", "motor", "valve", "sensor", "component"]):
                entity_type = "Component"
            elif any(word in combined_text for word in ["manual", "guide", "instruction", "reference", "document"]):
                entity_type = "Document"
            elif any(word in combined_text for word in ["taylor", "machine", "equipment", "unit", "system", "device"]):
                entity_type = "Equipment"
            
            logger.info(f"Classified entity '{entity_name}' as '{entity_type}' based on '{combined_text}'")
            
            classified_entity = {
                "name": entity.get("name", ""),
                "type": entity_type,
                "description": entity.get("description", ""),
                "properties": entity.get("properties", {}),
                "multimodal_content": entity.get("multimodal_content", []),
                "source": "rag_anything_processed"
            }
            
            classified_entities.append(classified_entity)
        
        return classified_entities
    
    def _generate_semantic_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Generate semantic relationships instead of generic ones."""
        
        semantic_relationships = []
        
        for relationship in relationships:
            # Get relationship description or context
            description = relationship.get("description", "")
            context = relationship.get("context", "")
            combined_text = f"{description} {context}".lower()
            
            # Classify relationship type based on content
            relationship_type = "RELATED_TO"  # Default fallback
            confidence = 0.5
            
            for semantic_type, patterns in self.relationship_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, combined_text, re.IGNORECASE):
                        relationship_type = semantic_type
                        confidence = 0.9
                        break
                if confidence > 0.8:
                    break
            
            semantic_relationship = {
                "source": relationship.get("source", ""),
                "target": relationship.get("target", ""),
                "type": relationship_type,
                "description": description,
                "context": context,
                "confidence": confidence,
                "properties": relationship.get("properties", {}),
                "classification_source": "semantic_classification"
            }
            
            semantic_relationships.append(semantic_relationship)
        
        return semantic_relationships
    
    def _create_equipment_hierarchies(self, entities: List[Dict]) -> List[Dict]:
        """Create equipment hierarchies for unified equipment representation."""
        
        hierarchies = []
        
        # Group Taylor equipment entities
        taylor_entities = [e for e in entities if "taylor" in e["name"].lower()]
        if len(taylor_entities) > 1:
            # Create unified Taylor equipment entity
            hierarchies.append({
                "source": "Taylor_Equipment_Unified",
                "targets": [e["name"] for e in taylor_entities],
                "type": "UNIFIES",
                "description": "Unified representation of Taylor ice cream machine components and documentation"
            })
        
        # Group procedure entities by equipment
        equipment_entities = [e for e in entities if e["type"] == "Equipment"]
        procedure_entities = [e for e in entities if e["type"] == "Procedure"]
        
        for equipment in equipment_entities:
            related_procedures = [
                p for p in procedure_entities 
                if any(word in equipment["name"].lower() for word in p["name"].lower().split())
            ]
            
            for procedure in related_procedures:
                hierarchies.append({
                    "source": procedure["name"],
                    "target": equipment["name"],
                    "type": "PROCEDURE_FOR",
                    "description": f"{procedure['name']} is a procedure for {equipment['name']}"
                })
        
        return hierarchies
    
    def _generate_cross_modal_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Generate relationships between text, images, and tables."""
        
        cross_modal_relationships = []
        
        # Find entities with multimodal content
        text_entities = [e for e in entities if e.get("type") != "Image" and e.get("type") != "Table"]
        image_entities = [e for e in entities if e.get("type") == "Image"]
        table_entities = [e for e in entities if e.get("type") == "Table"]
        
        # Connect images to related text entities
        for image in image_entities:
            image_description = image.get("description", "").lower()
            
            for text_entity in text_entities:
                text_content = f"{text_entity.get('name', '')} {text_entity.get('description', '')}".lower()
                
                # Simple keyword matching for demonstration
                if any(word in text_content for word in image_description.split()[:5]):
                    cross_modal_relationships.append({
                        "source": image["name"],
                        "target": text_entity["name"],
                        "type": "ILLUSTRATES",
                        "description": f"Image illustrates {text_entity['name']}"
                    })
        
        # Connect tables to related entities
        for table in table_entities:
            table_description = table.get("description", "").lower()
            
            for text_entity in text_entities:
                if any(word in text_entity.get("name", "").lower() for word in ["temperature", "specification", "parameter"]):
                    cross_modal_relationships.append({
                        "source": table["name"],
                        "target": text_entity["name"],
                        "type": "SPECIFIES",
                        "description": f"Table specifies parameters for {text_entity['name']}"
                    })
        
        return cross_modal_relationships
    
    def populate_neo4j_with_semantic_graph(self, processed_data: Dict) -> Dict[str, Any]:
        """Populate Neo4j with semantically classified entities and relationships."""
        
        if not self.neo4j_service.connected:
            return {"error": "Neo4j not connected"}
        
        try:
            logger.info(f"Starting Neo4j population with {len(processed_data.get('entities', []))} entities and {len(processed_data.get('semantic_relationships', []))} relationships")
            
            with self.neo4j_service.driver.session() as session:
                # Clear existing graph for fresh population
                session.run("MATCH (n) DETACH DELETE n")
                
                stats = {
                    "entities_created": 0,
                    "semantic_relationships_created": 0,
                    "hierarchies_created": 0,
                    "cross_modal_relationships_created": 0
                }
                
                # Create entities with proper labels
                for entity in processed_data["entities"]:
                    session.run(f"""
                        CREATE (n:{entity['type']} {{
                            name: $name,
                            description: $description,
                            document_source: $document_source
                        }})
                        SET n += $properties
                    """, {
                        "name": entity.get("name", ""),
                        "description": entity.get("description", ""),
                        "document_source": entity.get("document_source", ""),
                        "properties": entity.get("properties", {})
                    })
                    stats["entities_created"] += 1
                
                # Create semantic relationships
                for relationship in processed_data["semantic_relationships"]:
                    try:
                        source_name = relationship.get("source", "")
                        target_name = relationship.get("target", "")
                        rel_type = relationship.get("type", "RELATED_TO")
                        
                        # Validate relationship type for Cypher (no spaces or special chars)
                        rel_type = rel_type.replace(" ", "_").replace("-", "_")
                        
                        if source_name and target_name:
                            session.run(f"""
                                MATCH (a {{name: $source}}), (b {{name: $target}})
                                CREATE (a)-[r:{rel_type} {{
                                    description: $description,
                                    context: $context,
                                    confidence: $confidence
                                }}]->(b)
                            """, {
                                "source": source_name,
                                "target": target_name,
                                "description": relationship.get("description", ""),
                                "context": relationship.get("context", ""),
                                "confidence": relationship.get("confidence", 0.5)
                            })
                            stats["semantic_relationships_created"] += 1
                        else:
                            logger.warning(f"Skipping relationship with missing source/target: {source_name} -> {target_name}")
                            
                    except Exception as rel_error:
                        logger.error(f"Failed to create relationship {relationship.get('source')} -> {relationship.get('target')}: {rel_error}")
                        continue
                
                # Create equipment hierarchies
                for hierarchy in processed_data["equipment_hierarchies"]:
                    if "targets" in hierarchy:  # Multiple targets (unification)
                        for target in hierarchy["targets"]:
                            session.run(f"""
                                MERGE (unified {{name: $source}})
                                MATCH (target {{name: $target}})
                                CREATE (target)-[r:{hierarchy['type']}]->(unified)
                                SET r.description = $description
                            """, {
                                "source": hierarchy["source"],
                                "target": target,
                                "description": hierarchy["description"]
                            })
                    else:  # Single target
                        session.run(f"""
                            MATCH (a {{name: $source}}), (b {{name: $target}})
                            CREATE (a)-[r:{hierarchy['type']} {{
                                description: $description
                            }}]->(b)
                        """, {
                            "source": hierarchy["source"],
                            "target": hierarchy["target"],
                            "description": hierarchy["description"]
                        })
                    stats["hierarchies_created"] += 1
                
                # Create cross-modal relationships
                for cross_modal in processed_data["cross_modal_relationships"]:
                    session.run(f"""
                        MATCH (a {{name: $source}}), (b {{name: $target}})
                        CREATE (a)-[r:{cross_modal['type']} {{
                            description: $description
                        }}]->(b)
                    """, {
                        "source": cross_modal["source"],
                        "target": cross_modal["target"],
                        "description": cross_modal["description"]
                    })
                    stats["cross_modal_relationships_created"] += 1
                
                return {
                    "neo4j_population_completed": True,
                    "statistics": stats,
                    "semantic_relationships_enabled": True
                }
                
        except Exception as e:
            logger.error(f"Neo4j population failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"error": str(e)}