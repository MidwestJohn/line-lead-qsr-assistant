#!/usr/bin/env python3
"""
Multi-Modal Citation Service
Provides synchronized voice + visual content citations for QSR manual references
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF
import base64
from io import BytesIO
import hashlib

logger = logging.getLogger(__name__)

class CitationType:
    """Types of citations that can be extracted from documents"""
    IMAGE = "image"
    DIAGRAM = "diagram" 
    TABLE = "table"
    TEXT_SECTION = "text_section"
    SAFETY_WARNING = "safety_warning"
    PROCEDURE_STEP = "procedure_step"

class VisualCitation:
    """Represents a visual citation with metadata and timing"""
    
    def __init__(self, citation_type: str, source_document: str, page_number: int, 
                 reference_text: str, content_data: bytes = None, timing: str = "during_speech",
                 highlight_area: Optional[str] = None, coordinates: Optional[Dict] = None):
        self.citation_type = citation_type
        self.source_document = source_document
        self.page_number = page_number
        self.reference_text = reference_text
        self.content_data = content_data
        self.timing = timing
        self.highlight_area = highlight_area
        self.coordinates = coordinates
        self.citation_id = self._generate_citation_id()
        
    def _generate_citation_id(self) -> str:
        """Generate unique citation ID"""
        content = f"{self.source_document}_{self.page_number}_{self.reference_text}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary for JSON serialization"""
        return {
            "citation_id": self.citation_id,
            "type": self.citation_type,
            "source": self.source_document,
            "page": self.page_number,
            "reference": self.reference_text,
            "timing": self.timing,
            "highlight_area": self.highlight_area,
            "coordinates": self.coordinates,
            "has_content": bool(self.content_data)
        }

