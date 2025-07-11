#!/usr/bin/env python3
"""
LightRAG Semantic Interceptor
Hooks into LightRAG's entity extraction and relationship mapping stages to generate semantic relationships
"""

import logging
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import networkx as nx
from datetime import datetime

logger = logging.getLogger(__name__)

class LightRAGSemanticInterceptor:
    """
    Intercepts LightRAG's knowledge graph construction to generate semantic relationships
    """
    
    def __init__(self, neo4j_relationship_generator):
        self.neo4j_generator = neo4j_relationship_generator
        self.rag_storage_path = Path("./data/rag_storage")
        self.rag_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Equipment unification patterns
        self.equipment_brands = {
            "taylor": ["taylor", "c602", "c708", "c713"],
            "hobart": ["hobart", "hcm", "hcm450"],
            "carpigiani": ["carpigiani", "lb502", "lb302"],
            "electro_freeze": ["electro freeze", "ef", "88t"],
            "stoelting": ["stoelting", "f144", "f231"]
        }
        
        # QSR-specific entity patterns for automatic detection
        self.qsr_patterns = {
            "equipment_keywords": [
                "machine", "equipment", "unit", "system", "device", "fryer", 
                "grill", "freezer", "cooler", "mixer", "blender", "dispenser"
            ],
            "component_keywords": [
                "compressor", "pump", "motor", "valve", "sensor", "control",
                "panel", "switch", "gauge", "filter", "belt", "chain"
            ],
            "procedure_keywords": [
                "cleaning", "maintenance", "service", "operation", "startup",
                "shutdown", "sanitizing", "descaling", "calibration"
            ],
            "safety_keywords": [
                "warning", "caution", "danger", "safety", "hazard", "risk",
                "protective", "emergency", "lockout", "tagout"
            ],
            "parameter_keywords": [
                "temperature", "pressure", "speed", "time", "setting",
                "specification", "tolerance", "range", "limit"
            ]
        }
    
    async def intercept_entity_extraction(self, raw_entities: List[Dict], document_source: str) -> List[Dict]:
        """
        Intercept and enhance entity extraction with QSR-specific classification
        """
        try:
            logger.info(f"Intercepting entity extraction for {document_source}: {len(raw_entities)} entities")
            
            enhanced_entities = []
            equipment_entities = []
            
            for entity in raw_entities:
                # Enhanced entity classification
                enhanced_entity = await self._classify_qsr_entity(entity, document_source)
                enhanced_entities.append(enhanced_entity)
                
                # Track equipment for unification
                if enhanced_entity.get("type") == "Equipment":
                    equipment_entities.append(enhanced_entity)
            
            # Apply equipment unification
            unified_entities = await self._unify_equipment_entities(enhanced_entities, equipment_entities)
            
            logger.info(f"Enhanced {len(raw_entities)} entities -> {len(unified_entities)} unified entities")
            return unified_entities
            
        except Exception as e:
            logger.error(f"Entity extraction interception failed: {e}")
            return raw_entities
    
    async def intercept_relationship_mapping(self, raw_relationships: List[Dict], entities: List[Dict], document_source: str) -> List[Dict]:
        """
        Intercept and enhance relationship mapping with semantic classification
        """
        try:
            logger.info(f"Intercepting relationship mapping for {document_source}: {len(raw_relationships)} relationships")
            
            # Create entity lookup for relationship enhancement
            entity_lookup = {e.get("name", e.get("id", "")): e for e in entities}
            
            semantic_relationships = []
            
            for relationship in raw_relationships:
                # Apply semantic classification
                semantic_rel = await self._classify_semantic_relationship(relationship, entity_lookup, document_source)
                semantic_relationships.append(semantic_rel)
            
            # Generate additional QSR-specific relationships
            additional_relationships = await self._generate_qsr_relationships(entities, document_source)
            semantic_relationships.extend(additional_relationships)
            
            logger.info(f"Enhanced {len(raw_relationships)} relationships -> {len(semantic_relationships)} semantic relationships")
            return semantic_relationships
            
        except Exception as e:
            logger.error(f"Relationship mapping interception failed: {e}")
            return raw_relationships
    
    async def _classify_qsr_entity(self, entity: Dict, document_source: str) -> Dict:
        """
        Classify entity with QSR-specific logic
        """
        entity_name = entity.get("name", entity.get("id", "")).lower()
        entity_description = entity.get("description", entity.get("content", "")).lower()
        combined_text = f"{entity_name} {entity_description}"
        
        # Enhanced QSR-specific classification
        entity_type = "Entity"  # Default
        confidence = 0.5
        
        # Check equipment brands first (highest priority)
        for brand, models in self.equipment_brands.items():
            if any(model in combined_text for model in models):
                entity_type = "Equipment"
                confidence = 0.95
                entity["equipment_brand"] = brand
                break
        
        # Check QSR patterns if not equipment
        if entity_type == "Entity":
            for pattern_type, keywords in self.qsr_patterns.items():
                if any(keyword in combined_text for keyword in keywords):
                    if pattern_type == "equipment_keywords":
                        entity_type = "Equipment"
                        confidence = 0.85
                    elif pattern_type == "component_keywords":
                        entity_type = "Component"
                        confidence = 0.90
                    elif pattern_type == "procedure_keywords":
                        entity_type = "Procedure"
                        confidence = 0.88
                    elif pattern_type == "safety_keywords":
                        entity_type = "Safety"
                        confidence = 0.92
                    elif pattern_type == "parameter_keywords":
                        entity_type = "Parameter"
                        confidence = 0.87
                    break
        
        # Enhance entity with classification
        enhanced_entity = {
            **entity,
            "type": entity_type,
            "classification_confidence": confidence,
            "qsr_classified": True,
            "document_source": document_source,
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        return enhanced_entity
    
    async def _classify_semantic_relationship(self, relationship: Dict, entity_lookup: Dict, document_source: str) -> Dict:
        """
        Classify relationship with semantic meaning
        """
        source_entity = entity_lookup.get(relationship.get("source", ""), {})
        target_entity = entity_lookup.get(relationship.get("target", ""), {})
        
        description = relationship.get("description", "").lower()
        context = relationship.get("context", "").lower()
        combined_context = f"{description} {context}"
        
        # Semantic relationship classification
        relationship_type = "RELATED_TO"  # Default
        confidence = 0.5
        
        # Equipment-Component relationships
        if (source_entity.get("type") == "Equipment" and target_entity.get("type") == "Component"):
            if any(word in combined_context for word in ["contains", "includes", "has", "equipped with"]):
                relationship_type = "CONTAINS"
                confidence = 0.9
            elif any(word in combined_context for word in ["part of", "belongs to", "component of"]):
                relationship_type = "PART_OF"
                confidence = 0.9
        
        # Component-Equipment relationships
        elif (source_entity.get("type") == "Component" and target_entity.get("type") == "Equipment"):
            if any(word in combined_context for word in ["part of", "belongs to", "component of"]):
                relationship_type = "PART_OF"
                confidence = 0.9
        
        # Procedure relationships
        elif source_entity.get("type") == "Procedure":
            if any(word in combined_context for word in ["procedure for", "process for", "method for"]):
                relationship_type = "PROCEDURE_FOR"
                confidence = 0.9
            elif any(word in combined_context for word in ["requires", "needs", "depends on"]):
                relationship_type = "REQUIRES"
                confidence = 0.85
            elif any(word in combined_context for word in ["followed by", "then", "next"]):
                relationship_type = "FOLLOWED_BY"
                confidence = 0.8
        
        # Safety relationships
        elif source_entity.get("type") == "Safety":
            if any(word in combined_context for word in ["warning for", "applies to", "safety for"]):
                relationship_type = "SAFETY_WARNING_FOR"
                confidence = 0.9
        
        # Parameter relationships
        elif source_entity.get("type") == "Parameter":
            if any(word in combined_context for word in ["parameter of", "setting for", "controls"]):
                relationship_type = "PARAMETER_OF"
                confidence = 0.88
            elif any(word in combined_context for word in ["governs", "controls", "manages"]):
                relationship_type = "GOVERNS"
                confidence = 0.85
        
        # Document relationships
        elif target_entity.get("type") == "Equipment":
            if any(word in combined_context for word in ["documented in", "manual for", "describes"]):
                relationship_type = "DOCUMENTS"
                confidence = 0.85
        
        # Enhanced relationship with proper format for Neo4j generator
        semantic_relationship = {
            "source": relationship.get("source", ""),
            "target": relationship.get("target", ""), 
            "type": relationship_type,
            "description": description,
            "context": context,
            "confidence": confidence,
            "semantic_confidence": confidence,
            "source_entity_type": source_entity.get("type", "Unknown"),
            "target_entity_type": target_entity.get("type", "Unknown"),
            "properties": relationship.get("properties", {}),
            "qsr_classified": True,
            "document_source": document_source,
            "classification_timestamp": datetime.now().isoformat()
        }
        
        return semantic_relationship
    
    async def _unify_equipment_entities(self, all_entities: List[Dict], equipment_entities: List[Dict]) -> List[Dict]:
        """
        Unify equipment entities by brand and model for canonical representation
        """
        if len(equipment_entities) < 2:
            return all_entities
        
        # Group equipment by brand
        brand_groups = {}
        for equipment in equipment_entities:
            brand = equipment.get("equipment_brand", "unknown")
            if brand not in brand_groups:
                brand_groups[brand] = []
            brand_groups[brand].append(equipment)
        
        unified_entities = []
        equipment_unifications = []
        
        # Process non-equipment entities first
        for entity in all_entities:
            if entity.get("type") != "Equipment":
                unified_entities.append(entity)
        
        # Unify equipment entities by brand
        for brand, brand_equipment in brand_groups.items():
            if len(brand_equipment) == 1:
                # Single equipment, no unification needed
                unified_entities.append(brand_equipment[0])
            else:
                # Multiple equipment of same brand - create unified entity
                primary_equipment = brand_equipment[0]
                unified_name = f"{brand.title()}_Equipment_Unified"
                
                unified_equipment = {
                    "name": unified_name,
                    "type": "Equipment",
                    "unified_equipment": True,
                    "equipment_brand": brand,
                    "unified_components": [eq["name"] for eq in brand_equipment],
                    "description": f"Unified {brand} equipment representation",
                    "classification_confidence": 0.95,
                    "document_source": primary_equipment.get("document_source", ""),
                    "extraction_timestamp": datetime.now().isoformat()
                }
                
                unified_entities.append(unified_equipment)
                
                # Track unification for relationship updates
                equipment_unifications.append({
                    "unified_entity": unified_name,
                    "original_entities": [eq["name"] for eq in brand_equipment]
                })
        
        logger.info(f"Equipment unification: {len(equipment_unifications)} unifications created")
        return unified_entities
    
    async def _generate_qsr_relationships(self, entities: List[Dict], document_source: str) -> List[Dict]:
        """
        Generate additional QSR-specific relationships based on entity patterns
        """
        additional_relationships = []
        
        # Create entity type lookups
        equipment_entities = [e for e in entities if e.get("type") == "Equipment"]
        component_entities = [e for e in entities if e.get("type") == "Component"]
        procedure_entities = [e for e in entities if e.get("type") == "Procedure"]
        safety_entities = [e for e in entities if e.get("type") == "Safety"]
        parameter_entities = [e for e in entities if e.get("type") == "Parameter"]
        
        # Generate equipment-component relationships
        for equipment in equipment_entities:
            for component in component_entities:
                # Check if component name suggests it belongs to equipment
                if any(word in component["name"].lower() for word in equipment["name"].lower().split()):
                    additional_relationships.append({
                        "source": equipment["name"],
                        "target": component["name"],
                        "type": "CONTAINS",
                        "description": f"{equipment['name']} contains {component['name']}",
                        "context": "inferred equipment-component relationship",
                        "semantic_confidence": 0.75,
                        "auto_generated": True,
                        "document_source": document_source
                    })
        
        # Generate procedure-equipment relationships
        for procedure in procedure_entities:
            for equipment in equipment_entities:
                # Check if procedure mentions equipment
                proc_text = f"{procedure['name']} {procedure.get('description', '')}".lower()
                equip_words = equipment["name"].lower().split()
                if any(word in proc_text for word in equip_words):
                    additional_relationships.append({
                        "source": procedure["name"],
                        "target": equipment["name"],
                        "type": "PROCEDURE_FOR",
                        "description": f"{procedure['name']} is a procedure for {equipment['name']}",
                        "context": "inferred procedure-equipment relationship",
                        "semantic_confidence": 0.8,
                        "auto_generated": True,
                        "document_source": document_source
                    })
        
        # Generate safety-equipment relationships
        for safety in safety_entities:
            for equipment in equipment_entities:
                # Safety guidelines often apply to equipment
                additional_relationships.append({
                    "source": safety["name"],
                    "target": equipment["name"],
                    "type": "SAFETY_WARNING_FOR",
                    "description": f"{safety['name']} applies to {equipment['name']}",
                    "context": "inferred safety-equipment relationship",
                    "semantic_confidence": 0.7,
                    "auto_generated": True,
                    "document_source": document_source
                })
        
        # Generate parameter-equipment relationships
        for parameter in parameter_entities:
            for equipment in equipment_entities:
                # Parameters often control equipment
                additional_relationships.append({
                    "source": parameter["name"],
                    "target": equipment["name"],
                    "type": "PARAMETER_OF",
                    "description": f"{parameter['name']} is a parameter of {equipment['name']}",
                    "context": "inferred parameter-equipment relationship",
                    "semantic_confidence": 0.75,
                    "auto_generated": True,
                    "document_source": document_source
                })
        
        logger.info(f"Generated {len(additional_relationships)} additional QSR relationships")
        return additional_relationships
    
    async def post_process_knowledge_graph(self, entities: List[Dict], relationships: List[Dict], document_source: str) -> Dict[str, Any]:
        """
        Post-process the complete knowledge graph for semantic optimization
        """
        try:
            # Create network graph for analysis
            G = nx.DiGraph()
            
            # Add nodes
            for entity in entities:
                G.add_node(entity["name"], **entity)
            
            # Add edges
            for relationship in relationships:
                G.add_edge(
                    relationship["source"],
                    relationship["target"],
                    relationship_type=relationship["type"],
                    **relationship
                )
            
            # Analyze graph structure
            analysis = {
                "total_entities": len(entities),
                "total_relationships": len(relationships),
                "entity_types": self._count_entity_types(entities),
                "relationship_types": self._count_relationship_types(relationships),
                "equipment_hierarchies": self._analyze_equipment_hierarchies(entities, relationships),
                "semantic_density": len(relationships) / max(len(entities), 1),
                "document_source": document_source,
                "processing_timestamp": datetime.now().isoformat()
            }
            
            # Store processed graph
            await self._store_processed_graph(entities, relationships, analysis, document_source)
            
            # CRITICAL FIX: Populate Neo4j with the processed entities and relationships
            if self.neo4j_generator:
                logger.info(f"🚀 Populating Neo4j with {len(entities)} entities and {len(relationships)} relationships")
                try:
                    # Prepare the data in the format expected by the generator
                    processed_data = {
                        "entities": entities,
                        "semantic_relationships": relationships,  # Key fix: use correct field name
                        "analysis": analysis,
                        "document_source": document_source
                    }
                    population_result = self.neo4j_generator.populate_neo4j_with_semantic_graph(processed_data)
                    population_success = population_result.get("neo4j_population_completed", False)
                    if population_success:
                        logger.info("✅ Neo4j population completed successfully")
                        stats = population_result.get('statistics', {})
                        logger.info(f"📊 Created: {stats.get('entities_created', 0)} entities, {stats.get('semantic_relationships_created', 0)} relationships")
                    else:
                        logger.warning("⚠️  Neo4j population reported failure")
                        logger.error(f"🔍 Population result: {population_result}")
                        if population_result.get("error"):
                            logger.error(f"❌ Error details: {population_result['error']}")
                except Exception as e:
                    logger.error(f"❌ Neo4j population failed: {e}")
            else:
                logger.warning("⚠️  Neo4j generator not available - skipping automatic population")
            
            return {
                "entities": entities,
                "relationships": relationships,
                "analysis": analysis,
                "semantic_processing_completed": True,
                "neo4j_population_attempted": self.neo4j_generator is not None
            }
            
        except Exception as e:
            logger.error(f"Knowledge graph post-processing failed: {e}")
            return {
                "entities": entities,
                "relationships": relationships,
                "error": str(e),
                "semantic_processing_completed": False
            }
    
    def _count_entity_types(self, entities: List[Dict]) -> Dict[str, int]:
        """Count entities by type"""
        type_counts = {}
        for entity in entities:
            entity_type = entity.get("type", "Unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts
    
    def _count_relationship_types(self, relationships: List[Dict]) -> Dict[str, int]:
        """Count relationships by type"""
        type_counts = {}
        for relationship in relationships:
            rel_type = relationship.get("type", "Unknown")
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        return type_counts
    
    def _analyze_equipment_hierarchies(self, entities: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """Analyze equipment hierarchies in the graph"""
        equipment_entities = [e for e in entities if e.get("type") == "Equipment"]
        unified_equipment = [e for e in equipment_entities if e.get("unified_equipment")]
        
        return {
            "total_equipment": len(equipment_entities),
            "unified_equipment": len(unified_equipment),
            "equipment_brands": list(set(e.get("equipment_brand", "unknown") for e in equipment_entities)),
            "contains_relationships": len([r for r in relationships if r.get("type") == "CONTAINS"]),
            "part_of_relationships": len([r for r in relationships if r.get("type") == "PART_OF"])
        }
    
    async def _store_processed_graph(self, entities: List[Dict], relationships: List[Dict], analysis: Dict, document_source: str) -> None:
        """Store processed graph for future reference"""
        try:
            storage_file = self.rag_storage_path / f"semantic_graph_{document_source.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            storage_data = {
                "entities": entities,
                "relationships": relationships,
                "analysis": analysis,
                "document_source": document_source,
                "storage_timestamp": datetime.now().isoformat()
            }
            
            with open(storage_file, 'w') as f:
                json.dump(storage_data, f, indent=2)
            
            logger.info(f"Stored processed semantic graph: {storage_file}")
            
        except Exception as e:
            logger.error(f"Failed to store processed graph: {e}")