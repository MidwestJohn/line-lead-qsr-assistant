#!/usr/bin/env python3
"""
Ragie Integration Service for Line Lead QSR Assistant
=====================================================

Replaces the complex Graph RAG system with Ragie's managed RAG service.
Provides document upload, search, and retrieval capabilities while maintaining
compatibility with the existing chat interface.

Key Features:
- Document upload to Ragie with QSR-specific metadata
- Semantic search with filtering and reranking
- Multi-modal content support (PDF, images, videos)
- Response parsing to maintain API compatibility
- QSR-optimized retrieval strategies

Author: Generated with Memex (https://memex.tech)
"""

import logging
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import asyncio

from ragie import Ragie
import aiofiles

logger = logging.getLogger(__name__)

class RagieService:
    """Main service for Ragie integration with QSR-specific optimizations"""
    
    def __init__(self):
        """Initialize Ragie client and QSR configuration"""
        self.api_key = os.getenv("RAGIE_API_KEY")
        if not self.api_key:
            raise ValueError("RAGIE_API_KEY environment variable is required")
        
        self.client = Ragie(auth=self.api_key)
        self.partition = os.getenv("RAGIE_PARTITION", "qsr_manuals")
        
        # QSR-specific configuration
        self.qsr_equipment_types = {
            "fryer", "grill", "oven", "ice_machine", "pos_system", 
            "drive_thru", "prep_station", "dishwasher", "mixer"
        }
        
        self.qsr_procedure_types = {
            "cleaning", "maintenance", "troubleshooting", "setup", 
            "safety", "daily_ops", "opening", "closing"
        }
        
        logger.info(f"RagieService initialized with partition: {self.partition}")
    
    async def upload_document(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload a document to Ragie with QSR-specific metadata
        
        Args:
            file_path: Path to the file to upload
            metadata: Document metadata (will be enhanced with QSR tags)
            
        Returns:
            Upload result with document ID and processing status
        """
        try:
            # Extract QSR-specific metadata
            enhanced_metadata = self._enhance_qsr_metadata(file_path, metadata)
            
            # Upload to Ragie
            with open(file_path, 'rb') as f:
                response = self.client.documents.create(request={
                    "file": {
                        "file_name": Path(file_path).name,
                        "content": f,
                    },
                    "mode": "hi_res",  # Extract images and tables for QSR diagrams
                    "metadata": enhanced_metadata,
                    "partition": self.partition,
                    "name": enhanced_metadata.get("display_name", Path(file_path).name)
                })
            
            logger.info(f"Successfully uploaded {Path(file_path).name} to Ragie: {response.id}")
            
            return {
                "success": True,
                "document_id": response.id,
                "filename": Path(file_path).name,
                "chunk_count": response.chunk_count,
                "page_count": response.page_count,
                "ragie_metadata": enhanced_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to upload {file_path} to Ragie: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": Path(file_path).name
            }
    
    async def search_documents(self, query: str, top_k: int = 8, equipment_type: str = None, 
                              procedure_type: str = None, safety_level: str = None) -> List[Dict[str, Any]]:
        """
        Search documents using Ragie with QSR-specific filtering
        
        Args:
            query: Search query
            top_k: Maximum number of results
            equipment_type: Filter by equipment type (fryer, grill, etc.)
            procedure_type: Filter by procedure type (cleaning, maintenance, etc.)
            safety_level: Filter by safety level (critical, high, medium, low)
            
        Returns:
            List of relevant chunks formatted for the chat system
        """
        try:
            # Build QSR-specific filter
            filter_dict = self._build_qsr_filter(equipment_type, procedure_type, safety_level)
            
            # Search with Ragie
            response = self.client.retrievals.retrieve(request={
                "query": query,
                "top_k": top_k,
                "rerank": True,  # Enable semantic reranking for better quality
                "filter": filter_dict if filter_dict else None,
                "partition": self.partition,
                "max_chunks_per_document": 3,  # Diversify sources
                "recency_bias": True  # Favor newer manuals
            })
            
            # Parse results for compatibility with existing chat system
            parsed_chunks = []
            for chunk in response.scored_chunks:
                parsed_chunk = {
                    "text": chunk.text,
                    "similarity": chunk.score,
                    "source": chunk.document_name,
                    "document_id": chunk.document_id,
                    "metadata": chunk.metadata,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.index,
                    "ragie_source": True  # Flag for tracking
                }
                
                # Add QSR-specific enhancements
                parsed_chunk.update(self._enhance_chunk_for_qsr(chunk))
                parsed_chunks.append(parsed_chunk)
            
            logger.info(f"Retrieved {len(parsed_chunks)} chunks for query: {query[:50]}...")
            return parsed_chunks
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    async def search_with_context(self, query: str, conversation_context: List[str] = None) -> Dict[str, Any]:
        """
        Enhanced search with conversation context for better QSR assistance
        
        Args:
            query: Current query
            conversation_context: Previous messages for context
            
        Returns:
            Enhanced search results with context-aware ranking
        """
        try:
            # Detect QSR intent from query
            equipment_type, procedure_type, safety_level = self._detect_qsr_intent(query)
            
            # Perform search with detected filters
            chunks = await self.search_documents(
                query=query,
                top_k=8,
                equipment_type=equipment_type,
                procedure_type=procedure_type,
                safety_level=safety_level
            )
            
            # Group by document for better context
            documents = self._group_chunks_by_document(chunks)
            
            return {
                "chunks": chunks,
                "documents": documents,
                "detected_equipment": equipment_type,
                "detected_procedure": procedure_type,
                "safety_level": safety_level,
                "total_sources": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Context search failed: {e}")
            return {"chunks": [], "documents": [], "error": str(e)}
    
    def _enhance_qsr_metadata(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata with QSR-specific tags and classifications"""
        enhanced = metadata.copy()
        
        filename = Path(file_path).name.lower()
        
        # Auto-detect equipment type from filename
        for equipment in self.qsr_equipment_types:
            if equipment.replace("_", "") in filename.replace("_", "").replace("-", ""):
                enhanced["equipment_type"] = equipment
                break
        
        # Auto-detect document type
        if "manual" in filename:
            enhanced["document_type"] = "manual"
        elif "cleaning" in filename or "clean" in filename:
            enhanced["document_type"] = "cleaning_guide"
            enhanced["procedure_type"] = "cleaning"
        elif "safety" in filename:
            enhanced["document_type"] = "safety_protocol"
            enhanced["safety_level"] = "critical"
        elif "maintenance" in filename:
            enhanced["procedure_type"] = "maintenance"
        elif "manager" in filename:
            enhanced["document_type"] = "management_guide"
            enhanced["target_role"] = "manager"
        
        # Add QSR-specific tags
        enhanced.update({
            "industry": "qsr",
            "language": "en",
            "upload_timestamp": datetime.now().isoformat(),
            "system_source": "line_lead_assistant"
        })
        
        # Set display name if not provided
        if "display_name" not in enhanced:
            enhanced["display_name"] = metadata.get("original_filename", Path(file_path).name)
        
        return enhanced
    
    def _build_qsr_filter(self, equipment_type: str = None, procedure_type: str = None, 
                         safety_level: str = None) -> Optional[Dict[str, Any]]:
        """Build Ragie filter for QSR-specific search"""
        filter_conditions = []
        
        if equipment_type:
            filter_conditions.append({"equipment_type": {"$eq": equipment_type}})
        
        if procedure_type:
            filter_conditions.append({"procedure_type": {"$eq": procedure_type}})
        
        if safety_level:
            filter_conditions.append({"safety_level": {"$eq": safety_level}})
        
        # Always filter for QSR industry
        filter_conditions.append({"industry": {"$eq": "qsr"}})
        
        if len(filter_conditions) == 1:
            return filter_conditions[0]
        elif len(filter_conditions) > 1:
            return {"$and": filter_conditions}
        
        return None
    
    def _detect_qsr_intent(self, query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Detect QSR-specific intent from user query"""
        query_lower = query.lower()
        
        # Detect equipment type
        equipment_type = None
        for equipment in self.qsr_equipment_types:
            if equipment.replace("_", " ") in query_lower:
                equipment_type = equipment
                break
        
        # Detect procedure type
        procedure_type = None
        for procedure in self.qsr_procedure_types:
            if procedure in query_lower:
                procedure_type = procedure
                break
        
        # Detect safety level
        safety_level = None
        if any(word in query_lower for word in ["emergency", "urgent", "critical", "danger"]):
            safety_level = "critical"
        elif any(word in query_lower for word in ["safety", "caution", "warning"]):
            safety_level = "high"
        
        return equipment_type, procedure_type, safety_level
    
    def _enhance_chunk_for_qsr(self, chunk) -> Dict[str, Any]:
        """Add QSR-specific enhancements to chunk data"""
        enhancements = {}
        
        # Extract equipment mentions from text
        equipment_mentioned = []
        for equipment in self.qsr_equipment_types:
            if equipment.replace("_", " ") in chunk.text.lower():
                equipment_mentioned.append(equipment)
        
        if equipment_mentioned:
            enhancements["equipment_mentioned"] = equipment_mentioned
        
        # Detect if chunk contains steps
        if any(pattern in chunk.text.lower() for pattern in ["step", "1.", "first", "then", "next"]):
            enhancements["contains_steps"] = True
        
        # Detect safety warnings
        if any(word in chunk.text.lower() for word in ["warning", "caution", "danger", "avoid"]):
            enhancements["safety_warning"] = True
        
        return enhancements
    
    def _group_chunks_by_document(self, chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Group chunks by source document for better context"""
        documents = {}
        
        for chunk in chunks:
            doc_id = chunk["document_id"]
            if doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "document_name": chunk["source"],
                    "chunks": [],
                    "metadata": chunk.get("metadata", {}),
                    "max_score": chunk["similarity"]
                }
            
            documents[doc_id]["chunks"].append(chunk)
            documents[doc_id]["max_score"] = max(
                documents[doc_id]["max_score"], 
                chunk["similarity"]
            )
        
        return documents

# Global instance for use throughout the application
ragie_service = RagieService()