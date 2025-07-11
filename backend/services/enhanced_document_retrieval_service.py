#!/usr/bin/env python3
"""
Enhanced Document Retrieval Service
===================================

Connects Neo4j entities to their source document chunks for complete context retrieval.
Provides the missing link between entity metadata and actual document content.

Features:
- Retrieves source document chunks referenced by Neo4j entities
- Combines entity metadata with actual document content
- Supports multi-modal citations and visual references
- Provides rich context for LLM response generation

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import asyncio

# Import LightRAG for document chunk retrieval
try:
    from lightrag import LightRAG
    from lightrag.utils import EmbeddingFunc
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    logging.warning("LightRAG not available for document retrieval")

logger = logging.getLogger(__name__)

class EnhancedDocumentRetrievalService:
    """
    Service that connects Neo4j entity metadata to actual source document content
    """
    
    def __init__(self):
        self.lightrag_working_dir = os.getenv('LIGHTRAG_WORKING_DIR', './rag_storage')
        self.lightrag_instance = None
        self.document_cache = {}
        
        # Initialize LightRAG if available
        if LIGHTRAG_AVAILABLE:
            self._initialize_lightrag()
    
    def _initialize_lightrag(self):
        """Initialize LightRAG for document content retrieval"""
        try:
            # Custom embedding function with correct parameters
            def custom_embedding(texts: List[str]) -> List[List[float]]:
                """Custom embedding function using sentence-transformers"""
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    embeddings = model.encode(texts)
                    return [emb.tolist() for emb in embeddings]
                except Exception as e:
                    logger.error(f"Embedding generation failed: {e}")
                    # Return dummy embeddings as fallback
                    return [[0.0] * 384 for _ in texts]
            
            # Create EmbeddingFunc with required parameters
            embedding_func = EmbeddingFunc(
                embedding_dim=384,
                max_token_size=512,
                func=custom_embedding
            )
            
            # Initialize LightRAG
            self.lightrag_instance = LightRAG(
                working_dir=self.lightrag_working_dir,
                embedding_func=embedding_func
            )
            
            logger.info("✅ LightRAG initialized for document retrieval")
            
        except Exception as e:
            logger.error(f"LightRAG initialization failed: {e}")
            self.lightrag_instance = None
    
    async def retrieve_source_content_for_entities(
        self, 
        entities: List[Dict[str, Any]], 
        query: str,
        max_chunks: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve actual source document content for given entities
        
        Args:
            entities: List of Neo4j entities with metadata
            query: Original user query for context
            max_chunks: Maximum number of document chunks to retrieve
            
        Returns:
            Dictionary with source content, entities, and visual citations
        """
        
        logger.info(f"🔍 Retrieving source content for {len(entities)} entities")
        
        # Extract search terms from entities and query
        search_terms = self._extract_search_terms(entities, query)
        
        # Retrieve relevant document chunks
        source_chunks = await self._retrieve_document_chunks(search_terms, max_chunks)
        
        # Combine entity metadata with source content
        enhanced_context = self._combine_entities_with_source_content(entities, source_chunks, query)
        
        # Extract visual citations
        visual_citations = self._extract_visual_citations_from_entities(entities)
        
        return {
            "source_content": source_chunks,
            "entity_metadata": entities,
            "visual_citations": visual_citations,
            "enhanced_context": enhanced_context,
            "search_terms": search_terms,
            "content_available": len(source_chunks) > 0
        }
    
    def _extract_search_terms(self, entities: List[Dict[str, Any]], query: str) -> List[str]:
        """Extract relevant search terms from entities and query with temperature focus"""
        
        search_terms = []
        
        # Priority temperature and food safety terms
        if "temperature" in query.lower():
            search_terms.extend(["temperature", "temp", "degrees", "°F", "°C", "heating", "cooling"])
        
        if any(word in query.lower() for word in ["food", "safety", "safe"]):
            search_terms.extend(["food safety", "food", "safety", "safe", "handling"])
        
        # Add query terms
        query_words = query.lower().split()
        search_terms.extend([word for word in query_words if len(word) > 3])
        
        # Add entity names and descriptions
        for entity in entities:
            entity_name = entity.get('item_name', '') or entity.get('name', '')
            entity_desc = entity.get('item_description', '') or entity.get('description', '')
            
            if entity_name:
                search_terms.append(entity_name.lower())
            
            if entity_desc:
                # Extract key terms from description
                desc_words = entity_desc.lower().split()
                search_terms.extend([word for word in desc_words if len(word) > 4])
        
        # Remove duplicates and common words
        search_terms = list(set(search_terms))
        common_words = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'have', 'been', 'will', 'they', 'their', 'what', 'are'}
        search_terms = [term for term in search_terms if term not in common_words]
        
        logger.info(f"📋 Extracted search terms: {search_terms[:15]}")  # Show more terms
        
        return search_terms[:15]  # Allow more terms for better matching
    
    async def _retrieve_document_chunks(self, search_terms: List[str], max_chunks: int) -> List[Dict[str, Any]]:
        """Retrieve relevant document chunks using LightRAG or fallback methods"""
        
        if not self.lightrag_instance:
            logger.warning("⚠️ LightRAG not available, using fallback retrieval")
            return await self._fallback_document_retrieval(search_terms, max_chunks)
        
        try:
            # Query LightRAG for relevant content
            search_query = " ".join(search_terms[:5])  # Use top 5 terms
            
            # Use LightRAG query to get relevant content
            logger.info(f"🔍 Querying LightRAG with: {search_query}")
            
            # Query LightRAG (this returns the actual document content)
            response = await self.lightrag_instance.aquery(search_query)
            
            if response:
                # Extract chunks from LightRAG response
                chunks = self._parse_lightrag_response(response, search_terms)
                logger.info(f"✅ Retrieved {len(chunks)} document chunks from LightRAG")
                return chunks[:max_chunks]
            else:
                logger.warning("⚠️ No response from LightRAG, using fallback")
                return await self._fallback_document_retrieval(search_terms, max_chunks)
                
        except Exception as e:
            logger.error(f"❌ LightRAG retrieval failed: {e}")
            return await self._fallback_document_retrieval(search_terms, max_chunks)
    
    def _parse_lightrag_response(self, response: str, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Parse LightRAG response into structured chunks"""
        
        chunks = []
        
        # Split response into logical sections
        sections = response.split('\n\n')
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 50:  # Only include substantial content
                # Calculate relevance score based on search terms
                relevance_score = sum(1 for term in search_terms if term.lower() in section.lower())
                
                chunk = {
                    "content": section.strip(),
                    "chunk_id": f"lightrag_chunk_{i}",
                    "source": "lightrag_query",
                    "relevance_score": relevance_score,
                    "length": len(section),
                    "contains_terms": [term for term in search_terms if term.lower() in section.lower()]
                }
                chunks.append(chunk)
        
        # Sort by relevance score
        chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return chunks
    
    async def _fallback_document_retrieval(self, search_terms: List[str], max_chunks: int) -> List[Dict[str, Any]]:
        """Fallback document retrieval when LightRAG is not available"""
        
        logger.info("🔄 Using fallback document retrieval")
        
        # Look for uploaded documents
        uploaded_docs_dir = Path("uploaded_docs")
        if not uploaded_docs_dir.exists():
            return []
        
        chunks = []
        
        # Process ALL uploaded PDFs (not just New-Crew-Handbook)
        for pdf_file in uploaded_docs_dir.glob("*.pdf"):
            try:
                # Extract text from PDF (basic extraction)
                text_content = await self._extract_text_from_pdf(pdf_file)
                
                if text_content:
                    # Create chunks from PDF content
                    pdf_chunks = self._create_chunks_from_text(text_content, search_terms, str(pdf_file))
                    chunks.extend(pdf_chunks)
                    logger.info(f"✅ Processed {pdf_file.name}: {len(pdf_chunks)} relevant chunks")
                    
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
        
        # Sort by relevance and return top chunks
        chunks.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return chunks[:max_chunks]
    
    async def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
                
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""
    
    def _create_chunks_from_text(self, text: str, search_terms: List[str], source: str) -> List[Dict[str, Any]]:
        """Create searchable chunks from text content"""
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 100]
        
        chunks = []
        for i, paragraph in enumerate(paragraphs):
            # Calculate relevance score
            relevance_score = sum(1 for term in search_terms if term.lower() in paragraph.lower())
            
            if relevance_score > 0:  # Only include relevant chunks
                chunk = {
                    "content": paragraph,
                    "chunk_id": f"pdf_chunk_{i}",
                    "source": source,
                    "relevance_score": relevance_score,
                    "length": len(paragraph),
                    "contains_terms": [term for term in search_terms if term.lower() in paragraph.lower()]
                }
                chunks.append(chunk)
        
        return chunks
    
    def _combine_entities_with_source_content(
        self, 
        entities: List[Dict[str, Any]], 
        source_chunks: List[Dict[str, Any]], 
        query: str
    ) -> Dict[str, Any]:
        """Combine entity metadata with source document content for rich context"""
        
        # Create enhanced context for LLM
        context_parts = [
            f"User Query: {query}",
            "",
            "RELEVANT INFORMATION FROM DOCUMENTS:",
        ]
        
        # Add source content
        for i, chunk in enumerate(source_chunks[:3], 1):  # Top 3 chunks
            context_parts.append(f"{i}. {chunk['content']}")
            context_parts.append("")
        
        # Add entity metadata context
        if entities:
            context_parts.append("RELATED ENTITIES:")
            for entity in entities[:5]:  # Top 5 entities
                entity_name = entity.get('item_name', '') or entity.get('name', '')
                entity_type = entity.get('item_type', '') or entity.get('type', '')
                page_refs = entity.get('page_refs', [])
                
                if entity_name:
                    entity_info = f"• {entity_name} ({entity_type})"
                    if page_refs:
                        entity_info += f" - See pages {page_refs}"
                    context_parts.append(entity_info)
        
        enhanced_context = "\n".join(context_parts)
        
        return {
            "full_context": enhanced_context,
            "source_chunks_count": len(source_chunks),
            "entities_count": len(entities),
            "context_length": len(enhanced_context)
        }
    
    def _extract_visual_citations_from_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract visual citations from entity metadata"""
        
        visual_citations = []
        
        for entity in entities:
            visual_refs = entity.get('visual_refs', [])
            page_refs = entity.get('page_refs', [])
            entity_name = entity.get('item_name', '') or entity.get('name', '')
            
            if visual_refs or page_refs:
                citation = {
                    "entity_name": entity_name,
                    "visual_refs": visual_refs,
                    "page_refs": page_refs,
                    "citation_count": len(visual_refs),
                    "has_visual_content": len(visual_refs) > 0
                }
                visual_citations.append(citation)
        
        return visual_citations

# Global instance
enhanced_document_retrieval_service = EnhancedDocumentRetrievalService()