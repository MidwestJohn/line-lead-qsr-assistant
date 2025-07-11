#!/usr/bin/env python3
"""
Document Context Integration Service
Comprehensive document-level context enhancement for Line Lead QSR System
"""

import os
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from collections import defaultdict

# AI/ML imports
from openai import OpenAI

# Neo4j imports
from neo4j import GraphDatabase

# Local imports
from .neo4j_service import Neo4jService

logger = logging.getLogger(__name__)

class DocumentContextIntegrationService:
    """
    Comprehensive document context integration service
    Implements document summarization, hierarchical structure, and entity deduplication
    """
    
    def __init__(self):
        self.neo4j_service = Neo4jService()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # QSR-specific document type patterns
        self.document_type_patterns = {
            "service_manual": ["service", "manual", "maintenance", "repair", "technical"],
            "cleaning_guide": ["cleaning", "sanitize", "wash", "hygiene", "protocol"],
            "safety_protocol": ["safety", "warning", "caution", "hazard", "emergency"],
            "operation_guide": ["operation", "operating", "procedure", "workflow", "process"],
            "installation_manual": ["installation", "setup", "assembly", "mounting"],
            "troubleshooting_guide": ["troubleshoot", "problem", "issue", "fault", "diagnostic"]
        }
        
        # Equipment type classification
        self.equipment_categories = {
            "ice_cream": ["taylor", "c602", "soft serve", "ice cream", "shake"],
            "fryer": ["fryer", "frying", "oil", "basket", "heating"],
            "grill": ["grill", "grilling", "cooking", "plate", "surface"],
            "beverage": ["beverage", "drink", "dispenser", "fountain"],
            "refrigeration": ["refrigerator", "freezer", "cooling", "temperature"],
            "cleaning": ["cleaning", "sanitizer", "chemical", "wash"]
        }
        
        # Entity normalization patterns
        self.normalization_patterns = {
            "equipment_models": {
                r"taylor\s*c602": "Taylor C602",
                r"c602[a-z0-9]*": "Taylor C602",
                r"model\s*c602": "Taylor C602",
                r"grote\s*tool": "Grote Tool",
                r"1grote\s*tool": "Grote Tool"
            },
            "procedures": {
                r"cleaning\s*procedure": "Cleaning Procedure",
                r"maintenance\s*schedule": "Maintenance Schedule",
                r"safety\s*protocol": "Safety Protocol"
            },
            "temperatures": {
                r"(\d+)\s*°?f": r"\1°F",
                r"(\d+)\s*degrees": r"\1°F",
                r"(\d+)\s*deg": r"\1°F"
            }
        }
        
    async def process_document_upload(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document upload with comprehensive context integration
        
        Args:
            document_data: Dictionary containing document info and content
            
        Returns:
            Processing results with document context and hierarchical structure
        """
        
        logger.info(f"Processing document upload with context integration: {document_data.get('filename', 'unknown')}")
        
        try:
            # 1. Generate document-level summary
            document_summary = await self.generate_document_summary(document_data)
            
            # 2. Extract and normalize entities with hierarchy
            hierarchical_entities = await self.extract_hierarchical_entities(document_data, document_summary)
            
            # 3. Create Neo4j document node with rich metadata
            document_node = await self.create_document_node(document_data, document_summary)
            
            # 4. Process entities with deduplication and normalization
            processed_entities = await self.process_entities_with_deduplication(
                hierarchical_entities, document_node['document_id']
            )
            
            # 5. Create hierarchical relationships
            hierarchy_relationships = await self.create_hierarchical_relationships(
                processed_entities, document_node['document_id']
            )
            
            # 6. Store in Neo4j with hierarchical structure
            neo4j_results = await self.store_hierarchical_structure(
                document_node, processed_entities, hierarchy_relationships
            )
            
            return {
                "status": "success",
                "document_summary": document_summary,
                "document_node": document_node,
                "processed_entities": len(processed_entities),
                "hierarchy_relationships": len(hierarchy_relationships),
                "neo4j_results": neo4j_results,
                "processing_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document context integration failed: {e}")
            raise e
    
    async def generate_document_summary(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive document-level summary
        
        Args:
            document_data: Document content and metadata
            
        Returns:
            Document summary with purpose, focus, audience, and classification
        """
        
        content = document_data.get('content', '')
        filename = document_data.get('filename', '')
        
        # AI prompt for document summarization
        prompt = f"""
        Analyze this QSR (Quick Service Restaurant) technical document and provide a comprehensive summary:

        Document: {filename}
        Content: {content[:3000]}...

        Please provide a JSON response with:
        1. document_purpose: Main purpose and objective of this document
        2. equipment_focus: Primary equipment/systems covered (be specific with models)
        3. target_audience: Who this document is intended for (line leads, maintenance staff, etc.)
        4. document_type: Classification (service_manual, cleaning_guide, safety_protocol, etc.)
        5. key_procedures: List of main procedures/processes covered
        6. safety_protocols: Critical safety information mentioned
        7. critical_temperatures: Any temperature specifications mentioned
        8. maintenance_schedules: Maintenance timing/frequency mentioned
        9. brand_context: Brand/franchise context (McDonald's, etc.)
        10. qsr_category: Equipment category (ice_cream, fryer, grill, etc.)
        11. executive_summary: 2-3 sentence overview for line leads
        12. hierarchical_sections: Main sections/chapters of the document

        Focus on actionable information for QSR line leads managing equipment.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a QSR technical documentation expert. Provide precise, actionable summaries for restaurant equipment management."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            summary_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                summary_data = json.loads(summary_text)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                summary_data = self._parse_summary_fallback(summary_text)
            
            # Classify document type
            document_type = self._classify_document_type(filename, content, summary_data)
            summary_data['document_type'] = document_type
            
            # Extract equipment category
            equipment_category = self._classify_equipment_category(filename, content, summary_data)
            summary_data['qsr_category'] = equipment_category
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Document summary generation failed: {e}")
            # Return basic summary
            return {
                "document_purpose": f"Technical documentation for {filename}",
                "equipment_focus": "Equipment maintenance and operation",
                "target_audience": "QSR line leads and maintenance staff",
                "document_type": "technical_manual",
                "key_procedures": [],
                "safety_protocols": [],
                "critical_temperatures": [],
                "maintenance_schedules": [],
                "brand_context": "QSR franchise",
                "qsr_category": "general_equipment",
                "executive_summary": f"Technical documentation for equipment management from {filename}",
                "hierarchical_sections": []
            }
    
    async def extract_hierarchical_entities(self, document_data: Dict[str, Any], 
                                           document_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract entities with hierarchical structure and document context
        
        Args:
            document_data: Document content and metadata
            document_summary: Generated document summary
            
        Returns:
            List of entities with hierarchical relationships and context
        """
        
        content = document_data.get('content', '')
        
        # AI prompt for hierarchical entity extraction
        prompt = f"""
        Extract entities from this QSR technical document with hierarchical structure:

        Document Type: {document_summary.get('document_type', 'unknown')}
        Equipment Focus: {document_summary.get('equipment_focus', 'unknown')}
        Content: {content[:4000]}...

        Extract entities following this hierarchy:
        Manual → Equipment_Type → Equipment_Model → Procedure → Step → Detail

        For each entity, provide:
        1. entity_text: The exact text from document
        2. entity_type: EQUIPMENT, PROCEDURE, STEP, DETAIL, TEMPERATURE, SAFETY, etc.
        3. canonical_name: Normalized, standard name
        4. hierarchy_level: 1 (Equipment_Type) to 6 (Detail)
        5. parent_entity: What this entity belongs to
        6. page_reference: Page number if available
        7. section_context: Which section/chapter this appears in
        8. qsr_context: How this relates to QSR operations
        9. confidence: Extraction confidence (0.0-1.0)

        Focus on:
        - Equipment models and components
        - Procedures and steps
        - Temperatures and settings
        - Safety warnings and protocols
        - Maintenance schedules
        - Tools and parts

        Return as JSON array of entities.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a QSR technical entity extraction expert. Extract entities with precise hierarchical relationships."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            entities_text = response.choices[0].message.content
            
            try:
                entities = json.loads(entities_text)
                if not isinstance(entities, list):
                    entities = []
            except json.JSONDecodeError:
                entities = []
            
            # Add document context to each entity
            for entity in entities:
                entity['document_id'] = document_data.get('document_id', str(uuid.uuid4()))
                entity['document_type'] = document_summary.get('document_type', 'unknown')
                entity['equipment_category'] = document_summary.get('qsr_category', 'general')
                entity['extraction_timestamp'] = datetime.now().isoformat()
                entity['processing_method'] = 'document_context_integration'
            
            return entities
            
        except Exception as e:
            logger.error(f"Hierarchical entity extraction failed: {e}")
            return []
    
    async def create_document_node(self, document_data: Dict[str, Any], 
                                   document_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create document node with rich metadata for Neo4j
        
        Args:
            document_data: Document content and metadata
            document_summary: Generated document summary
            
        Returns:
            Document node data for Neo4j storage
        """
        
        document_id = document_data.get('document_id', str(uuid.uuid4()))
        
        document_node = {
            "document_id": document_id,
            "filename": document_data.get('filename', ''),
            "document_type": document_summary.get('document_type', 'unknown'),
            "qsr_category": document_summary.get('qsr_category', 'general'),
            "target_audience": document_summary.get('target_audience', 'line_leads'),
            "brand_context": document_summary.get('brand_context', 'QSR'),
            "equipment_focus": document_summary.get('equipment_focus', ''),
            "purpose": document_summary.get('document_purpose', ''),
            "executive_summary": document_summary.get('executive_summary', ''),
            "key_procedures": document_summary.get('key_procedures', []),
            "safety_protocols": document_summary.get('safety_protocols', []),
            "critical_temperatures": document_summary.get('critical_temperatures', []),
            "maintenance_schedules": document_summary.get('maintenance_schedules', []),
            "hierarchical_sections": document_summary.get('hierarchical_sections', []),
            "page_count": document_data.get('page_count', 0),
            "confidence_score": 0.95,  # High confidence for AI-generated summaries
            "processing_timestamp": datetime.now().isoformat(),
            "hierarchical_document": True
        }
        
        return document_node
    
    async def process_entities_with_deduplication(self, entities: List[Dict[str, Any]], 
                                                  document_id: str) -> List[Dict[str, Any]]:
        """
        Process entities with comprehensive deduplication and normalization
        
        Args:
            entities: Raw extracted entities
            document_id: Document identifier
            
        Returns:
            Deduplicated and normalized entities
        """
        
        # Group entities by canonical name for deduplication
        canonical_groups = defaultdict(list)
        
        for entity in entities:
            # Normalize entity name
            canonical_name = self._normalize_entity_name(
                entity.get('entity_text', ''), 
                entity.get('entity_type', 'ENTITY')
            )
            entity['canonical_name'] = canonical_name
            canonical_groups[canonical_name].append(entity)
        
        # Deduplicate within each group
        deduplicated_entities = []
        
        for canonical_name, entity_group in canonical_groups.items():
            if len(entity_group) == 1:
                # No duplicates
                deduplicated_entities.append(entity_group[0])
            else:
                # Merge duplicates, keeping most complete version
                merged_entity = self._merge_duplicate_entities(entity_group)
                deduplicated_entities.append(merged_entity)
        
        # Cross-document deduplication (check existing Neo4j entities)
        cross_doc_deduplicated = await self._cross_document_deduplication(deduplicated_entities)
        
        return cross_doc_deduplicated
    
    async def create_hierarchical_relationships(self, entities: List[Dict[str, Any]], 
                                                document_id: str) -> List[Dict[str, Any]]:
        """
        Create hierarchical relationships between entities
        
        Args:
            entities: Processed entities
            document_id: Document identifier
            
        Returns:
            List of hierarchical relationships
        """
        
        relationships = []
        
        # Create hierarchy mapping
        hierarchy_map = {}
        for entity in entities:
            hierarchy_level = entity.get('hierarchy_level', 0)
            if hierarchy_level not in hierarchy_map:
                hierarchy_map[hierarchy_level] = []
            hierarchy_map[hierarchy_level].append(entity)
        
        # Create BELONGS_TO relationships
        for level in sorted(hierarchy_map.keys()):
            if level == 1:
                continue  # Top level, no parent
                
            current_entities = hierarchy_map[level]
            parent_entities = hierarchy_map.get(level - 1, [])
            
            for entity in current_entities:
                parent_name = entity.get('parent_entity', '')
                if parent_name:
                    # Find matching parent
                    for parent in parent_entities:
                        if (parent.get('canonical_name', '').lower() in parent_name.lower() or
                            parent_name.lower() in parent.get('canonical_name', '').lower()):
                            
                            relationships.append({
                                "source_entity": entity['canonical_name'],
                                "target_entity": parent['canonical_name'],
                                "relationship_type": "BELONGS_TO",
                                "hierarchy_level_source": level,
                                "hierarchy_level_target": level - 1,
                                "document_id": document_id,
                                "confidence": 0.9
                            })
                            break
        
        # Create semantic relationships based on QSR context
        semantic_relationships = self._create_semantic_relationships(entities, document_id)
        relationships.extend(semantic_relationships)
        
        return relationships
    
    async def store_hierarchical_structure(self, document_node: Dict[str, Any], 
                                           entities: List[Dict[str, Any]], 
                                           relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store hierarchical structure in Neo4j
        
        Args:
            document_node: Document node data
            entities: Processed entities
            relationships: Hierarchical relationships
            
        Returns:
            Storage results
        """
        
        try:
            # Connect to Neo4j
            if not self.neo4j_service.connected:
                await self.neo4j_service.connect()
            
            # Create document node
            doc_result = await self._create_document_node_neo4j(document_node)
            
            # Create entity nodes
            entity_results = []
            for entity in entities:
                entity_result = await self._create_entity_node_neo4j(entity)
                entity_results.append(entity_result)
            
            # Create relationships
            relationship_results = []
            for relationship in relationships:
                rel_result = await self._create_relationship_neo4j(relationship)
                relationship_results.append(rel_result)
            
            return {
                "document_created": doc_result,
                "entities_created": len([r for r in entity_results if r]),
                "relationships_created": len([r for r in relationship_results if r]),
                "total_entities": len(entities),
                "total_relationships": len(relationships)
            }
            
        except Exception as e:
            logger.error(f"Neo4j hierarchical storage failed: {e}")
            return {
                "error": str(e),
                "entities_created": 0,
                "relationships_created": 0
            }
    
    # Helper methods
    
    def _classify_document_type(self, filename: str, content: str, 
                                summary_data: Dict[str, Any]) -> str:
        """Classify document type based on content and filename"""
        
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        for doc_type, patterns in self.document_type_patterns.items():
            if any(pattern in filename_lower or pattern in content_lower for pattern in patterns):
                return doc_type
        
        return "technical_manual"
    
    def _classify_equipment_category(self, filename: str, content: str, 
                                     summary_data: Dict[str, Any]) -> str:
        """Classify equipment category"""
        
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        for category, patterns in self.equipment_categories.items():
            if any(pattern in filename_lower or pattern in content_lower for pattern in patterns):
                return category
        
        return "general_equipment"
    
    def _normalize_entity_name(self, entity_text: str, entity_type: str) -> str:
        """Normalize entity name using patterns"""
        
        entity_lower = entity_text.lower().strip()
        
        # Apply normalization patterns based on entity type
        if entity_type == "EQUIPMENT":
            for pattern, replacement in self.normalization_patterns["equipment_models"].items():
                entity_lower = re.sub(pattern, replacement, entity_lower, flags=re.IGNORECASE)
        elif entity_type == "PROCEDURE":
            for pattern, replacement in self.normalization_patterns["procedures"].items():
                entity_lower = re.sub(pattern, replacement, entity_lower, flags=re.IGNORECASE)
        elif entity_type == "TEMPERATURE":
            for pattern, replacement in self.normalization_patterns["temperatures"].items():
                entity_lower = re.sub(pattern, replacement, entity_lower, flags=re.IGNORECASE)
        
        # Clean up whitespace and formatting
        normalized = re.sub(r'\s+', ' ', entity_lower).strip()
        
        # Capitalize properly
        if entity_type in ["EQUIPMENT", "PROCEDURE"]:
            normalized = normalized.title()
        
        return normalized
    
    def _merge_duplicate_entities(self, entity_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge duplicate entities, keeping most complete version"""
        
        # Sort by completeness (more fields = more complete)
        sorted_entities = sorted(entity_group, 
                                key=lambda e: len([v for v in e.values() if v]), 
                                reverse=True)
        
        base_entity = sorted_entities[0].copy()
        
        # Merge additional information from other entities
        for entity in sorted_entities[1:]:
            for key, value in entity.items():
                if not base_entity.get(key) and value:
                    base_entity[key] = value
                elif key == 'page_reference' and value:
                    # Combine page references
                    existing_pages = base_entity.get('page_reference', [])
                    if not isinstance(existing_pages, list):
                        existing_pages = [existing_pages]
                    if isinstance(value, list):
                        existing_pages.extend(value)
                    else:
                        existing_pages.append(value)
                    base_entity['page_reference'] = list(set(existing_pages))
        
        # Mark as merged
        base_entity['merged_from_duplicates'] = len(entity_group)
        base_entity['confidence'] = min(0.95, base_entity.get('confidence', 0.8) + 0.1)
        
        return base_entity
    
    async def _cross_document_deduplication(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform cross-document deduplication"""
        
        # For now, return entities as-is
        # In future, query Neo4j to find existing entities and merge
        return entities
    
    def _create_semantic_relationships(self, entities: List[Dict[str, Any]], 
                                       document_id: str) -> List[Dict[str, Any]]:
        """Create semantic relationships based on QSR context"""
        
        relationships = []
        
        # Find equipment and procedure pairs
        equipment_entities = [e for e in entities if e.get('entity_type') == 'EQUIPMENT']
        procedure_entities = [e for e in entities if e.get('entity_type') == 'PROCEDURE']
        
        # Create PROCEDURE_FOR relationships
        for procedure in procedure_entities:
            for equipment in equipment_entities:
                # Check if procedure applies to equipment
                if (equipment.get('canonical_name', '').lower() in procedure.get('qsr_context', '').lower() or
                    any(keyword in procedure.get('entity_text', '').lower() 
                        for keyword in ['cleaning', 'maintenance', 'service', 'repair'])):
                    
                    relationships.append({
                        "source_entity": procedure['canonical_name'],
                        "target_entity": equipment['canonical_name'],
                        "relationship_type": "PROCEDURE_FOR",
                        "document_id": document_id,
                        "confidence": 0.8
                    })
        
        return relationships
    
    def _parse_summary_fallback(self, summary_text: str) -> Dict[str, Any]:
        """Fallback summary parsing if JSON fails"""
        
        return {
            "document_purpose": "Equipment documentation",
            "equipment_focus": "QSR equipment",
            "target_audience": "line_leads",
            "document_type": "technical_manual",
            "key_procedures": [],
            "safety_protocols": [],
            "critical_temperatures": [],
            "maintenance_schedules": [],
            "brand_context": "QSR",
            "qsr_category": "general_equipment",
            "executive_summary": summary_text[:200] + "...",
            "hierarchical_sections": []
        }
    
    async def _create_document_node_neo4j(self, document_node: Dict[str, Any]) -> bool:
        """Create document node in Neo4j"""
        
        try:
            with self.neo4j_service.driver.session() as session:
                query = """
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
                
                result = session.run(query, **document_node)
                return result.single() is not None
                
        except Exception as e:
            logger.error(f"Document node creation failed: {e}")
            return False
    
    async def _create_entity_node_neo4j(self, entity: Dict[str, Any]) -> bool:
        """Create entity node in Neo4j"""
        
        try:
            entity_type = entity.get('entity_type', 'ENTITY')
            
            with self.neo4j_service.driver.session() as session:
                query = f"""
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
                    equipment_category: $equipment_category,
                    extraction_timestamp: $extraction_timestamp,
                    processing_method: $processing_method
                }})
                RETURN e
                """
                
                result = session.run(query, **entity)
                return result.single() is not None
                
        except Exception as e:
            logger.error(f"Entity node creation failed: {e}")
            return False
    
    async def _create_relationship_neo4j(self, relationship: Dict[str, Any]) -> bool:
        """Create relationship in Neo4j"""
        
        try:
            with self.neo4j_service.driver.session() as session:
                rel_type = relationship['relationship_type']
                
                query = f"""
                MATCH (source {{canonical_name: $source_entity}}), 
                      (target {{canonical_name: $target_entity}})
                CREATE (source)-[r:{rel_type} {{
                    document_id: $document_id,
                    confidence: $confidence
                }}]->(target)
                RETURN r
                """
                
                result = session.run(query, 
                                   source_entity=relationship['source_entity'],
                                   target_entity=relationship['target_entity'],
                                   document_id=relationship['document_id'],
                                   confidence=relationship['confidence'])
                return result.single() is not None
                
        except Exception as e:
            logger.error(f"Relationship creation failed: {e}")
            return False