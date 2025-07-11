#!/usr/bin/env python3
"""
Document Context Service
=======================

Enhances the Line Lead QSR system with comprehensive document-level context integration.
Provides hierarchical document understanding, contextual summarization, and multi-level
retrieval capabilities to bridge granular entity data with broader document purpose.

Key Features:
- Document summarization during upload pipeline
- Hierarchical entity structure in Neo4j
- Context-aware prompt enhancement
- Hybrid retrieval combining granular and contextual information

Author: Generated with Memex (https://memex.tech)
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """QSR document type classification"""
    SERVICE_MANUAL = "service_manual"
    CLEANING_GUIDE = "cleaning_guide"
    SAFETY_PROTOCOL = "safety_protocol"
    INSTALLATION_GUIDE = "installation_guide"
    TROUBLESHOOTING = "troubleshooting"
    SPECIFICATIONS = "specifications"
    TRAINING_MANUAL = "training_manual"
    REGULATORY_COMPLIANCE = "regulatory_compliance"

class QSRCategory(Enum):
    """QSR equipment and process categories"""
    ICE_CREAM_MACHINES = "ice_cream_machines"
    FRYERS = "fryers" 
    GRILLS = "grills"
    OVENS = "ovens"
    REFRIGERATION = "refrigeration"
    CLEANING_SYSTEMS = "cleaning_systems"
    BEVERAGE_EQUIPMENT = "beverage_equipment"
    FOOD_PREP = "food_prep"
    SAFETY_EQUIPMENT = "safety_equipment"

@dataclass
class DocumentSummary:
    """Comprehensive document-level summary"""
    document_id: str
    filename: str
    document_type: DocumentType
    qsr_category: QSRCategory
    target_audience: str  # "line_leads", "technicians", "managers"
    brand_context: str    # "McDonald's", "Burger King", etc.
    equipment_focus: List[str]  # Primary equipment mentioned
    
    # Executive summary
    purpose: str
    key_procedures: List[str]
    safety_protocols: List[str]
    critical_temperatures: List[str]
    maintenance_schedules: List[str]
    
    # Hierarchical structure
    table_of_contents: List[Dict[str, Any]]
    section_summaries: Dict[str, str]  # section_name -> summary
    
    # Metadata
    page_count: int
    processing_timestamp: str
    confidence_score: float

@dataclass
class HierarchicalEntity:
    """Entity with hierarchical document context"""
    entity_id: str
    entity_name: str
    entity_type: str
    
    # Hierarchical context
    document_context: DocumentSummary
    section_path: List[str]  # ["Manual", "Temperature Controls", "Setting Procedures"]
    page_number: int
    
    # Contextual information
    contextual_description: str
    related_procedures: List[str]
    safety_considerations: List[str]
    qsr_specific_notes: List[str]

class DocumentContextService:
    """
    Service for extracting and managing document-level context in QSR systems
    """
    
    def __init__(self, neo4j_service=None):
        self.neo4j_service = neo4j_service
        self.document_summaries = {}  # Cache for document summaries
        self.hierarchy_cache = {}     # Cache for hierarchical structures
        
        # QSR-specific patterns for document classification
        self.document_type_patterns = {
            DocumentType.SERVICE_MANUAL: [
                "service manual", "maintenance manual", "repair guide",
                "service guide", "technician manual"
            ],
            DocumentType.CLEANING_GUIDE: [
                "cleaning", "sanitizing", "hygiene", "wash", "disinfect"
            ],
            DocumentType.SAFETY_PROTOCOL: [
                "safety", "warning", "caution", "hazard", "emergency"
            ],
            DocumentType.INSTALLATION_GUIDE: [
                "installation", "setup", "mounting", "assembly"
            ],
            DocumentType.TROUBLESHOOTING: [
                "troubleshooting", "problem", "fault", "error", "diagnostic"
            ],
            DocumentType.SPECIFICATIONS: [
                "specifications", "specs", "technical data", "parameters"
            ]
        }
        
        self.qsr_category_patterns = {
            QSRCategory.ICE_CREAM_MACHINES: [
                "ice cream", "frozen dessert", "soft serve", "taylor", "c602", "c708"
            ],
            QSRCategory.FRYERS: [
                "fryer", "frying", "oil", "basket", "filtration"
            ],
            QSRCategory.GRILLS: [
                "grill", "grilling", "burger", "patty", "clamshell"
            ],
            QSRCategory.REFRIGERATION: [
                "refrigerator", "freezer", "cold storage", "temperature control"
            ],
            QSRCategory.CLEANING_SYSTEMS: [
                "cleaning system", "wash station", "sanitizer", "chemical feed"
            ]
        }
        
        # Brand-specific indicators
        self.brand_patterns = {
            "McDonald's": ["mcdonald", "mcdonalds", "golden arches", "big mac"],
            "Burger King": ["burger king", "whopper", "bk"],
            "KFC": ["kfc", "kentucky fried", "colonel"],
            "Taco Bell": ["taco bell", "chalupa", "crunch"]
        }
    
    async def process_document_for_context(self, doc_path: Path, content: str = None) -> DocumentSummary:
        """
        Extract comprehensive document-level context during upload pipeline
        """
        try:
            logger.info(f"🔍 Processing document context for: {doc_path.name}")
            
            # Extract document content if not provided
            if not content:
                content = await self._extract_document_content(doc_path)
            
            # Generate document ID
            document_id = self._generate_document_id(doc_path)
            
            # Classify document type and category
            doc_type = self._classify_document_type(content, doc_path.name)
            qsr_category = self._classify_qsr_category(content, doc_path.name)
            
            # Extract brand context
            brand_context = self._extract_brand_context(content, doc_path.name)
            
            # Extract target audience
            target_audience = self._extract_target_audience(content)
            
            # Extract equipment focus
            equipment_focus = self._extract_equipment_focus(content)
            
            # Generate executive summary
            purpose = await self._extract_document_purpose(content, doc_type)
            key_procedures = self._extract_key_procedures(content)
            safety_protocols = self._extract_safety_protocols(content)
            critical_temperatures = self._extract_critical_temperatures(content)
            maintenance_schedules = self._extract_maintenance_schedules(content)
            
            # Extract hierarchical structure
            table_of_contents = await self._extract_table_of_contents(doc_path, content)
            section_summaries = await self._generate_section_summaries(doc_path, content, table_of_contents)
            
            # Get page count
            page_count = await self._get_page_count(doc_path)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(content, doc_type, qsr_category)
            
            # Create document summary
            summary = DocumentSummary(
                document_id=document_id,
                filename=doc_path.name,
                document_type=doc_type,
                qsr_category=qsr_category,
                target_audience=target_audience,
                brand_context=brand_context,
                equipment_focus=equipment_focus,
                purpose=purpose,
                key_procedures=key_procedures,
                safety_protocols=safety_protocols,
                critical_temperatures=critical_temperatures,
                maintenance_schedules=maintenance_schedules,
                table_of_contents=table_of_contents,
                section_summaries=section_summaries,
                page_count=page_count,
                processing_timestamp=datetime.now().isoformat(),
                confidence_score=confidence_score
            )
            
            # Cache the summary
            self.document_summaries[document_id] = summary
            
            # Store in Neo4j
            await self._store_document_summary_in_neo4j(summary)
            
            logger.info(f"✅ Document context processed: {doc_type.value}/{qsr_category.value} confidence={confidence_score:.2f}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Document context processing failed: {e}")
            raise
    
    async def enhance_entity_with_hierarchy(self, entity_data: Dict[str, Any], 
                                          document_id: str) -> HierarchicalEntity:
        """
        Enhance extracted entity with hierarchical document context
        """
        try:
            # Get document summary
            doc_summary = self.document_summaries.get(document_id)
            if not doc_summary:
                # Try to load from Neo4j
                doc_summary = await self._load_document_summary_from_neo4j(document_id)
            
            if not doc_summary:
                logger.warning(f"No document summary found for: {document_id}")
                return None
            
            # Extract entity information
            entity_id = entity_data.get("id", "")
            entity_name = entity_data.get("name", "")
            entity_type = entity_data.get("type", "")
            
            # Determine section path from entity context
            section_path = self._determine_section_path(entity_data, doc_summary)
            
            # Extract page number
            page_number = entity_data.get("page_number", 1)
            
            # Generate contextual description
            contextual_description = await self._generate_contextual_description(
                entity_data, doc_summary, section_path
            )
            
            # Extract related procedures
            related_procedures = self._extract_related_procedures(entity_data, doc_summary)
            
            # Extract safety considerations
            safety_considerations = self._extract_safety_considerations(entity_data, doc_summary)
            
            # Extract QSR-specific notes
            qsr_specific_notes = self._extract_qsr_specific_notes(entity_data, doc_summary)
            
            # Create hierarchical entity
            hierarchical_entity = HierarchicalEntity(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                document_context=doc_summary,
                section_path=section_path,
                page_number=page_number,
                contextual_description=contextual_description,
                related_procedures=related_procedures,
                safety_considerations=safety_considerations,
                qsr_specific_notes=qsr_specific_notes
            )
            
            return hierarchical_entity
            
        except Exception as e:
            logger.error(f"❌ Entity hierarchy enhancement failed: {e}")
            return None
    
    async def generate_context_aware_prompt(self, query: str, entities: List[Dict], 
                                          user_context: str = "line_lead") -> str:
        """
        Generate context-aware prompts that include document-level information
        """
        try:
            # Identify relevant documents from entities
            document_ids = set()
            for entity in entities:
                doc_id = entity.get("document_id")
                if doc_id:
                    document_ids.add(doc_id)
            
            # Build contextual prompt sections
            prompt_sections = []
            
            # Add user context
            if user_context == "line_lead":
                prompt_sections.append(
                    "Context: You are assisting a QSR line lead with equipment maintenance and operations. "
                    "Provide practical, actionable guidance focused on food safety, efficiency, and compliance."
                )
            
            # Add document context for each relevant document
            for doc_id in document_ids:
                doc_summary = self.document_summaries.get(doc_id)
                if doc_summary:
                    doc_context = self._build_document_context_string(doc_summary)
                    prompt_sections.append(f"Document Context: {doc_context}")
            
            # Add hierarchical entity context
            entity_contexts = []
            for entity in entities:
                if entity.get("hierarchical_context"):
                    entity_context = self._build_entity_context_string(entity)
                    entity_contexts.append(entity_context)
            
            if entity_contexts:
                prompt_sections.append("Relevant Information:\n" + "\n".join(entity_contexts))
            
            # Add the user query
            prompt_sections.append(f"Question: {query}")
            
            # Combine sections
            enhanced_prompt = "\n\n".join(prompt_sections)
            
            logger.info(f"🎯 Generated context-aware prompt for query: {query[:50]}...")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"❌ Context-aware prompt generation failed: {e}")
            return query  # Fallback to original query
    
    async def hybrid_retrieval(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Implement hybrid retrieval combining granular entities and document context
        """
        try:
            results = {
                "granular_entities": [],
                "document_summaries": [],
                "hierarchical_paths": [],
                "contextual_recommendations": []
            }
            
            # 1. Granular entity search (existing functionality)
            granular_results = await self._search_granular_entities(query, top_k)
            results["granular_entities"] = granular_results
            
            # 2. Document-level context search
            document_results = await self._search_document_summaries(query, top_k // 2)
            results["document_summaries"] = document_results
            
            # 3. Hierarchical relationship traversal
            hierarchy_results = await self._traverse_hierarchical_relationships(query, granular_results)
            results["hierarchical_paths"] = hierarchy_results
            
            # 4. Contextual recommendations
            contextual_recs = await self._generate_contextual_recommendations(
                query, granular_results, document_results
            )
            results["contextual_recommendations"] = contextual_recs
            
            logger.info(f"🔍 Hybrid retrieval: {len(granular_results)} entities, "
                       f"{len(document_results)} documents, {len(hierarchy_results)} paths")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Hybrid retrieval failed: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _extract_document_content(self, doc_path: Path) -> str:
        """Extract text content from document"""
        try:
            if doc_path.suffix.lower() == '.pdf':
                doc = fitz.open(str(doc_path))
                content = ""
                for page in doc:
                    content += page.get_text()
                doc.close()
                return content
            else:
                # Handle other file types
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return ""
    
    def _generate_document_id(self, doc_path: Path) -> str:
        """Generate unique document identifier"""
        import hashlib
        return hashlib.md5(f"{doc_path.name}_{doc_path.stat().st_mtime}".encode()).hexdigest()[:12]
    
    def _classify_document_type(self, content: str, filename: str) -> DocumentType:
        """Classify document type based on content and filename"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        scores = {}
        for doc_type, patterns in self.document_type_patterns.items():
            score = 0
            for pattern in patterns:
                score += content_lower.count(pattern)
                if pattern in filename_lower:
                    score += 3  # Boost filename matches
            scores[doc_type] = score
        
        # Return type with highest score, default to SERVICE_MANUAL
        if scores:
            return max(scores, key=scores.get)
        return DocumentType.SERVICE_MANUAL
    
    def _classify_qsr_category(self, content: str, filename: str) -> QSRCategory:
        """Classify QSR category based on content and filename"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        scores = {}
        for category, patterns in self.qsr_category_patterns.items():
            score = 0
            for pattern in patterns:
                score += content_lower.count(pattern)
                if pattern in filename_lower:
                    score += 3  # Boost filename matches
            scores[category] = score
        
        # Return category with highest score, default to ICE_CREAM_MACHINES
        if scores:
            return max(scores, key=scores.get)
        return QSRCategory.ICE_CREAM_MACHINES
    
    def _extract_brand_context(self, content: str, filename: str) -> str:
        """Extract brand context from content"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        for brand, patterns in self.brand_patterns.items():
            for pattern in patterns:
                if pattern in content_lower or pattern in filename_lower:
                    return brand
        
        return "Generic QSR"
    
    def _extract_target_audience(self, content: str) -> str:
        """Determine target audience from content"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["line lead", "shift manager", "crew leader"]):
            return "line_leads"
        elif any(term in content_lower for term in ["technician", "service", "repair"]):
            return "technicians"
        elif any(term in content_lower for term in ["manager", "supervisor", "director"]):
            return "managers"
        else:
            return "line_leads"  # Default for QSR context
    
    def _extract_equipment_focus(self, content: str) -> List[str]:
        """Extract primary equipment mentioned in document"""
        equipment_patterns = {
            "Taylor C602": ["taylor", "c602"],
            "Fryer": ["fryer", "frying"],
            "Grill": ["grill", "grilling"],
            "Oven": ["oven", "baking"],
            "Refrigerator": ["refrigerator", "cooler"]
        }
        
        content_lower = content.lower()
        equipment_found = []
        
        for equipment, patterns in equipment_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                equipment_found.append(equipment)
        
        return equipment_found[:5]  # Limit to top 5
    
    async def _extract_document_purpose(self, content: str, doc_type: DocumentType) -> str:
        """Extract the main purpose of the document"""
        content_lower = content.lower()
        
        # Extract first few paragraphs that often contain purpose
        sentences = content[:1000].split('.')
        purpose_sentences = []
        
        for sentence in sentences[:5]:
            if any(keyword in sentence.lower() for keyword in 
                   ["purpose", "manual", "guide", "instruction", "procedure"]):
                purpose_sentences.append(sentence.strip())
        
        if purpose_sentences:
            return ". ".join(purpose_sentences[:2]) + "."
        
        # Fallback based on document type
        fallback_purposes = {
            DocumentType.SERVICE_MANUAL: "Service and maintenance procedures for QSR equipment",
            DocumentType.CLEANING_GUIDE: "Cleaning and sanitization procedures for food safety compliance",
            DocumentType.SAFETY_PROTOCOL: "Safety protocols and emergency procedures for QSR operations"
        }
        
        return fallback_purposes.get(doc_type, "QSR operational procedures and guidelines")
    
    def _extract_key_procedures(self, content: str) -> List[str]:
        """Extract key procedures from content"""
        procedures = []
        
        # Look for numbered procedures or steps
        procedure_patterns = [
            r"(?:procedure|steps?):\s*\n((?:\d+\..*?\n?)+)",
            r"(?:to|how to)\s+([^.]+cleaning[^.]*)",
            r"(?:to|how to)\s+([^.]+maintenance[^.]*)",
            r"(?:to|how to)\s+([^.]+temperature[^.]*)"
        ]
        
        for pattern in procedure_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                procedure_text = match.group(1).strip()
                if len(procedure_text) > 10:  # Filter out very short matches
                    procedures.append(procedure_text[:100] + "..." if len(procedure_text) > 100 else procedure_text)
        
        return procedures[:5]  # Limit to top 5
    
    def _extract_safety_protocols(self, content: str) -> List[str]:
        """Extract safety protocols from content"""
        safety_protocols = []
        
        # Look for safety-related content
        safety_patterns = [
            r"(?:warning|caution|danger):\s*([^.]+)",
            r"(?:always|never|do not)\s+([^.]+)",
            r"(?:before|after)\s+(?:operating|servicing|cleaning)\s+([^.]+)"
        ]
        
        for pattern in safety_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                safety_text = match.group(0).strip()
                if len(safety_text) > 10:
                    safety_protocols.append(safety_text[:100] + "..." if len(safety_text) > 100 else safety_text)
        
        return safety_protocols[:5]  # Limit to top 5
    
    def _extract_critical_temperatures(self, content: str) -> List[str]:
        """Extract critical temperature information"""
        temperatures = []
        
        # Look for temperature specifications
        temp_patterns = [
            r"temperature.*?(\d+)\s*(?:degrees?|°F|°C)",
            r"(\d+)\s*(?:degrees?|°F|°C).*?(?:setting|required|maintain)",
            r"set.*?to.*?(\d+)\s*(?:degrees?|°F|°C)"
        ]
        
        for pattern in temp_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                temp_text = match.group(0).strip()
                temperatures.append(temp_text)
        
        return list(set(temperatures))[:5]  # Remove duplicates, limit to 5
    
    def _extract_maintenance_schedules(self, content: str) -> List[str]:
        """Extract maintenance schedule information"""
        schedules = []
        
        # Look for maintenance frequency information
        schedule_patterns = [
            r"(?:daily|weekly|monthly|annually)\s+(?:clean|maintenance|check|inspect)",
            r"every\s+\d+\s+(?:days?|weeks?|months?)\s+[^.]+",
            r"(?:schedule|frequency).*?(?:clean|maintenance)[^.]*"
        ]
        
        for pattern in schedule_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                schedule_text = match.group(0).strip()
                if len(schedule_text) > 10:
                    schedules.append(schedule_text[:100] + "..." if len(schedule_text) > 100 else schedule_text)
        
        return schedules[:5]  # Limit to top 5
    
    async def _extract_table_of_contents(self, doc_path: Path, content: str) -> List[Dict[str, Any]]:
        """Extract table of contents structure"""
        toc = []
        
        try:
            # Use PyMuPDF to get TOC if available
            doc = fitz.open(str(doc_path))
            if doc.get_toc():
                for level, title, page in doc.get_toc():
                    toc.append({
                        "level": level,
                        "title": title.strip(),
                        "page": page,
                        "type": "toc_entry"
                    })
            doc.close()
        except:
            # Fallback to text-based extraction
            lines = content.split('\n')
            for i, line in enumerate(lines[:50]):  # Check first 50 lines
                line = line.strip()
                if re.match(r'^\d+\.?\s+[A-Z]', line) and len(line) < 100:
                    toc.append({
                        "level": 1,
                        "title": line,
                        "page": 1,  # Approximate
                        "type": "text_extracted"
                    })
        
        return toc[:20]  # Limit to first 20 entries
    
    async def _generate_section_summaries(self, doc_path: Path, content: str, 
                                        toc: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate summaries for each major section"""
        summaries = {}
        
        # If we have TOC, extract content for each section
        if toc:
            for i, section in enumerate(toc[:5]):  # Limit to first 5 sections
                section_title = section["title"]
                
                # Extract section content (simplified approach)
                section_start = content.find(section_title)
                if section_start > -1:
                    # Find next section or take next 500 chars
                    next_section_start = len(content)
                    if i + 1 < len(toc):
                        next_title = toc[i + 1]["title"]
                        next_pos = content.find(next_title, section_start + len(section_title))
                        if next_pos > -1:
                            next_section_start = next_pos
                    
                    section_content = content[section_start:min(section_start + 500, next_section_start)]
                    
                    # Generate simple summary (first sentence or two)
                    sentences = section_content.split('.')
                    summary = '. '.join(sentences[:2]).strip()
                    if summary:
                        summaries[section_title] = summary + "."
        
        return summaries
    
    async def _get_page_count(self, doc_path: Path) -> int:
        """Get document page count"""
        try:
            if doc_path.suffix.lower() == '.pdf':
                doc = fitz.open(str(doc_path))
                count = len(doc)
                doc.close()
                return count
            else:
                return 1  # Assume single page for non-PDF
        except:
            return 1
    
    def _calculate_confidence_score(self, content: str, doc_type: DocumentType, 
                                  qsr_category: QSRCategory) -> float:
        """Calculate confidence score for classification"""
        content_lower = content.lower()
        
        # Base score
        score = 0.5
        
        # Boost for QSR-specific terms
        qsr_terms = ["qsr", "restaurant", "food service", "kitchen", "crew", "shift"]
        for term in qsr_terms:
            if term in content_lower:
                score += 0.1
        
        # Boost for technical content
        tech_terms = ["temperature", "procedure", "maintenance", "cleaning", "safety"]
        for term in tech_terms:
            if term in content_lower:
                score += 0.05
        
        # Boost for structured content
        if re.search(r'\d+\..*(?:\n.*\d+\.)', content):  # Numbered lists
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _store_document_summary_in_neo4j(self, summary: DocumentSummary) -> None:
        """Store document summary in Neo4j with hierarchical structure"""
        try:
            if not self.neo4j_service or not self.neo4j_service.connected:
                logger.warning("Neo4j not available for document summary storage")
                return
            
            # Create Document node with comprehensive metadata
            document_query = """
            MERGE (d:Document {document_id: $document_id})
            SET d.filename = $filename,
                d.document_type = $document_type,
                d.qsr_category = $qsr_category,
                d.target_audience = $target_audience,
                d.brand_context = $brand_context,
                d.equipment_focus = $equipment_focus,
                d.purpose = $purpose,
                d.key_procedures = $key_procedures,
                d.safety_protocols = $safety_protocols,
                d.critical_temperatures = $critical_temperatures,
                d.maintenance_schedules = $maintenance_schedules,
                d.page_count = $page_count,
                d.confidence_score = $confidence_score,
                d.processing_timestamp = $processing_timestamp,
                d.hierarchical_document = true
            RETURN d
            """
            
            params = {
                "document_id": summary.document_id,
                "filename": summary.filename,
                "document_type": summary.document_type.value,
                "qsr_category": summary.qsr_category.value,
                "target_audience": summary.target_audience,
                "brand_context": summary.brand_context,
                "equipment_focus": summary.equipment_focus,
                "purpose": summary.purpose,
                "key_procedures": summary.key_procedures,
                "safety_protocols": summary.safety_protocols,
                "critical_temperatures": summary.critical_temperatures,
                "maintenance_schedules": summary.maintenance_schedules,
                "page_count": summary.page_count,
                "confidence_score": summary.confidence_score,
                "processing_timestamp": summary.processing_timestamp
            }
            
            self.neo4j_service.execute_query(document_query, params)
            
            # Create Section nodes for hierarchical structure
            for section_name, section_summary in summary.section_summaries.items():
                section_query = """
                MATCH (d:Document {document_id: $document_id})
                MERGE (s:Section {name: $section_name, document_id: $document_id})
                SET s.summary = $section_summary,
                    s.document_type = $document_type
                MERGE (d)-[:HAS_SECTION]->(s)
                RETURN s
                """
                
                section_params = {
                    "document_id": summary.document_id,
                    "section_name": section_name,
                    "section_summary": section_summary,
                    "document_type": summary.document_type.value
                }
                
                self.neo4j_service.execute_query(section_query, section_params)
            
            # Create Equipment nodes and relationships
            for equipment in summary.equipment_focus:
                equipment_query = """
                MATCH (d:Document {document_id: $document_id})
                MERGE (e:Equipment {name: $equipment_name})
                SET e.category = $qsr_category
                MERGE (d)-[:COVERS_EQUIPMENT]->(e)
                RETURN e
                """
                
                equipment_params = {
                    "document_id": summary.document_id,
                    "equipment_name": equipment,
                    "qsr_category": summary.qsr_category.value
                }
                
                self.neo4j_service.execute_query(equipment_query, equipment_params)
            
            logger.info(f"✅ Document summary stored in Neo4j: {summary.document_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store document summary in Neo4j: {e}")
    
    async def _load_document_summary_from_neo4j(self, document_id: str) -> Optional[DocumentSummary]:
        """Load document summary from Neo4j"""
        try:
            if not self.neo4j_service or not self.neo4j_service.connected:
                return None
            
            query = """
            MATCH (d:Document {document_id: $document_id})
            OPTIONAL MATCH (d)-[:HAS_SECTION]->(s:Section)
            RETURN d, collect(s) as sections
            """
            
            results = self.neo4j_service.execute_query(query, {"document_id": document_id})
            
            if results.get("success") and results.get("records"):
                record = results["records"][0]
                doc_data = record["d"]
                sections_data = record["sections"]
                
                # Reconstruct section summaries
                section_summaries = {}
                for section in sections_data:
                    if section:
                        section_summaries[section["name"]] = section.get("summary", "")
                
                # Create DocumentSummary object
                summary = DocumentSummary(
                    document_id=doc_data["document_id"],
                    filename=doc_data["filename"],
                    document_type=DocumentType(doc_data["document_type"]),
                    qsr_category=QSRCategory(doc_data["qsr_category"]),
                    target_audience=doc_data["target_audience"],
                    brand_context=doc_data["brand_context"],
                    equipment_focus=doc_data["equipment_focus"],
                    purpose=doc_data["purpose"],
                    key_procedures=doc_data["key_procedures"],
                    safety_protocols=doc_data["safety_protocols"],
                    critical_temperatures=doc_data["critical_temperatures"],
                    maintenance_schedules=doc_data["maintenance_schedules"],
                    table_of_contents=[],  # TODO: Store and retrieve TOC
                    section_summaries=section_summaries,
                    page_count=doc_data["page_count"],
                    processing_timestamp=doc_data["processing_timestamp"],
                    confidence_score=doc_data["confidence_score"]
                )
                
                # Cache the loaded summary
                self.document_summaries[document_id] = summary
                return summary
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to load document summary from Neo4j: {e}")
            return None
    
    def _determine_section_path(self, entity_data: Dict[str, Any], 
                               doc_summary: DocumentSummary) -> List[str]:
        """Determine hierarchical section path for entity"""
        section_path = [doc_summary.filename]
        
        # Try to match entity context to document sections
        entity_context = entity_data.get("context", "").lower()
        
        for section_name in doc_summary.section_summaries.keys():
            if any(word in entity_context for word in section_name.lower().split()):
                section_path.append(section_name)
                break
        
        # Add equipment-specific path if available
        entity_name = entity_data.get("name", "").lower()
        for equipment in doc_summary.equipment_focus:
            if equipment.lower() in entity_name:
                section_path.append(f"{equipment} Components")
                break
        
        return section_path
    
    async def _generate_contextual_description(self, entity_data: Dict[str, Any], 
                                             doc_summary: DocumentSummary, 
                                             section_path: List[str]) -> str:
        """Generate contextual description for entity"""
        entity_name = entity_data.get("name", "")
        entity_type = entity_data.get("type", "")
        
        # Build context-rich description
        context_parts = []
        
        # Add document context
        context_parts.append(f"From {doc_summary.brand_context} {doc_summary.document_type.value}")
        
        # Add hierarchical path
        if len(section_path) > 1:
            path_str = " → ".join(section_path[1:])  # Skip filename
            context_parts.append(f"Located in: {path_str}")
        
        # Add QSR-specific context
        if doc_summary.target_audience == "line_leads":
            context_parts.append("For QSR line lead operations")
        
        # Add equipment context if relevant
        for equipment in doc_summary.equipment_focus:
            if equipment.lower() in entity_name.lower():
                context_parts.append(f"Related to {equipment} equipment")
                break
        
        return ". ".join(context_parts) + "."
    
    def _extract_related_procedures(self, entity_data: Dict[str, Any], 
                                   doc_summary: DocumentSummary) -> List[str]:
        """Extract procedures related to the entity"""
        entity_name = entity_data.get("name", "").lower()
        related_procedures = []
        
        # Check if entity appears in key procedures
        for procedure in doc_summary.key_procedures:
            if any(word in procedure.lower() for word in entity_name.split()):
                related_procedures.append(procedure)
        
        return related_procedures[:3]  # Limit to 3 most relevant
    
    def _extract_safety_considerations(self, entity_data: Dict[str, Any], 
                                     doc_summary: DocumentSummary) -> List[str]:
        """Extract safety considerations related to the entity"""
        entity_name = entity_data.get("name", "").lower()
        safety_considerations = []
        
        # Check if entity appears in safety protocols
        for protocol in doc_summary.safety_protocols:
            if any(word in protocol.lower() for word in entity_name.split()):
                safety_considerations.append(protocol)
        
        return safety_considerations[:3]  # Limit to 3 most relevant
    
    def _extract_qsr_specific_notes(self, entity_data: Dict[str, Any], 
                                   doc_summary: DocumentSummary) -> List[str]:
        """Extract QSR-specific notes for the entity"""
        notes = []
        
        # Add category-specific notes
        if doc_summary.qsr_category == QSRCategory.ICE_CREAM_MACHINES:
            notes.append("Critical for dessert service continuity")
            notes.append("Temperature control essential for food safety")
        elif doc_summary.qsr_category == QSRCategory.FRYERS:
            notes.append("High-volume cooking equipment")
            notes.append("Oil quality affects product consistency")
        
        # Add brand-specific notes
        if doc_summary.brand_context == "McDonald's":
            notes.append("Follow McDonald's operational standards")
        
        return notes[:3]  # Limit to 3 notes
    
    def _build_document_context_string(self, doc_summary: DocumentSummary) -> str:
        """Build a context string for document summary"""
        context_parts = []
        
        context_parts.append(f"{doc_summary.brand_context} {doc_summary.document_type.value}")
        context_parts.append(f"covering {doc_summary.qsr_category.value}")
        
        if doc_summary.equipment_focus:
            equipment_list = ", ".join(doc_summary.equipment_focus[:3])
            context_parts.append(f"focusing on: {equipment_list}")
        
        context_parts.append(f"Purpose: {doc_summary.purpose}")
        
        return ". ".join(context_parts)
    
    def _build_entity_context_string(self, entity: Dict[str, Any]) -> str:
        """Build context string for hierarchical entity"""
        hierarchical_context = entity.get("hierarchical_context", {})
        
        if not hierarchical_context:
            return f"• {entity.get('name', '')}: {entity.get('description', '')}"
        
        context_parts = []
        context_parts.append(f"• {entity.get('name', '')}")
        
        if hierarchical_context.get("section_path"):
            path = " → ".join(hierarchical_context["section_path"])
            context_parts.append(f"(from {path})")
        
        if hierarchical_context.get("contextual_description"):
            context_parts.append(f": {hierarchical_context['contextual_description']}")
        
        return " ".join(context_parts)
    
    async def _search_granular_entities(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search for granular entities (existing functionality)"""
        try:
            if not self.neo4j_service or not self.neo4j_service.connected:
                return []
            
            # Use existing entity search or implement basic entity retrieval
            entity_query = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS toLower($query) 
               OR toLower(n.description) CONTAINS toLower($query)
            RETURN n, labels(n) as types
            LIMIT $limit
            """
            
            results = self.neo4j_service.execute_query(entity_query, {
                "query": query,
                "limit": top_k
            })
            
            entities = []
            if results.get("success") and results.get("records"):
                for record in results["records"]:
                    node = record["n"]
                    node_types = record["types"]
                    
                    entities.append({
                        "name": node.get("name", ""),
                        "description": node.get("description", ""),
                        "type": node_types[0] if node_types else "Entity",
                        "properties": dict(node)
                    })
            
            return entities
            
        except Exception as e:
            logger.error(f"❌ Granular entity search failed: {e}")
            return []
    
    async def _search_document_summaries(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search document summaries for contextual matches"""
        try:
            query_lower = query.lower()
            matching_summaries = []
            
            # Search cached summaries
            for doc_id, summary in self.document_summaries.items():
                score = 0
                
                # Check purpose
                if any(word in summary.purpose.lower() for word in query_lower.split()):
                    score += 3
                
                # Check equipment focus
                for equipment in summary.equipment_focus:
                    if equipment.lower() in query_lower:
                        score += 2
                
                # Check key procedures
                for procedure in summary.key_procedures:
                    if any(word in procedure.lower() for word in query_lower.split()):
                        score += 1
                
                if score > 0:
                    matching_summaries.append({
                        "document_id": doc_id,
                        "summary": summary,
                        "relevance_score": score
                    })
            
            # Sort by relevance and return top results
            matching_summaries.sort(key=lambda x: x["relevance_score"], reverse=True)
            return matching_summaries[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Document summary search failed: {e}")
            return []
    
    async def _traverse_hierarchical_relationships(self, query: str, 
                                                  entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Traverse hierarchical relationships to find related context"""
        try:
            if not self.neo4j_service or not self.neo4j_service.connected:
                return []
            
            hierarchy_paths = []
            
            for entity in entities:
                entity_name = entity.get("name", "")
                
                # Find hierarchical relationships
                hierarchy_query = """
                MATCH path = (d:Document)-[:HAS_SECTION]->(s:Section)-[:CONTAINS*0..2]->(n)
                WHERE toLower(n.name) CONTAINS toLower($entity_name)
                RETURN d, s, nodes(path) as path_nodes
                LIMIT 3
                """
                
                results = self.neo4j_service.execute_query(hierarchy_query, {
                    "entity_name": entity_name
                })
                
                if results.get("success") and results.get("records"):
                    for record in results["records"]:
                        document = record["d"]
                        section = record["s"]
                        path_nodes = record["path_nodes"]
                        
                        hierarchy_paths.append({
                            "entity": entity_name,
                            "document": document.get("filename", ""),
                            "section": section.get("name", ""),
                            "path_length": len(path_nodes),
                            "context": f"Found in {document.get('filename', '')} → {section.get('name', '')}"
                        })
            
            return hierarchy_paths
            
        except Exception as e:
            logger.error(f"❌ Hierarchical relationship traversal failed: {e}")
            return []
    
    async def _generate_contextual_recommendations(self, query: str, 
                                                  granular_results: List[Dict[str, Any]], 
                                                  document_results: List[Dict[str, Any]]) -> List[str]:
        """Generate contextual recommendations based on search results"""
        recommendations = []
        
        try:
            # Analyze query for intent
            query_lower = query.lower()
            
            # Temperature-related recommendations
            if any(word in query_lower for word in ["temperature", "temp", "heat", "cold"]):
                recommendations.append("Check critical temperature settings in equipment specifications")
                recommendations.append("Verify food safety temperature compliance")
            
            # Cleaning-related recommendations
            if any(word in query_lower for word in ["clean", "sanitize", "wash"]):
                recommendations.append("Follow daily cleaning checklist procedures")
                recommendations.append("Ensure proper chemical concentrations")
            
            # Maintenance-related recommendations
            if any(word in query_lower for word in ["maintenance", "repair", "service"]):
                recommendations.append("Review maintenance schedule requirements")
                recommendations.append("Check for any safety precautions before servicing")
            
            # Add document-specific recommendations
            for doc_result in document_results[:2]:
                summary = doc_result.get("summary")
                if summary:
                    if summary.target_audience == "line_leads":
                        recommendations.append(f"Consult {summary.filename} for line lead procedures")
                    
                    if summary.safety_protocols:
                        recommendations.append("Review safety protocols before proceeding")
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            logger.error(f"❌ Contextual recommendations generation failed: {e}")
            return []

# Global instance
document_context_service = DocumentContextService()