class MultiModalCitationService:
    """
    Service for extracting and coordinating multi-modal citations from QSR manuals
    """
    
    def __init__(self, uploaded_docs_path: str = "uploaded_docs"):
        self.uploaded_docs_path = Path(uploaded_docs_path)
        self.citation_cache = {}  # Cache extracted citations
        self.document_index = {}  # Index of document content
        
        # Reference detection patterns for QSR manuals
        self.reference_patterns = {
            "diagram": [
                r"(?:see|check|refer to|shown in|diagram|figure)\s+(\d+(?:\.\d+)?[A-Z]?)",
                r"diagram\s+(\d+(?:\.\d+)?[A-Z]?)",
                r"figure\s+(\d+(?:\.\d+)?[A-Z]?)",
                r"(?:see|check)\s+(?:the\s+)?diagram"
            ],
            "table": [
                r"(?:table|chart|specification)\s+(\d+(?:\.\d+)?)",
                r"temperature\s+(?:table|chart|specifications?)",
                r"(?:see|check|refer to)\s+(?:the\s+)?(?:temperature|spec|specifications?)\s+(?:table|chart)",
                r"(?:shown in|see)\s+(?:the\s+)?(?:table|chart)"
            ],
            "page": [
                r"(?:page|pg\.?)\s+(\d+)",
                r"see\s+page\s+(\d+)",
                r"on\s+page\s+(\d+)"
            ],
            "section": [
                r"section\s+(\d+(?:\.\d+)*)",
                r"(?:see|refer to)\s+section\s+(\d+(?:\.\d+)*)"
            ],
            "temperature": [
                r"(?:set|adjust|check|temperature)\s+(?:to\s+)?(\d+)\s*(?:degrees?|°F?|°C?)",
                r"(\d+)\s*(?:degrees?|°F|°C)",
                r"temperature.*?(\d+).*?(?:degrees?|°F|°C)"
            ],
            "safety": [
                r"(?:warning|caution|danger|safety|precaution)",
                r"(?:always|never|do not|ensure|make sure)",
                r"(?:before|after)\s+(?:operating|servicing|cleaning)"
            ]
        }
        
        # QSR equipment-specific visual patterns
        self.equipment_visual_patterns = {
            "compressor": ["compressor", "refrigeration unit", "cooling system"],
            "temperature_sensor": ["temperature sensor", "thermometer", "temp probe"],
            "control_panel": ["control panel", "display", "interface", "buttons"],
            "cleaning_procedure": ["cleaning", "sanitizing", "disassembly"],
            "safety_equipment": ["safety", "protective", "emergency"]
        }
        
    async def extract_citations_from_response(self, voice_text: str, current_equipment: str = None) -> Dict[str, Any]:
        """
        Extract visual citations from voice response text and find matching content
        """
        try:
            citations = []
            manual_references = []
            
            # Detect reference patterns in voice text
            references = self._detect_references_in_text(voice_text)
            
            # For each detected reference, find corresponding visual content
            for ref in references:
                citation = await self._find_visual_content_for_reference(ref, current_equipment)
                if citation:
                    citations.append(citation)
                    
                    # Cache the citation for content retrieval
                    self._cache_citation(citation)
                    
                    # Also create manual reference
                    manual_ref = {
                        "page": citation.page_number,
                        "section": ref.get("section", ""),
                        "document": citation.source_document,
                        "reference_type": citation.citation_type
                    }
                    manual_references.append(manual_ref)
            
            # Additional context-based visual suggestions
            context_citations = await self._suggest_context_based_visuals(voice_text, current_equipment)
            for citation in context_citations:
                self._cache_citation(citation)
            citations.extend(context_citations)
            
            return {
                "voice_text": voice_text,
                "visual_citations": [c.to_dict() for c in citations],
                "manual_references": manual_references,
                "citation_count": len(citations),
                "synchronized": True
            }
            
        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")
            return {
                "voice_text": voice_text,
                "visual_citations": [],
                "manual_references": [],
                "error": str(e)
            }
    
    def _detect_references_in_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect reference patterns in voice text
        """
        references = []
        text_lower = text.lower()
        
        for ref_type, patterns in self.reference_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    ref_data = {
                        "type": ref_type,
                        "matched_text": match.group(0),
                        "position": match.span(),
                        "value": match.group(1) if match.groups() else None
                    }
                    
                    # Extract context around the reference
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    ref_data["context"] = text[start:end].strip()
                    
                    references.append(ref_data)
        
        return references
    
    async def _find_visual_content_for_reference(self, reference: Dict[str, Any], 
                                                current_equipment: str = None) -> Optional[VisualCitation]:
        """
        Find actual visual content that matches the reference
        """
        try:
            ref_type = reference["type"]
            ref_value = reference.get("value")
            context = reference.get("context", "")
            
            # Find relevant documents
            documents = await self._find_relevant_documents(current_equipment)
            
            for doc_path in documents:
                # Check if document is already indexed
                if doc_path not in self.document_index:
                    await self._index_document_content(doc_path)
                
                doc_index = self.document_index.get(doc_path, {})
                
                # Search for matching content based on reference type
                if ref_type == "diagram" or ref_type == "figure":
                    citation = await self._find_diagram_content(doc_path, ref_value, context)
                elif ref_type == "table":
                    citation = await self._find_table_content(doc_path, context)
                elif ref_type == "page":
                    citation = await self._find_page_content(doc_path, int(ref_value) if ref_value else 1)
                elif ref_type == "temperature":
                    citation = await self._find_temperature_table(doc_path, ref_value)
                elif ref_type == "safety":
                    citation = await self._find_safety_visual(doc_path, context)
                else:
                    citation = await self._find_general_visual(doc_path, context)
                
                if citation:
                    return citation
            
            return None
            
        except Exception as e:
            logger.error(f"Visual content search failed: {e}")
            return None
    
    async def _suggest_context_based_visuals(self, voice_text: str, 
                                           current_equipment: str = None) -> List[VisualCitation]:
        """
        Suggest visual content based on voice text context and current equipment
        """
        suggestions = []
        text_lower = voice_text.lower()
        
        try:
            # Find documents for current equipment
            documents = await self._find_relevant_documents(current_equipment)
            
            for doc_path in documents:
                if doc_path not in self.document_index:
                    await self._index_document_content(doc_path)
                
                # Check for equipment-specific visual patterns
                for equipment_part, keywords in self.equipment_visual_patterns.items():
                    if any(keyword in text_lower for keyword in keywords):
                        visual = await self._find_equipment_visual(doc_path, equipment_part, keywords)
                        if visual:
                            suggestions.append(visual)
            
            return suggestions[:3]  # Limit to top 3 suggestions
            
        except Exception as e:
            logger.error(f"Context-based visual suggestions failed: {e}")
            return []
    
    async def _find_relevant_documents(self, current_equipment: str = None) -> List[Path]:
        """
        Find documents relevant to current equipment or return all available documents
        """
        documents = []
        
        if not self.uploaded_docs_path.exists():
            return documents
        
        # Find PDF documents
        pdf_files = list(self.uploaded_docs_path.glob("*.pdf"))
        
        if current_equipment:
            # Filter by equipment type if specified
            equipment_keywords = current_equipment.lower().split()
            for pdf_file in pdf_files:
                filename_lower = pdf_file.name.lower()
                if any(keyword in filename_lower for keyword in equipment_keywords):
                    documents.append(pdf_file)
        
        # If no equipment-specific documents found, return all
        if not documents:
            documents = pdf_files
        
        return documents
    
    async def _index_document_content(self, doc_path: Path) -> None:
        """
        Index document content for fast lookup
        """
        try:
            doc_index = {
                "pages": {},
                "images": {},
                "tables": {},
                "text_blocks": {}
            }
            
            # Open PDF document
            doc = fitz.open(str(doc_path))
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text blocks
                text_blocks = page.get_text("dict")
                doc_index["text_blocks"][page_num] = text_blocks
                
                # Find images
                image_list = page.get_images()
                if image_list:
                    doc_index["images"][page_num] = image_list
                
                # Find tables (approximate detection)
                tables = self._detect_tables_on_page(page)
                if tables:
                    doc_index["tables"][page_num] = tables
                
                # Store page info
                doc_index["pages"][page_num] = {
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "text": page.get_text()
                }
            
            doc.close()
            self.document_index[str(doc_path)] = doc_index
            
        except Exception as e:
            logger.error(f"Document indexing failed for {doc_path}: {e}")
    
    async def _find_diagram_content(self, doc_path: Path, diagram_number: str = None, 
                                  context: str = "") -> Optional[VisualCitation]:
        """
        Find diagram content in document
        """
        try:
            doc = fitz.open(str(doc_path))
            doc_index = self.document_index.get(str(doc_path), {})
            
            # Search for diagrams with numbers if specified
            for page_num, images in doc_index.get("images", {}).items():
                page = doc[page_num]
                page_text = doc_index["pages"][page_num]["text"].lower()
                
                # Check if page contains relevant content
                if diagram_number:
                    if f"diagram {diagram_number}" in page_text or f"figure {diagram_number}" in page_text:
                        # Extract the first image on this page
                        if images:
                            image_data = await self._extract_image_from_page(page, images[0])
                            if image_data:
                                citation = VisualCitation(
                                    citation_type=CitationType.DIAGRAM,
                                    source_document=doc_path.name,
                                    page_number=page_num + 1,
                                    reference_text=f"diagram {diagram_number}",
                                    content_data=image_data,
                                    timing="during_speech"
                                )
                                doc.close()
                                return citation
                
                # Fallback: look for context keywords
                elif any(keyword in page_text for keyword in context.lower().split()):
                    if images:
                        image_data = await self._extract_image_from_page(page, images[0])
                        if image_data:
                            citation = VisualCitation(
                                citation_type=CitationType.DIAGRAM,
                                source_document=doc_path.name,
                                page_number=page_num + 1,
                                reference_text="relevant diagram",
                                content_data=image_data,
                                timing="during_speech"
                            )
                            doc.close()
                            return citation
            
            doc.close()
            return None
            
        except Exception as e:
            logger.error(f"Diagram search failed: {e}")
            return None
    
    async def _find_table_content(self, doc_path: Path, context: str) -> Optional[VisualCitation]:
        """
        Find table content in document
        """
        try:
            doc = fitz.open(str(doc_path))
            doc_index = self.document_index.get(str(doc_path), {})
            
            # Search for pages with tables and matching context
            for page_num, tables in doc_index.get("tables", {}).items():
                page_text = doc_index["pages"][page_num]["text"].lower()
                
                # Check if page contains table and relevant context
                if any(keyword in page_text for keyword in ["table", "specification", "temperature"]):
                    if any(keyword in page_text for keyword in context.lower().split()):
                        # Extract table area as image
                        page = doc[page_num]
                        table_data = await self._extract_table_as_image(page, tables[0] if tables else None)
                        
                        if table_data:
                            citation = VisualCitation(
                                citation_type=CitationType.TABLE,
                                source_document=doc_path.name,
                                page_number=page_num + 1,
                                reference_text="specification table",
                                content_data=table_data,
                                timing="during_speech"
                            )
                            doc.close()
                            return citation
            
            doc.close()
            return None
            
        except Exception as e:
            logger.error(f"Table search failed: {e}")
            return None
    
    async def _find_page_content(self, doc_path: Path, page_number: int) -> Optional[VisualCitation]:
        """
        Extract specific page content
        """
        try:
            doc = fitz.open(str(doc_path))
            
            if page_number <= len(doc):
                page = doc[page_number - 1]  # Convert to 0-based index
                
                # Render page as image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better quality
                img_data = pix.tobytes("png")
                
                citation = VisualCitation(
                    citation_type=CitationType.TEXT_SECTION,
                    source_document=doc_path.name,
                    page_number=page_number,
                    reference_text=f"page {page_number}",
                    content_data=img_data,
                    timing="during_speech"
                )
                
                doc.close()
                return citation
            
            doc.close()
            return None
            
        except Exception as e:
            logger.error(f"Page extraction failed: {e}")
            return None
    
    async def _find_temperature_table(self, doc_path: Path, temperature: str = None) -> Optional[VisualCitation]:
        """
        Find temperature specification tables
        """
        try:
            doc = fitz.open(str(doc_path))
            doc_index = self.document_index.get(str(doc_path), {})
            
            # Look for pages with temperature information
            for page_num, page_info in doc_index.get("pages", {}).items():
                page_text = page_info["text"].lower()
                
                if any(keyword in page_text for keyword in ["temperature", "°f", "°c", "degrees"]):
                    if temperature and temperature in page_text:
                        # Found specific temperature reference
                        page = doc[page_num]
                        page_img = await self._extract_page_section_with_highlight(page, temperature)
                        
                        if page_img:
                            citation = VisualCitation(
                                citation_type=CitationType.TABLE,
                                source_document=doc_path.name,
                                page_number=page_num + 1,
                                reference_text=f"temperature {temperature}",
                                content_data=page_img,
                                timing="during_speech",
                                highlight_area=f"{temperature}°F"
                            )
                            doc.close()
                            return citation
            
            doc.close()
            return None
            
        except Exception as e:
            logger.error(f"Temperature table search failed: {e}")
            return None
    
    async def _find_safety_visual(self, doc_path: Path, context: str) -> Optional[VisualCitation]:
        """
        Find safety-related visual content
        """
        try:
            doc = fitz.open(str(doc_path))
            doc_index = self.document_index.get(str(doc_path), {})
            
            # Look for safety content
            for page_num, page_info in doc_index.get("pages", {}).items():
                page_text = page_info["text"].lower()
                
                if any(keyword in page_text for keyword in ["warning", "caution", "safety", "danger"]):
                    page = doc[page_num]
                    
                    # Check if page has images (safety diagrams)
                    images = doc_index.get("images", {}).get(page_num, [])
                    if images:
                        image_data = await self._extract_image_from_page(page, images[0])
                        if image_data:
                            citation = VisualCitation(
                                citation_type=CitationType.SAFETY_WARNING,
                                source_document=doc_path.name,
                                page_number=page_num + 1,
                                reference_text="safety warning",
                                content_data=image_data,
                                timing="during_speech"
                            )
                            doc.close()
                            return citation
                    else:
                        # Extract text section as image
                        page_img = page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png")
                        citation = VisualCitation(
                            citation_type=CitationType.SAFETY_WARNING,
                            source_document=doc_path.name,
                            page_number=page_num + 1,
                            reference_text="safety information",
                            content_data=page_img,
                            timing="during_speech"
                        )
                        doc.close()
                        return citation
            
            doc.close()
            return None
            
        except Exception as e:
            logger.error(f"Safety visual search failed: {e}")
            return None
    
    async def _find_general_visual(self, doc_path: Path, context: str) -> Optional[VisualCitation]:
        """
        Find general visual content based on context
        """
        # Implementation for general visual search
        return None
    
    async def _find_equipment_visual(self, doc_path: Path, equipment_part: str, 
                                   keywords: List[str]) -> Optional[VisualCitation]:
        """
        Find equipment-specific visual content
        """
        try:
            doc = fitz.open(str(doc_path))
            doc_index = self.document_index.get(str(doc_path), {})
            
            # Search for pages with equipment keywords
            for page_num, page_info in doc_index.get("pages", {}).items():
                page_text = page_info["text"].lower()
                
                if any(keyword in page_text for keyword in keywords):
                    page = doc[page_num]
                    images = doc_index.get("images", {}).get(page_num, [])
                    
                    if images:
                        # Extract first relevant image
                        image_data = await self._extract_image_from_page(page, images[0])
                        if image_data:
                            citation = VisualCitation(
                                citation_type=CitationType.DIAGRAM,
                                source_document=doc_path.name,
                                page_number=page_num + 1,
                                reference_text=f"{equipment_part} diagram",
                                content_data=image_data,
                                timing="during_speech",
                                highlight_area=equipment_part
                            )
                            doc.close()
                            return citation
            
            doc.close()
            return None
            
        except Exception as e:
            logger.error(f"Equipment visual search failed: {e}")
            return None
    
    def _detect_tables_on_page(self, page) -> List[Dict]:
        """
        Simple table detection based on text layout
        """
        try:
            text_dict = page.get_text("dict")
            tables = []
            
            # Look for rectangular text arrangements that might be tables
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    # Simple heuristic: if block has multiple lines with similar spacing
                    lines = block["lines"]
                    if len(lines) > 2:
                        # Check for table-like structure
                        y_positions = [line["bbox"][1] for line in lines]
                        if len(set(y_positions)) == len(y_positions):  # Distinct Y positions
                            tables.append({
                                "bbox": block["bbox"],
                                "lines": len(lines)
                            })
            
            return tables
            
        except Exception as e:
            logger.error(f"Table detection failed: {e}")
            return []
    
    async def _extract_image_from_page(self, page, image_info) -> Optional[bytes]:
        """
        Extract image data from page
        """
        try:
            # Get image data
            xref = image_info[0]  # First element is xref
            pix = fitz.Pixmap(page.parent, xref)
            
            if pix.n < 5:  # Not CMYK
                img_data = pix.tobytes("png")
            else:  # CMYK, convert to RGB
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix1.tobytes("png")
                pix1 = None
            
            pix = None
            return img_data
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return None
    
    async def _extract_table_as_image(self, page, table_info) -> Optional[bytes]:
        """
        Extract table area as image
        """
        try:
            if table_info:
                # Crop page to table area
                bbox = table_info["bbox"]
                rect = fitz.Rect(bbox)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect)
            else:
                # Full page if no specific table area
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            img_data = pix.tobytes("png")
            return img_data
            
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return None
    
    async def _extract_page_section_with_highlight(self, page, highlight_text: str) -> Optional[bytes]:
        """
        Extract page section and highlight specific text
        """
        try:
            # For now, just return the full page
            # TODO: Implement text highlighting
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            return img_data
            
        except Exception as e:
            logger.error(f"Page section extraction failed: {e}")
            return None
    
    async def get_citation_content(self, citation_id: str) -> Optional[bytes]:
        """
        Retrieve citation content by ID
        """
        # Search through cached citations
        for doc_citations in self.citation_cache.values():
            for citation in doc_citations:
                if citation.citation_id == citation_id:
                    return citation.content_data
        
        return None
    
    def _cache_citation(self, citation: VisualCitation) -> None:
        """
        Cache citation for content retrieval
        """
        doc_key = citation.source_document
        if doc_key not in self.citation_cache:
            self.citation_cache[doc_key] = []
        self.citation_cache[doc_key].append(citation)
        logger.info(f"Cached citation {citation.citation_id} for document {doc_key}")
    
    async def synchronize_voice_with_visuals(self, voice_response: Dict[str, Any], 
                                           timing_markers: List[str] = None) -> Dict[str, Any]:
        """
        Create synchronized voice + visual response with timing coordination
        """
        try:
            voice_text = voice_response.get("response", "")
            current_equipment = voice_response.get("equipment_context")
            
            # Extract citations
            citation_result = await self.extract_citations_from_response(voice_text, current_equipment)
            
            # Add timing coordination
            synchronized_response = {
                **voice_response,
                "multimodal_citations": citation_result,
                "display_coordination": {
                    "voice_timing": "auto",
                    "visual_display": "synchronized",
                    "interaction_enabled": True
                },
                "voice_visual_sync": True
            }
            
            return synchronized_response
            
        except Exception as e:
            logger.error(f"Voice-visual synchronization failed: {e}")
            return voice_response

# Global instance
multimodal_citation_service = MultiModalCitationService()