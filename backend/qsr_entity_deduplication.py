#!/usr/bin/env python3
"""
Phase 2B: QSR Entity Deduplication Engine
=========================================

Comprehensive entity deduplication system specifically tuned for QSR equipment
and procedures during Enterprise Bridge processing with bulletproof reliability.

Features:
- Fuzzy matching logic for equipment names ("1Grote Tool" vs "Grote Tool", "Taylor C602" vs "C602")
- Canonical name resolution keeping most complete and descriptive entity version
- Domain-specific patterns for QSR equipment models, procedure names, safety protocols
- Entity merging logic preserving all source references and relationships
- Seamless integration into existing bridge processing pipeline

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import difflib
from collections import defaultdict

from reliability_infrastructure import (
    circuit_breaker,
    transaction_manager,
    dead_letter_queue
)

logger = logging.getLogger(__name__)

class QSREntityType(Enum):
    """QSR-specific entity types"""
    EQUIPMENT = "equipment"
    PROCEDURE = "procedure"
    COMPONENT = "component"
    SAFETY_PROTOCOL = "safety_protocol"
    SPECIFICATION = "specification"
    BRAND = "brand"
    MODEL = "model"
    INGREDIENT = "ingredient"
    LOCATION = "location"

class MatchingStrategy(Enum):
    """Entity matching strategies"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    PATTERN = "pattern"
    CANONICAL = "canonical"

@dataclass
class QSREntityPattern:
    """QSR-specific entity pattern"""
    pattern_type: str
    regex_pattern: str
    canonical_format: str
    confidence_boost: float
    examples: List[str] = field(default_factory=list)

@dataclass
class EntityMatch:
    """Entity match result"""
    entity1_id: str
    entity2_id: str
    match_type: MatchingStrategy
    confidence: float
    canonical_name: str
    merge_recommendation: str
    match_details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MergedEntity:
    """Merged entity result"""
    merged_id: str
    canonical_name: str
    entity_type: QSREntityType
    source_entities: List[str]
    properties: Dict[str, Any]
    source_references: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    merge_metadata: Dict[str, Any] = field(default_factory=dict)

