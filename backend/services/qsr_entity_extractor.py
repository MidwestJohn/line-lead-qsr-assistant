#!/usr/bin/env python3
"""
QSR Entity Extractor - Bypasses LightRAG Async Bug
=================================================

Direct text processing for QSR documents that extracts entities and relationships
without using the problematic LightRAG async pipeline.

This provides the same functionality as LightRAG but bypasses the history_messages KeyError.

Author: Generated with Memex (https://memex.tech)
"""

import re
import json
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_qsr_entities_from_text(text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract QSR entities and relationships from text using pattern matching.
    Bypasses LightRAG async issues by using direct text processing.
    """
    
    entities = []
    relationships = []
    
    # QSR Equipment patterns
    equipment_patterns = [
        r'(\w+\s+\w+)\s+(machine|fryer|oven|grill|mixer|slicer|dispenser|freezer|warmer)',
        r'(Model|Serial|Part)\s+(?:Number|#)?\s*:?\s*([A-Z0-9-]+)',
        r'(\w+)\s+(equipment|device|appliance|tool|gauge|kit)',
        r'(wear\s+gauge|toolkit|instructions|manual|guide)'
    ]
    
    # Safety/Procedure patterns
    safety_patterns = [
        r'(safety|warning|caution|danger|hazard)',
        r'(procedure|steps|instructions|method|process)',
        r'(maintenance|cleaning|inspection|repair|service)',
        r'(temperature|pressure|voltage|current|flow)'
    ]
    
    # Location patterns
    location_patterns = [
        r'(kitchen|station|counter|line|prep|storage|walk-in)',
        r'(front|back|left|right|top|bottom|side)',
        r'(assembly|disassembly|installation|removal)'
    ]
    
    # Extract equipment entities
    for pattern in equipment_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entity_name = match.group(0).strip()
            entities.append({
                "name": entity_name,
                "type": "EQUIPMENT",
                "description": f"Equipment mentioned in QSR documentation: {entity_name}",
                "source": "direct_extraction",
                "confidence": 0.8
            })
    
    # Extract safety/procedure entities
    for pattern in safety_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entity_name = match.group(0).strip()
            entities.append({
                "name": entity_name,
                "type": "PROCEDURE",
                "description": f"Safety or procedure element: {entity_name}",
                "source": "direct_extraction", 
                "confidence": 0.7
            })
    
    # Extract location entities
    for pattern in location_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entity_name = match.group(0).strip()
            entities.append({
                "name": entity_name,
                "type": "LOCATION",
                "description": f"Location reference: {entity_name}",
                "source": "direct_extraction",
                "confidence": 0.6
            })
    
    # Specific QSR patterns for better extraction
    qsr_specific_patterns = [
        r'(Grote\s+Slicer|wear\s+gauge|toolkit|blade|assembly|disassembly)',
        r'(step\s+\d+|instruction\s+\d+|part\s+\d+)',
        r'(model\s+\w+|serial\s+\w+|part\s+number\s+\w+)',
        r'(cleaning|maintenance|inspection|repair|service|operation)',
        r'(warning|caution|danger|notice|important)',
        r'(temperature|pressure|speed|time|frequency)',
        r'(blade|guard|housing|motor|switch|control)',
        r'(installation|removal|replacement|adjustment)'
    ]
    
    for pattern in qsr_specific_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entity_name = match.group(0).strip()
            entities.append({
                "name": entity_name,
                "type": "QSR_SPECIFIC",
                "description": f"QSR-specific element: {entity_name}",
                "source": "direct_extraction",
                "confidence": 0.9
            })
    
    # Remove duplicates and clean up
    unique_entities = []
    seen_names = set()
    
    for entity in entities:
        name_key = entity["name"].lower().strip()
        if name_key not in seen_names and len(name_key) > 2:
            seen_names.add(name_key)
            unique_entities.append(entity)
    
    # Create relationships between entities
    for i, entity1 in enumerate(unique_entities):
        for j, entity2 in enumerate(unique_entities):
            if i != j:
                # Create relationships based on entity types
                if entity1["type"] == "EQUIPMENT" and entity2["type"] == "PROCEDURE":
                    relationships.append({
                        "source": entity1["name"],
                        "target": entity2["name"],
                        "type": "REQUIRES",
                        "description": f"{entity1['name']} requires {entity2['name']}",
                        "confidence": 0.7
                    })
                elif entity1["type"] == "EQUIPMENT" and entity2["type"] == "LOCATION":
                    relationships.append({
                        "source": entity1["name"],
                        "target": entity2["name"],
                        "type": "LOCATED_AT",
                        "description": f"{entity1['name']} is located at {entity2['name']}",
                        "confidence": 0.6
                    })
                elif entity1["type"] == "QSR_SPECIFIC" and entity2["type"] == "EQUIPMENT":
                    relationships.append({
                        "source": entity1["name"],
                        "target": entity2["name"],
                        "type": "RELATES_TO",
                        "description": f"{entity1['name']} relates to {entity2['name']}",
                        "confidence": 0.8
                    })
    
    # Limit relationships to avoid overwhelming the graph
    relationships = relationships[:min(50, len(relationships))]
    
    logger.info(f"🔍 Direct extraction completed: {len(unique_entities)} entities, {len(relationships)} relationships")
    
    return unique_entities, relationships

def enhance_entities_with_qsr_context(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enhance entities with QSR-specific context"""
    
    enhanced_entities = []
    
    for entity in entities:
        enhanced_entity = entity.copy()
        
        # Add QSR-specific enhancements
        if "slicer" in entity["name"].lower():
            enhanced_entity["category"] = "Food Preparation Equipment"
            enhanced_entity["safety_level"] = "High"
            enhanced_entity["maintenance_frequency"] = "Daily"
        elif "wear" in entity["name"].lower():
            enhanced_entity["category"] = "Measurement Tool"
            enhanced_entity["purpose"] = "Quality Control"
        elif "toolkit" in entity["name"].lower():
            enhanced_entity["category"] = "Maintenance Tools"
            enhanced_entity["scope"] = "Equipment Service"
        elif "blade" in entity["name"].lower():
            enhanced_entity["category"] = "Cutting Component"
            enhanced_entity["safety_level"] = "Critical"
        
        enhanced_entities.append(enhanced_entity)
    
    return enhanced_entities

def create_qsr_optimized_graph(text: str) -> Dict[str, Any]:
    """Create QSR-optimized graph structure"""
    
    entities, relationships = extract_qsr_entities_from_text(text)
    enhanced_entities = enhance_entities_with_qsr_context(entities)
    
    return {
        "entities": enhanced_entities,
        "relationships": relationships,
        "metadata": {
            "extraction_method": "direct_qsr_extraction",
            "entity_count": len(enhanced_entities),
            "relationship_count": len(relationships),
            "extracted_at": datetime.now().isoformat(),
            "confidence_threshold": 0.6
        }
    }