#!/usr/bin/env python3
"""
Clean Ragie Service Implementation
=================================

Simple, focused Ragie integration without Neo4j dependencies.
Replaces the complex graph RAG system with Ragie's managed service.

Author: Generated with Memex (https://memex.tech)
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
from pathlib import Path

# Ragie SDK imports
try:
    from ragie import Ragie
    from ragie.types import DocumentMetadata
    RAGIE_AVAILABLE = True
except ImportError:
    RAGIE_AVAILABLE = False
    logging.warning("Ragie SDK not available. Install with: pip install ragie")

logger = logging.getLogger(__name__)

@dataclass
class RagieSearchResult:
    """Result from Ragie search"""
    text: str
    score: float
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any]

@dataclass
class RagieUploadResult:
    """Result from Ragie upload"""
    success: bool
    document_id: Optional[str] = None
    filename: Optional[str] = None
    chunk_count: Optional[int] = None
    error: Optional[str] = None

class CleanRagieService:
    """Clean Ragie service without Neo4j dependencies"""
    
    def __init__(self):
        """Initialize the service"""
        self.api_key = os.getenv("RAGIE_API_KEY")
        self.partition = os.getenv("RAGIE_PARTITION", "qsr_manuals")
        
        if not self.api_key:
            logger.error("RAGIE_API_KEY not found in environment variables")
            self.client = None
            return
        
        if not RAGIE_AVAILABLE:
            logger.error("Ragie SDK not available")
            self.client = None
            return
            
        try:
            self.client = Ragie(api_key=self.api_key)
            logger.info("✅ Ragie client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ragie client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Ragie service is available"""
        return self.client is not None
    
    async def search(self, query: str, limit: int = 5) -> List[RagieSearchResult]:
        """
        Search documents using Ragie
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        if not self.client:
            logger.error("Ragie client not available")
            return []
        
        try:
            logger.info(f"🔍 Searching Ragie: '{query}' (limit: {limit})")
            
            # Search with QSR-specific filters
            search_params = {
                "query": query,
                "partition": self.partition,
                "limit": limit,
                "filters": {
                    "document_type": "qsr_manual"
                }
            }
            
            response = self.client.search(**search_params)
            
            results = []
            for hit in response.results:
                result = RagieSearchResult(
                    text=hit.text,
                    score=hit.score,
                    document_id=hit.document_id,
                    chunk_id=hit.chunk_id,
                    metadata=hit.metadata or {}
                )
                results.append(result)
            
            logger.info(f"✅ Found {len(results)} results from Ragie")
            return results
            
        except Exception as e:
            logger.error(f"Ragie search failed: {e}")
            return []
    
    async def upload_document(self, file_path: str, metadata: Dict[str, Any]) -> RagieUploadResult:
        """
        Upload document to Ragie
        
        Args:
            file_path: Path to the document file
            metadata: Document metadata
            
        Returns:
            Upload result
        """
        if not self.client:
            return RagieUploadResult(success=False, error="Ragie client not available")
        
        try:
            logger.info(f"📤 Uploading to Ragie: {file_path}")
            
            # Prepare metadata for Ragie
            ragie_metadata = {
                "partition": self.partition,
                "document_type": "qsr_manual",
                "upload_source": "line_lead_qsr",
                **metadata
            }
            
            # Upload document
            with open(file_path, 'rb') as f:
                response = self.client.documents.create(
                    file=f,
                    metadata=ragie_metadata
                )
            
            logger.info(f"✅ Document uploaded to Ragie: {response.id}")
            
            return RagieUploadResult(
                success=True,
                document_id=response.id,
                filename=Path(file_path).name,
                chunk_count=getattr(response, 'chunk_count', None)
            )
            
        except Exception as e:
            logger.error(f"Ragie upload failed: {e}")
            return RagieUploadResult(
                success=False,
                error=str(e)
            )
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document from Ragie
        
        Args:
            document_id: Document ID in Ragie
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Ragie client not available")
            return False
        
        try:
            logger.info(f"🗑️ Deleting from Ragie: {document_id}")
            
            self.client.documents.delete(document_id)
            logger.info(f"✅ Document deleted from Ragie: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document from Ragie: {e}")
            return False

# Global service instance
clean_ragie_service = CleanRagieService()