class QSREntityDeduplicationEngine:
    """
    Comprehensive entity deduplication system specifically tuned for QSR equipment
    and procedures with fuzzy matching and canonical name resolution.
    """
    
    def __init__(self):
        self.qsr_patterns = self._initialize_qsr_patterns()
        self.brand_aliases = self._initialize_brand_aliases()
        self.equipment_models = self._initialize_equipment_models()
        self.procedure_patterns = self._initialize_procedure_patterns()
        
        # Deduplication tracking
        self.entity_matches: List[EntityMatch] = []
        self.merged_entities: Dict[str, MergedEntity] = {}
        self.deduplication_stats = defaultdict(int)
        
        logger.info("🔧 QSR Entity Deduplication Engine initialized")
    
    def _initialize_qsr_patterns(self) -> List[QSREntityPattern]:
        """Initialize QSR-specific entity patterns"""
        return [
            # Equipment model patterns
            QSREntityPattern(
                pattern_type="equipment_model",
                regex_pattern=r"(Taylor|Electro\s*Freeze|Carpigiani|Stoelting)\s*(Model\s*)?([A-Z]?\d+[A-Z]?)",
                canonical_format="{brand} {model}",
                confidence_boost=0.9,
                examples=["Taylor C602", "Taylor Model C602", "Electro Freeze SL500"]
            ),
            
            # Equipment with numeric prefixes
            QSREntityPattern(
                pattern_type="numeric_prefix_equipment",
                regex_pattern=r"(\d+)\s*([A-Za-z][A-Za-z\s]+(?:Tool|Machine|Unit|System|Equipment))",
                canonical_format="{equipment_name}",
                confidence_boost=0.8,
                examples=["1Grote Tool", "2Taylor Unit", "3Cleaning System"]
            ),
            
            # Procedure patterns
            QSREntityPattern(
                pattern_type="procedure",
                regex_pattern=r"(Daily|Weekly|Monthly|Annual)?\s*(Cleaning|Maintenance|Service|Inspection)\s*(Procedure|Process|Protocol)?",
                canonical_format="{frequency} {action} Procedure",
                confidence_boost=0.7,
                examples=["Daily Cleaning", "Weekly Maintenance Procedure", "Monthly Service"]
            ),
            
            # Temperature specifications
            QSREntityPattern(
                pattern_type="temperature",
                regex_pattern=r"(\d+)\s*°?\s*([FfCc])\s*(Temperature)?",
                canonical_format="{value}°{unit} Temperature",
                confidence_boost=0.85,
                examples=["165F", "165°F Temperature", "74C"]
            ),
            
            # Safety protocols
            QSREntityPattern(
                pattern_type="safety",
                regex_pattern=r"(Safety|Warning|Caution|HACCP)\s*(Protocol|Procedure|Guideline|Warning)?",
                canonical_format="{type} {category}",
                confidence_boost=0.8,
                examples=["Safety Protocol", "HACCP Guideline", "Warning Procedure"]
            )
        ]
    
    def _initialize_brand_aliases(self) -> Dict[str, List[str]]:
        """Initialize brand name aliases and variations"""
        return {
            "taylor": ["taylor", "taylor company", "taylor freezer", "taylor ice cream"],
            "grote": ["grote", "grote company", "grote tool", "grote equipment"],
            "electro_freeze": ["electro freeze", "electro-freeze", "electrofreeze", "ef"],
            "carpigiani": ["carpigiani", "carpigiani gelato", "carpigiani ice cream"],
            "stoelting": ["stoelting", "stoelting frozen", "stoelting equipment"],
            "hobart": ["hobart", "hobart corp", "hobart equipment", "hobart foodservice"],
            "manitowoc": ["manitowoc", "manitowoc ice", "manitowoc foodservice"],
            "hoshizaki": ["hoshizaki", "hoshizaki ice", "hoshizaki america"]
        }
    
    def _initialize_equipment_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize equipment model specifications"""
        return {
            "taylor_c602": {
                "canonical_name": "Taylor C602",
                "aliases": ["c602", "taylor c602", "model c602", "taylor model c602", "c-602"],
                "type": "ice_cream_machine",
                "specifications": {"capacity": "high_volume", "type": "soft_serve"}
            },
            "grote_tool": {
                "canonical_name": "Grote Tool",
                "aliases": ["grote tool", "1grote tool", "grote equipment", "grote slicer"],
                "type": "food_preparation",
                "specifications": {"function": "slicing", "category": "preparation"}
            },
            "hobart_mixer": {
                "canonical_name": "Hobart Mixer",
                "aliases": ["hobart mixer", "hobart dough mixer", "commercial mixer"],
                "type": "mixing_equipment",
                "specifications": {"capacity": "commercial", "function": "mixing"}
            }
        }
    
    def _initialize_procedure_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize procedure name patterns"""
        return {
            "daily_cleaning": {
                "canonical_name": "Daily Cleaning Procedure",
                "aliases": ["daily cleaning", "daily clean", "daily sanitization", "end of day cleaning"],
                "frequency": "daily",
                "category": "cleaning"
            },
            "weekly_maintenance": {
                "canonical_name": "Weekly Maintenance Procedure", 
                "aliases": ["weekly maintenance", "weekly service", "weekly inspection"],
                "frequency": "weekly",
                "category": "maintenance"
            },
            "safety_protocol": {
                "canonical_name": "Safety Protocol",
                "aliases": ["safety procedure", "safety guidelines", "safety warning", "safety protocol"],
                "category": "safety"
            }
        }
    
    async def deduplicate_entities(self, entities: List[Dict[str, Any]], 
                                 transaction_id: str = None) -> Dict[str, Any]:
        """
        Main deduplication function that processes entities and returns merged results.
        """
        logger.info(f"🔄 Starting QSR entity deduplication for {len(entities)} entities")
        
        try:
            # Use circuit breaker protection for deduplication
            result = await circuit_breaker.call(
                self._execute_deduplication_pipeline,
                entities,
                transaction_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Entity deduplication failed: {e}")
            
            # Add to dead letter queue for retry
            dead_letter_queue.add_failed_operation(
                "entity_deduplication",
                {"entity_count": len(entities), "transaction_id": transaction_id},
                e
            )
            
            return {
                "success": False,
                "error": str(e),
                "original_count": len(entities),
                "deduplicated_count": len(entities),
                "duplicates_found": 0,
                "entities_merged": 0
            }
    
    async def _execute_deduplication_pipeline(self, entities: List[Dict[str, Any]], 
                                            transaction_id: str = None) -> Dict[str, Any]:
        """Execute the complete deduplication pipeline"""
        
        # Step 1: Normalize entity names and extract patterns
        normalized_entities = await self._normalize_entities(entities)
        
        # Step 2: Find potential matches using multiple strategies
        potential_matches = await self._find_potential_matches(normalized_entities)
        
        # Step 3: Score and validate matches
        validated_matches = await self._validate_matches(potential_matches)
        
        # Step 4: Create merged entities with canonical names
        merged_entities = await self._create_merged_entities(validated_matches, normalized_entities)
        
        # Step 5: Preserve source references and relationships
        final_entities = await self._preserve_entity_relationships(merged_entities, entities)
        
        # Compile results
        result = {
            "success": True,
            "original_count": len(entities),
            "deduplicated_count": len(final_entities),
            "duplicates_found": len(validated_matches),
            "entities_merged": len(merged_entities),
            "merged_entities": final_entities,
            "deduplication_stats": dict(self.deduplication_stats),
            "processing_metadata": {
                "transaction_id": transaction_id,
                "processing_time": datetime.now().isoformat(),
                "patterns_applied": len(self.qsr_patterns)
            }
        }
        
        logger.info(f"✅ Deduplication complete: {result['original_count']} → {result['deduplicated_count']} entities")
        return result
    
    async def _normalize_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize entity names and classify types"""
        normalized = []
        
        for entity in entities:
            normalized_entity = entity.copy()
            
            # Extract and normalize name
            entity_name = entity.get("name", entity.get("text", "")).strip()
            normalized_name = self._normalize_entity_name(entity_name)
            
            # Classify entity type
            entity_type = self._classify_entity_type(normalized_name, entity)
            
            # Apply QSR patterns
            canonical_name, pattern_info = self._apply_qsr_patterns(normalized_name, entity_type)
            
            # Update entity with normalized information
            normalized_entity.update({
                "original_name": entity_name,
                "normalized_name": normalized_name,
                "canonical_name": canonical_name,
                "qsr_entity_type": entity_type.value if entity_type else "unknown",
                "pattern_info": pattern_info,
                "normalization_metadata": {
                    "normalized_at": datetime.now().isoformat(),
                    "pattern_applied": pattern_info.get("pattern_type") if pattern_info else None
                }
            })
            
            normalized.append(normalized_entity)
            self.deduplication_stats["entities_normalized"] += 1
        
        return normalized
    
    def _normalize_entity_name(self, name: str) -> str:
        """Normalize entity name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove leading numbers (for cases like "1Grote Tool")
        normalized = re.sub(r'^\d+\s*', '', normalized)
        
        # Standardize punctuation
        normalized = re.sub(r'[^\w\s°]', ' ', normalized)
        
        # Remove common filler words
        filler_words = ["the", "a", "an", "model", "type", "series", "unit", "system"]
        words = normalized.split()
        normalized_words = [word for word in words if word not in filler_words]
        
        return ' '.join(normalized_words).strip()
    
    def _classify_entity_type(self, name: str, entity: Dict[str, Any]) -> Optional[QSREntityType]:
        """Classify entity type based on name and context"""
        name_lower = name.lower()
        
        # Check explicit entity type from entity data
        entity_type = entity.get("type", entity.get("entity_type", "")).lower()
        if entity_type:
            for qsr_type in QSREntityType:
                if qsr_type.value in entity_type:
                    return qsr_type
        
        # Classification based on keywords in name
        equipment_keywords = ["machine", "equipment", "fryer", "grill", "freezer", "mixer", "slicer", "tool"]
        procedure_keywords = ["cleaning", "maintenance", "procedure", "process", "protocol", "inspection"]
        component_keywords = ["pump", "motor", "valve", "sensor", "control", "panel", "compressor"]
        safety_keywords = ["safety", "warning", "caution", "hazard", "protocol", "guideline"]
        
        if any(keyword in name_lower for keyword in equipment_keywords):
            return QSREntityType.EQUIPMENT
        elif any(keyword in name_lower for keyword in procedure_keywords):
            return QSREntityType.PROCEDURE
        elif any(keyword in name_lower for keyword in component_keywords):
            return QSREntityType.COMPONENT
        elif any(keyword in name_lower for keyword in safety_keywords):
            return QSREntityType.SAFETY_PROTOCOL
        
        # Check for brand names
        for brand in self.brand_aliases.keys():
            if brand in name_lower:
                return QSREntityType.EQUIPMENT
        
        # Check for temperature/specification patterns
        if re.search(r'\d+\s*°?[fc]', name_lower) or "temperature" in name_lower:
            return QSREntityType.SPECIFICATION
        
        return None
    
    def _apply_qsr_patterns(self, name: str, entity_type: Optional[QSREntityType]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Apply QSR-specific patterns to generate canonical names"""
        
        for pattern in self.qsr_patterns:
            match = re.search(pattern.regex_pattern, name, re.IGNORECASE)
            
            if match:
                # Extract pattern groups
                groups = match.groups()
                
                # Generate canonical name based on pattern type
                canonical_name = self._generate_canonical_name(pattern, groups, name)
                
                pattern_info = {
                    "pattern_type": pattern.pattern_type,
                    "original_match": match.group(0),
                    "extracted_groups": groups,
                    "confidence_boost": pattern.confidence_boost
                }
                
                return canonical_name, pattern_info
        
        # Check equipment models
        for model_key, model_info in self.equipment_models.items():
            if name in model_info["aliases"]:
                return model_info["canonical_name"], {
                    "pattern_type": "equipment_model_alias",
                    "model_key": model_key,
                    "confidence_boost": 0.95
                }
        
        # Check procedure patterns
        for proc_key, proc_info in self.procedure_patterns.items():
            if name in proc_info["aliases"]:
                return proc_info["canonical_name"], {
                    "pattern_type": "procedure_alias",
                    "procedure_key": proc_key,
                    "confidence_boost": 0.9
                }
        
        # Default: capitalize first letters
        canonical_name = ' '.join(word.capitalize() for word in name.split())
        return canonical_name, None
    
    def _generate_canonical_name(self, pattern: QSREntityPattern, 
                                groups: Tuple[str, ...], original_name: str) -> str:
        """Generate canonical name from pattern and extracted groups"""
        
        if pattern.pattern_type == "equipment_model":
            brand, model_prefix, model = groups
            return f"{brand.title()} {model.upper()}"
        
        elif pattern.pattern_type == "numeric_prefix_equipment":
            number, equipment_name = groups
            return equipment_name.title()
        
        elif pattern.pattern_type == "procedure":
            frequency, action, procedure_suffix = groups
            freq_str = frequency.title() if frequency else ""
            action_str = action.title()
            return f"{freq_str} {action_str} Procedure".strip()
        
        elif pattern.pattern_type == "temperature":
            value, unit, temp_suffix = groups
            return f"{value}°{unit.upper()} Temperature"
        
        elif pattern.pattern_type == "safety":
            safety_type, category = groups
            return f"{safety_type.title()} {category.title() if category else 'Protocol'}"
        
        # Default: return formatted original name
        return ' '.join(word.capitalize() for word in original_name.split())
    
    async def _find_potential_matches(self, entities: List[Dict[str, Any]]) -> List[EntityMatch]:
        """Find potential entity matches using multiple strategies"""
        potential_matches = []
        
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i + 1:], i + 1):
                
                # Skip if different entity types (with some exceptions)
                if not self._should_compare_entities(entity1, entity2):
                    continue
                
                # Try different matching strategies
                matches = await self._try_matching_strategies(entity1, entity2)
                
                # Add high-confidence matches
                for match in matches:
                    if match.confidence >= 0.7:  # Threshold for potential matches
                        potential_matches.append(match)
                        self.deduplication_stats["potential_matches_found"] += 1
        
        return potential_matches
    
    def _should_compare_entities(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> bool:
        """Determine if two entities should be compared for matching"""
        type1 = entity1.get("qsr_entity_type")
        type2 = entity2.get("qsr_entity_type")
        
        # Always compare if types are the same
        if type1 == type2:
            return True
        
        # Allow cross-type matching for related types
        related_types = [
            {"equipment", "component"},
            {"procedure", "safety_protocol"},
            {"specification", "component"}
        ]
        
        for related_set in related_types:
            if type1 in related_set and type2 in related_set:
                return True
        
        return False
    
    async def _try_matching_strategies(self, entity1: Dict[str, Any], 
                                     entity2: Dict[str, Any]) -> List[EntityMatch]:
        """Try different matching strategies between two entities"""
        matches = []
        
        # Strategy 1: Exact canonical name match
        exact_match = self._exact_name_match(entity1, entity2)
        if exact_match:
            matches.append(exact_match)
        
        # Strategy 2: Fuzzy string matching
        fuzzy_match = self._fuzzy_name_match(entity1, entity2)
        if fuzzy_match:
            matches.append(fuzzy_match)
        
        # Strategy 3: Pattern-based matching
        pattern_match = self._pattern_based_match(entity1, entity2)
        if pattern_match:
            matches.append(pattern_match)
        
        # Strategy 4: Semantic/contextual matching
        semantic_match = await self._semantic_match(entity1, entity2)
        if semantic_match:
            matches.append(semantic_match)
        
        return matches
    
    def _exact_name_match(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> Optional[EntityMatch]:
        """Check for exact canonical name match"""
        name1 = entity1.get("canonical_name", "")
        name2 = entity2.get("canonical_name", "")
        
        if name1 and name2 and name1 == name2:
            return EntityMatch(
                entity1_id=entity1.get("id", entity1.get("entity_id", "")),
                entity2_id=entity2.get("id", entity2.get("entity_id", "")),
                match_type=MatchingStrategy.EXACT,
                confidence=1.0,
                canonical_name=name1,
                merge_recommendation="merge_exact",
                match_details={"match_reason": "exact_canonical_name"}
            )
        
        return None
    
    def _fuzzy_name_match(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> Optional[EntityMatch]:
        """Check for fuzzy string matching"""
        name1 = entity1.get("normalized_name", "")
        name2 = entity2.get("normalized_name", "")
        
        if not name1 or not name2:
            return None
        
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
        
        # QSR-specific similarity thresholds
        entity_type = entity1.get("qsr_entity_type", "")
        
        if entity_type == "equipment":
            threshold = 0.8  # High threshold for equipment
        elif entity_type == "procedure":
            threshold = 0.75  # Medium threshold for procedures  
        else:
            threshold = 0.85  # Default high threshold
        
        if similarity >= threshold:
            # Determine canonical name (prefer more complete version)
            canonical1 = entity1.get("canonical_name", "")
            canonical2 = entity2.get("canonical_name", "")
            canonical_name = canonical1 if len(canonical1) >= len(canonical2) else canonical2
            
            return EntityMatch(
                entity1_id=entity1.get("id", entity1.get("entity_id", "")),
                entity2_id=entity2.get("id", entity2.get("entity_id", "")),
                match_type=MatchingStrategy.FUZZY,
                confidence=similarity,
                canonical_name=canonical_name,
                merge_recommendation="merge_fuzzy",
                match_details={
                    "similarity_score": similarity,
                    "threshold_used": threshold,
                    "name1": name1,
                    "name2": name2
                }
            )
        
        return None
    
    def _pattern_based_match(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> Optional[EntityMatch]:
        """Check for pattern-based matching"""
        pattern1 = entity1.get("pattern_info", {})
        pattern2 = entity2.get("pattern_info", {})
        
        if not pattern1 or not pattern2:
            return None
        
        # Check if same pattern type applied
        if pattern1.get("pattern_type") == pattern2.get("pattern_type"):
            
            # Equipment model pattern matching
            if pattern1.get("pattern_type") == "equipment_model":
                groups1 = pattern1.get("extracted_groups", [])
                groups2 = pattern2.get("extracted_groups", [])
                
                # Match if same brand and similar model
                if (len(groups1) >= 3 and len(groups2) >= 3 and
                    groups1[0].lower() == groups2[0].lower() and  # Same brand
                    groups1[2].lower() == groups2[2].lower()):    # Same model
                    
                    canonical_name = f"{groups1[0].title()} {groups1[2].upper()}"
                    
                    return EntityMatch(
                        entity1_id=entity1.get("id", entity1.get("entity_id", "")),
                        entity2_id=entity2.get("id", entity2.get("entity_id", "")),
                        match_type=MatchingStrategy.PATTERN,
                        confidence=0.95,
                        canonical_name=canonical_name,
                        merge_recommendation="merge_pattern",
                        match_details={
                            "pattern_type": "equipment_model",
                            "brand": groups1[0],
                            "model": groups1[2]
                        }
                    )
        
        return None
    
    async def _semantic_match(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> Optional[EntityMatch]:
        """Check for semantic/contextual matching"""
        
        # Check for known aliases
        name1 = entity1.get("normalized_name", "")
        name2 = entity2.get("normalized_name", "")
        
        # Equipment model aliases
        for model_key, model_info in self.equipment_models.items():
            aliases = [alias.lower() for alias in model_info["aliases"]]
            if name1 in aliases and name2 in aliases:
                return EntityMatch(
                    entity1_id=entity1.get("id", entity1.get("entity_id", "")),
                    entity2_id=entity2.get("id", entity2.get("entity_id", "")),
                    match_type=MatchingStrategy.SEMANTIC,
                    confidence=0.9,
                    canonical_name=model_info["canonical_name"],
                    merge_recommendation="merge_semantic",
                    match_details={
                        "match_reason": "equipment_alias",
                        "model_key": model_key,
                        "aliases_matched": [name1, name2]
                    }
                )
        
        # Procedure aliases
        for proc_key, proc_info in self.procedure_patterns.items():
            aliases = [alias.lower() for alias in proc_info["aliases"]]
            if name1 in aliases and name2 in aliases:
                return EntityMatch(
                    entity1_id=entity1.get("id", entity1.get("entity_id", "")),
                    entity2_id=entity2.get("id", entity2.get("entity_id", "")),
                    match_type=MatchingStrategy.SEMANTIC,
                    confidence=0.85,
                    canonical_name=proc_info["canonical_name"],
                    merge_recommendation="merge_semantic",
                    match_details={
                        "match_reason": "procedure_alias",
                        "procedure_key": proc_key,
                        "aliases_matched": [name1, name2]
                    }
                )
        
        return None
    
    async def _validate_matches(self, potential_matches: List[EntityMatch]) -> List[EntityMatch]:
        """Validate and filter potential matches"""
        validated_matches = []
        
        # Group matches by entity pairs to avoid conflicts
        entity_pair_matches = defaultdict(list)
        
        for match in potential_matches:
            pair_key = tuple(sorted([match.entity1_id, match.entity2_id]))
            entity_pair_matches[pair_key].append(match)
        
        # For each entity pair, select the best match
        for pair_key, matches in entity_pair_matches.items():
            # Sort by confidence
            matches.sort(key=lambda m: m.confidence, reverse=True)
            
            # Take the highest confidence match
            best_match = matches[0]
            
            # Additional validation rules
            if self._validate_match_logic(best_match):
                validated_matches.append(best_match)
                self.deduplication_stats["matches_validated"] += 1
        
        return validated_matches
    
    def _validate_match_logic(self, match: EntityMatch) -> bool:
        """Validate match using business logic"""
        
        # Confidence threshold checks
        if match.match_type == MatchingStrategy.EXACT and match.confidence < 0.95:
            return False
        
        if match.match_type == MatchingStrategy.FUZZY and match.confidence < 0.75:
            return False
        
        # Prevent merging entities with very different names unless high confidence
        if match.match_type == MatchingStrategy.FUZZY:
            details = match.match_details
            name1 = details.get("name1", "")
            name2 = details.get("name2", "")
            
            # Check if names are too different in length
            if abs(len(name1) - len(name2)) > max(len(name1), len(name2)) * 0.5:
                if match.confidence < 0.9:
                    return False
        
        return True
    
    async def _create_merged_entities(self, validated_matches: List[EntityMatch], 
                                    entities: List[Dict[str, Any]]) -> List[MergedEntity]:
        """Create merged entities from validated matches"""
        merged_entities = []
        entities_to_merge = set()
        
        # Track which entities are part of merges
        for match in validated_matches:
            entities_to_merge.add(match.entity1_id)
            entities_to_merge.add(match.entity2_id)
        
        # Group entities by merge clusters
        merge_clusters = self._create_merge_clusters(validated_matches)
        
        # Create merged entity for each cluster
        for cluster_id, entity_ids in merge_clusters.items():
            cluster_entities = [e for e in entities if e.get("id", e.get("entity_id", "")) in entity_ids]
            
            if len(cluster_entities) >= 2:
                merged_entity = await self._merge_entity_cluster(cluster_entities, validated_matches)
                merged_entities.append(merged_entity)
                self.deduplication_stats["entities_merged"] += 1
        
        return merged_entities
    
    def _create_merge_clusters(self, matches: List[EntityMatch]) -> Dict[str, Set[str]]:
        """Create clusters of entities that should be merged together"""
        clusters = defaultdict(set)
        entity_to_cluster = {}
        cluster_counter = 0
        
        for match in matches:
            entity1 = match.entity1_id
            entity2 = match.entity2_id
            
            # Check if either entity is already in a cluster
            cluster1 = entity_to_cluster.get(entity1)
            cluster2 = entity_to_cluster.get(entity2)
            
            if cluster1 is not None and cluster2 is not None:
                # Merge clusters if different
                if cluster1 != cluster2:
                    # Merge cluster2 into cluster1
                    clusters[cluster1].update(clusters[cluster2])
                    # Update entity mappings
                    for eid in clusters[cluster2]:
                        entity_to_cluster[eid] = cluster1
                    del clusters[cluster2]
                # Add entities to existing cluster
                clusters[cluster1].add(entity1)
                clusters[cluster1].add(entity2)
                
            elif cluster1 is not None:
                # Add entity2 to entity1's cluster
                clusters[cluster1].add(entity2)
                entity_to_cluster[entity2] = cluster1
                
            elif cluster2 is not None:
                # Add entity1 to entity2's cluster  
                clusters[cluster2].add(entity1)
                entity_to_cluster[entity1] = cluster2
                
            else:
                # Create new cluster
                cluster_id = f"cluster_{cluster_counter}"
                clusters[cluster_id].add(entity1)
                clusters[cluster_id].add(entity2)
                entity_to_cluster[entity1] = cluster_id
                entity_to_cluster[entity2] = cluster_id
                cluster_counter += 1
        
        return dict(clusters)
    
    async def _merge_entity_cluster(self, entities: List[Dict[str, Any]], 
                                  matches: List[EntityMatch]) -> MergedEntity:
        """Merge a cluster of entities into a single merged entity"""
        
        # Find the match that involves entities in this cluster
        cluster_entity_ids = {e.get("id", e.get("entity_id", "")) for e in entities}
        relevant_match = None
        
        for match in matches:
            if match.entity1_id in cluster_entity_ids and match.entity2_id in cluster_entity_ids:
                relevant_match = match
                break
        
        # Determine canonical name (prefer from match, fallback to most complete)
        if relevant_match:
            canonical_name = relevant_match.canonical_name
        else:
            # Choose the most complete canonical name
            canonical_names = [e.get("canonical_name", "") for e in entities if e.get("canonical_name")]
            canonical_name = max(canonical_names, key=len) if canonical_names else entities[0].get("name", "Merged Entity")
        
        # Determine entity type
        entity_types = [e.get("qsr_entity_type") for e in entities if e.get("qsr_entity_type")]
        if entity_types:
            entity_type = QSREntityType(max(set(entity_types), key=entity_types.count))
        else:
            entity_type = QSREntityType.EQUIPMENT  # Default
        
        # Combine properties from all entities
        combined_properties = {}
        for entity in entities:
            for key, value in entity.items():
                if key not in ["id", "entity_id", "name", "text"]:
                    if key not in combined_properties:
                        combined_properties[key] = value
                    elif isinstance(value, list) and isinstance(combined_properties[key], list):
                        combined_properties[key].extend(value)
                    elif value != combined_properties[key]:
                        # Handle conflicting values
                        if not isinstance(combined_properties[key], list):
                            combined_properties[key] = [combined_properties[key]]
                        if value not in combined_properties[key]:
                            combined_properties[key].append(value)
        
        # Collect source references
        source_references = []
        for entity in entities:
            source_ref = {
                "original_id": entity.get("id", entity.get("entity_id", "")),
                "original_name": entity.get("name", entity.get("text", "")),
                "source_document": entity.get("source_document", entity.get("document_id", "")),
                "page_references": entity.get("page_reference", entity.get("page_references", [])),
                "entity_properties": {k: v for k, v in entity.items() if k not in combined_properties}
            }
            source_references.append(source_ref)
        
        # Generate merged entity ID
        merged_id = f"merged_{hash(canonical_name) % 100000}_{int(datetime.now().timestamp()) % 10000}"
        
        merged_entity = MergedEntity(
            merged_id=merged_id,
            canonical_name=canonical_name,
            entity_type=entity_type,
            source_entities=[e.get("id", e.get("entity_id", "")) for e in entities],
            properties=combined_properties,
            source_references=source_references,
            relationships=[],  # Will be populated in next step
            merge_metadata={
                "merge_strategy": relevant_match.match_type.value if relevant_match else "manual",
                "merge_confidence": relevant_match.confidence if relevant_match else 0.8,
                "merged_at": datetime.now().isoformat(),
                "source_count": len(entities)
            }
        )
        
        return merged_entity
    
    async def _preserve_entity_relationships(self, merged_entities: List[MergedEntity], 
                                           original_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preserve and update entity relationships after merging"""
        
        # Create mapping from original entity IDs to merged entities
        entity_mapping = {}
        merged_entity_lookup = {}
        
        for merged in merged_entities:
            merged_entity_lookup[merged.merged_id] = merged
            for source_id in merged.source_entities:
                entity_mapping[source_id] = merged.merged_id
        
        # Process relationships for merged entities
        for merged in merged_entities:
            relationships = []
            
            # Collect relationships from all source entities
            for source_id in merged.source_entities:
                source_entity = next((e for e in original_entities 
                                    if e.get("id", e.get("entity_id", "")) == source_id), None)
                
                if source_entity:
                    entity_relationships = source_entity.get("relationships", [])
                    for rel in entity_relationships:
                        # Update relationship targets if they were merged
                        updated_rel = rel.copy()
                        
                        target_id = rel.get("target", rel.get("target_id", ""))
                        if target_id in entity_mapping:
                            updated_rel["target"] = entity_mapping[target_id]
                            updated_rel["target_id"] = entity_mapping[target_id]
                        
                        source_rel_id = rel.get("source", rel.get("source_id", ""))
                        if source_rel_id in entity_mapping:
                            updated_rel["source"] = entity_mapping[source_rel_id]
                            updated_rel["source_id"] = entity_mapping[source_rel_id]
                        
                        relationships.append(updated_rel)
            
            # Deduplicate relationships
            unique_relationships = []
            seen_relationships = set()
            
            for rel in relationships:
                rel_key = (rel.get("source", ""), rel.get("target", ""), rel.get("type", ""))
                if rel_key not in seen_relationships:
                    seen_relationships.add(rel_key)
                    unique_relationships.append(rel)
            
            merged.relationships = unique_relationships
        
        # Create final entity list (merged entities + non-merged entities)
        final_entities = []
        processed_entity_ids = set()
        
        # Add merged entities
        for merged in merged_entities:
            final_entity = {
                "id": merged.merged_id,
                "entity_id": merged.merged_id,
                "name": merged.canonical_name,
                "text": merged.canonical_name,
                "type": merged.entity_type.value,
                "entity_type": merged.entity_type.value,
                "relationships": merged.relationships,
                "source_references": merged.source_references,
                "merge_metadata": merged.merge_metadata,
                **merged.properties
            }
            final_entities.append(final_entity)
            
            # Track processed entities
            for source_id in merged.source_entities:
                processed_entity_ids.add(source_id)
        
        # Add non-merged entities
        for entity in original_entities:
            entity_id = entity.get("id", entity.get("entity_id", ""))
            if entity_id not in processed_entity_ids:
                # Update relationships for non-merged entities
                updated_entity = entity.copy()
                
                if "relationships" in updated_entity:
                    updated_relationships = []
                    for rel in updated_entity["relationships"]:
                        updated_rel = rel.copy()
                        
                        target_id = rel.get("target", rel.get("target_id", ""))
                        if target_id in entity_mapping:
                            updated_rel["target"] = entity_mapping[target_id]
                            updated_rel["target_id"] = entity_mapping[target_id]
                        
                        updated_relationships.append(updated_rel)
                    
                    updated_entity["relationships"] = updated_relationships
                
                final_entities.append(updated_entity)
        
        return final_entities
    
    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        return {
            "statistics": dict(self.deduplication_stats),
            "total_entities_processed": self.deduplication_stats.get("entities_processed", 0),
            "duplicates_found": self.deduplication_stats.get("duplicates_found", 0),
            "entities_merged": self.deduplication_stats.get("entities_merged", 0),
            "canonical_names_created": self.deduplication_stats.get("canonical_names_created", 0),
            "patterns_configured": len(self.qsr_patterns),
            "equipment_models": len(self.equipment_models),
            "procedure_patterns": len(self.procedure_patterns),
            "brand_aliases": len(self.brand_aliases),
            "last_updated": datetime.now().isoformat()
        }
    
    def calculate_similarity(self, entity1_name: str, entity2_name: str) -> float:
        """Calculate similarity between two entity names"""
        try:
            # Simple similarity calculation for testing
            from difflib import SequenceMatcher
            
            # Normalize names
            name1 = entity1_name.lower().strip()
            name2 = entity2_name.lower().strip()
            
            # Basic similarity using SequenceMatcher
            basic_similarity = SequenceMatcher(None, name1, name2).ratio()
            
            # QSR-specific enhancements
            enhanced_similarity = basic_similarity
            
            # Check for brand matching
            for brand in self.brand_aliases.keys():
                if brand.lower() in name1 and brand.lower() in name2:
                    enhanced_similarity += 0.2
            
            # Check for model number matching
            import re
            model_pattern = r'[A-Z]?\d{2,4}[A-Z]?'
            models1 = re.findall(model_pattern, name1.upper())
            models2 = re.findall(model_pattern, name2.upper())
            
            if models1 and models2 and any(m1 == m2 for m1 in models1 for m2 in models2):
                enhanced_similarity += 0.3
            
            return min(enhanced_similarity, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Error calculating similarity: {e}")
            return 0.0
    
    def resolve_canonical_name(self, entity_name: str) -> str:
        """Resolve canonical name for an entity"""
        try:
            # Simple canonical name resolution for testing
            normalized = entity_name.strip()
            
            # Apply QSR-specific canonicalization
            for brand, aliases in self.brand_aliases.items():
                for alias in aliases:
                    if alias.lower() in normalized.lower():
                        normalized = normalized.replace(alias, brand)
                        break
            
            # Extract model patterns
            import re
            model_pattern = r'([A-Za-z]+)\s*([A-Z]?\d{2,4}[A-Z]?)'
            match = re.search(model_pattern, normalized)
            
            if match:
                brand = match.group(1).title()
                model = match.group(2).upper()
                return f"{brand} {model}"
            
            return normalized.title()
            
        except Exception as e:
            logger.error(f"❌ Error resolving canonical name: {e}")
            return entity_name
    
    def recognize_qsr_pattern(self, term: str) -> str:
        """Recognize QSR-specific patterns"""
        try:
            term_lower = term.lower()
            
            # Check brand patterns
            for brand in self.brand_aliases.keys():
                if brand.lower() in term_lower:
                    return "equipment_brand"
            
            # Check model number patterns
            import re
            if re.search(r'[A-Z]?\d{2,4}[A-Z]?', term.upper()):
                return "model_number"
            
            # Check equipment type patterns
            equipment_types = ["fryer", "grill", "mixer", "slicer", "soft serve", "ice cream"]
            for equipment_type in equipment_types:
                if equipment_type in term_lower:
                    return "equipment_type"
            
            # Check procedure patterns
            procedure_terms = ["cleaning", "maintenance", "procedure", "protocol"]
            for procedure_term in procedure_terms:
                if procedure_term in term_lower:
                    return "procedure_type"
            
            # Check safety patterns
            safety_terms = ["safety", "haccp", "food safety", "sanitization"]
            for safety_term in safety_terms:
                if safety_term in term_lower:
                    return "safety_protocol"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"❌ Error recognizing QSR pattern: {e}")
            return "unknown"
    
    @property
    def similarity_threshold(self) -> float:
        """Get similarity threshold for matching"""
        return 0.8  # 80% similarity threshold


# Global instance
qsr_entity_deduplication = QSREntityDeduplicationEngine()

logger.info("🚀 QSR Entity Deduplication Engine ready")