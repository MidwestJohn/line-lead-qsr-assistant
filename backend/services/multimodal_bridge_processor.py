#!/usr/bin/env python3
"""
Multi-Modal Enterprise Bridge Processor
======================================

Integrates RAG-Anything multi-modal processing with the existing Enterprise Bridge system.
Enables complete PDF processing with text, images, tables, and diagrams preservation.

Features:
- RAG-Anything + MinerU integration for complete multi-modal extraction
- Multi-Modal Citation Service integration during document upload
- Enhanced entity extraction with visual references
- Neo4j schema enhancement for visual content
- Backward compatibility with existing Enterprise Bridge

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import asyncio

# Import existing services
from services.document_processor import document_processor, ProcessedContent
from services.multimodal_citation_service import multimodal_citation_service, VisualCitation
from services.qsr_entity_extractor import extract_qsr_entities_from_text

logger = logging.getLogger(__name__)

@dataclass
class MultiModalProcessingResult:
    """Complete multi-modal processing result"""
    text_content: str
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    visual_citations: List[Dict[str, Any]]
    processed_content: ProcessedContent
    processing_method: str
    statistics: Dict[str, Any]

class MultiModalBridgeProcessor:
    """
    Enhanced processor that integrates multi-modal capabilities with Enterprise Bridge
    """
    
    def __init__(self):
        self.use_rag_anything = os.getenv('USE_RAG_ANYTHING', 'false').lower() == 'true'
        self.use_multimodal_citations = os.getenv('USE_MULTIMODAL_CITATIONS', 'false').lower() == 'true'
        self.stats = {
            "documents_processed": 0,
            "visual_citations_extracted": 0,
            "enhanced_entities": 0
        }
        
        logger.info(f"🎨 Multi-Modal Bridge Processor initialized:")
        logger.info(f"   RAG-Anything: {self.use_rag_anything}")
        logger.info(f"   Multi-Modal Citations: {self.use_multimodal_citations}")
    
    async def process_document_with_multimodal(
        self, 
        file_path: str, 
        filename: str,
        progress_callback: Optional[callable] = None
    ) -> MultiModalProcessingResult:
        """
        Process document with complete multi-modal extraction and Enterprise Bridge integration
        """
        
        logger.info(f"🚀 Starting multi-modal processing for {filename}")
        start_time = time.time()
        
        try:
            # Stage 1: Enhanced document processing
            if progress_callback:
                await progress_callback({"stage": "multimodal_extraction", "progress": 10, "operation": "Extracting text, images, and tables"})
            
            processed_content = await self._extract_multimodal_content(file_path, filename)
            
            # Stage 2: Generate multi-modal citations
            if progress_callback:
                await progress_callback({"stage": "citation_generation", "progress": 30, "operation": "Generating visual citations"})
            
            visual_citations = await self._generate_visual_citations(file_path, processed_content)
            
            # Stage 3: Enhanced entity extraction with visual context
            if progress_callback:
                await progress_callback({"stage": "enhanced_entity_extraction", "progress": 50, "operation": "Extracting entities with visual context"})
            
            entities, relationships = await self._extract_entities_with_visual_context(
                processed_content, visual_citations, filename
            )
            
            # Stage 4: Enhance entities with multi-modal references
            if progress_callback:
                await progress_callback({"stage": "multimodal_enhancement", "progress": 75, "operation": "Enhancing entities with visual references"})
            
            enhanced_entities = await self._enhance_entities_with_multimodal_refs(entities, visual_citations)
            enhanced_relationships = await self._enhance_relationships_with_multimodal_refs(relationships, visual_citations)
            
            processing_time = time.time() - start_time
            self.stats["documents_processed"] += 1
            self.stats["visual_citations_extracted"] += len(visual_citations)
            self.stats["enhanced_entities"] += len(enhanced_entities)
            
            # Create comprehensive result
            result = MultiModalProcessingResult(
                text_content=processed_content.text_chunks[0] if processed_content.text_chunks else "",
                entities=enhanced_entities,
                relationships=enhanced_relationships,
                visual_citations=visual_citations,
                processed_content=processed_content,
                processing_method="multimodal_enterprise_bridge",
                statistics={
                    "processing_time_seconds": round(processing_time, 2),
                    "text_chunks": len(processed_content.text_chunks),
                    "images_found": len(processed_content.images),
                    "tables_found": len(processed_content.tables),
                    "visual_citations": len(visual_citations),
                    "entities_extracted": len(enhanced_entities),
                    "relationships_extracted": len(enhanced_relationships),
                    "visual_enhancements": sum(1 for e in enhanced_entities if e.get('visual_refs')),
                    "multimodal_enabled": True
                }
            )
            
            logger.info(f"✅ Multi-modal processing completed for {filename}")
            logger.info(f"📊 Results: {len(enhanced_entities)} entities, {len(enhanced_relationships)} relationships, {len(visual_citations)} visual citations")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Multi-modal processing failed for {filename}: {e}")
            
            # Fallback to basic processing
            logger.info("🔄 Falling back to basic text processing")
            return await self._fallback_to_basic_processing(file_path, filename)
    
    async def _extract_multimodal_content(self, file_path: str, filename: str) -> ProcessedContent:
        """
        Extract content using RAG-Anything if available, fallback to basic processing
        """
        
        if self.use_rag_anything:
            try:
                logger.info("🎨 Using RAG-Anything for multi-modal extraction")
                return await document_processor.process_document(file_path)
            except Exception as e:
                logger.warning(f"RAG-Anything processing failed, falling back to basic: {e}")
        
        # Fallback to basic processing
        logger.info("🔄 Falling back to basic processing due to RAG-Anything failure")
        return await document_processor.process_pdf_basic(file_path)
    
    async def _generate_visual_citations(self, file_path: str, processed_content: ProcessedContent) -> List[Dict[str, Any]]:
        """
        Generate visual citations using Multi-Modal Citation Service
        """
        
        if not self.use_multimodal_citations:
            return []
        
        try:
            logger.info("🔍 Generating visual citations")
            
            # Index document content for citation extraction
            await multimodal_citation_service._index_document_content(Path(file_path))
            
            # Create comprehensive text for citation extraction
            full_text = " ".join(processed_content.text_chunks)
            
            # Extract citations from the full document text
            citation_result = await multimodal_citation_service.extract_citations_from_response(full_text)
            
            return citation_result.get("visual_citations", [])
            
        except Exception as e:
            logger.error(f"Visual citation generation failed: {e}")
            return []
    
    async def _extract_entities_with_visual_context(
        self, 
        processed_content: ProcessedContent, 
        visual_citations: List[Dict[str, Any]], 
        filename: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract entities and relationships with enhanced visual context
        """
        
        # Combine all text content
        full_text = " ".join(processed_content.text_chunks)
        
        # Add visual context information to text
        enhanced_text = self._create_enhanced_text_with_visual_context(full_text, visual_citations, processed_content)
        
        # Extract entities using existing QSR entity extractor
        entities, relationships = extract_qsr_entities_from_text(enhanced_text)
        
        logger.info(f"📊 Extracted {len(entities)} entities and {len(relationships)} relationships with visual context")
        
        return entities, relationships
    
    def _create_enhanced_text_with_visual_context(
        self, 
        text: str, 
        visual_citations: List[Dict[str, Any]], 
        processed_content: ProcessedContent
    ) -> str:
        """
        Create enhanced text that includes visual context for better entity extraction
        """
        
        enhanced_sections = [text]
        
        # Add image context
        if processed_content.images:
            image_context = f"\n\nVISUAL CONTENT DETECTED:\n"
            image_context += f"- {len(processed_content.images)} images found in document\n"
            for i, img in enumerate(processed_content.images[:5]):  # Limit to first 5
                image_context += f"- Image {i+1}: {img.get('description', 'Equipment diagram or photo')}\n"
            enhanced_sections.append(image_context)
        
        # Add table context
        if processed_content.tables:
            table_context = f"\n\nTABLE CONTENT DETECTED:\n"
            table_context += f"- {len(processed_content.tables)} tables found in document\n"
            for i, table in enumerate(processed_content.tables[:3]):  # Limit to first 3
                table_context += f"- Table {i+1}: {table.get('description', 'Specifications or data table')}\n"
            enhanced_sections.append(table_context)
        
        # Add visual citation context
        if visual_citations:
            citation_context = f"\n\nVISUAL CITATIONS DETECTED:\n"
            for citation in visual_citations[:5]:  # Limit to first 5
                citation_type = citation.get('type', 'unknown')
                reference = citation.get('reference', 'visual element')
                page = citation.get('page', 'unknown')
                citation_context += f"- {citation_type}: {reference} (page {page})\n"
            enhanced_sections.append(citation_context)
        
        return "\n".join(enhanced_sections)
    
    async def _enhance_entities_with_multimodal_refs(
        self, 
        entities: List[Dict[str, Any]], 
        visual_citations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance entities with multi-modal references
        """
        
        enhanced_entities = []
        
        for entity in entities:
            enhanced_entity = entity.copy()
            
            # Find relevant visual citations for this entity
            entity_name = entity.get('name', '').lower()
            entity_description = entity.get('description', '').lower()
            
            relevant_citations = []
            image_refs = []
            table_refs = []
            diagram_refs = []
            page_refs = []
            
            for citation in visual_citations:
                citation_ref = citation.get('reference', '').lower()
                citation_type = citation.get('type', '')
                
                # Check if citation is relevant to this entity
                if (entity_name in citation_ref or 
                    any(word in citation_ref for word in entity_name.split()) or
                    any(word in citation_ref for word in entity_description.split())):
                    
                    relevant_citations.append(citation.get('citation_id'))
                    
                    # Categorize by type
                    if citation_type == 'image':
                        image_refs.append(citation.get('citation_id'))
                    elif citation_type == 'table':
                        table_refs.append(citation.get('citation_id'))
                    elif citation_type == 'diagram':
                        diagram_refs.append(citation.get('citation_id'))
                    
                    page_refs.append(citation.get('page'))
            
            # Add multi-modal properties to entity
            enhanced_entity.update({
                'visual_refs': relevant_citations,
                'image_refs': image_refs,
                'table_refs': table_refs,
                'diagram_refs': diagram_refs,
                'page_refs': list(set(page_refs)),  # Remove duplicates
                'citation_ids': relevant_citations,
                'multimodal_enhanced': len(relevant_citations) > 0
            })
            
            enhanced_entities.append(enhanced_entity)
        
        enhanced_count = sum(1 for e in enhanced_entities if e.get('multimodal_enhanced'))
        logger.info(f"🎨 Enhanced {enhanced_count} entities with multi-modal references")
        
        return enhanced_entities
    
    async def _enhance_relationships_with_multimodal_refs(
        self, 
        relationships: List[Dict[str, Any]], 
        visual_citations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance relationships with multi-modal references
        """
        
        enhanced_relationships = []
        
        for relationship in relationships:
            enhanced_relationship = relationship.copy()
            
            # Find visual citations that might illustrate this relationship
            source = relationship.get('source', '').lower()
            target = relationship.get('target', '').lower()
            relation_type = relationship.get('relation', '').lower()
            
            relevant_citations = []
            
            for citation in visual_citations:
                citation_ref = citation.get('reference', '').lower()
                
                # Check if citation illustrates this relationship
                if ((source in citation_ref or target in citation_ref) and
                    any(word in citation_ref for word in ['diagram', 'connection', 'procedure', 'process'])):
                    relevant_citations.append(citation.get('citation_id'))
            
            # Add visual context to relationship
            if relevant_citations:
                enhanced_relationship.update({
                    'visual_illustrations': relevant_citations,
                    'has_visual_context': True
                })
            else:
                enhanced_relationship['has_visual_context'] = False
            
            enhanced_relationships.append(enhanced_relationship)
        
        visual_relationships = sum(1 for r in enhanced_relationships if r.get('has_visual_context'))
        logger.info(f"🎨 Enhanced {visual_relationships} relationships with visual context")
        
        return enhanced_relationships
    
    async def _fallback_to_basic_processing(self, file_path: str, filename: str) -> MultiModalProcessingResult:
        """
        Fallback to basic text processing if multi-modal processing fails
        """
        
        logger.info("🔄 Using basic processing fallback")
        
        try:
            # Basic text extraction
            processed_content = await document_processor.process_pdf_basic(file_path)
            
            # Basic entity extraction
            full_text = " ".join(processed_content.text_chunks)
            entities, relationships = extract_qsr_entities_from_text(full_text)
            
            return MultiModalProcessingResult(
                text_content=full_text,
                entities=entities,
                relationships=relationships,
                visual_citations=[],
                processed_content=processed_content,
                processing_method="basic_fallback",
                statistics={
                    "processing_time_seconds": 0,
                    "text_chunks": len(processed_content.text_chunks),
                    "images_found": 0,
                    "tables_found": 0,
                    "visual_citations": 0,
                    "entities_extracted": len(entities),
                    "relationships_extracted": len(relationships),
                    "visual_enhancements": 0,
                    "multimodal_enabled": False
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Even basic processing failed: {e}")
            raise e
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            "multimodal_enabled": self.use_rag_anything and self.use_multimodal_citations,
            "rag_anything_enabled": self.use_rag_anything,
            "citations_enabled": self.use_multimodal_citations
        }

# Global instance
multimodal_bridge_processor = MultiModalBridgeProcessor()