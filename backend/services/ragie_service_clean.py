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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ragie SDK imports
try:
    from ragie import Ragie
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
    images: Optional[List[Dict[str, Any]]] = None  # Image references from chunk

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
            self.client = Ragie(auth=self.api_key)
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
            
            # Search using SDK pattern from reference app
            search_request = {
                "query": query,
                "filter_": {
                    "qsr_document_type": "manual"
                },
                "rerank": True,
                "partition": self.partition,
                "limit": limit
            }
            
            response = self.client.retrievals.retrieve(request=search_request)
            
            results = []
            if hasattr(response, 'scored_chunks') and response.scored_chunks:
                for chunk in response.scored_chunks:
                    chunk_metadata = getattr(chunk, 'metadata', {})
                    chunk_text = getattr(chunk, 'text', '')
                    
                    # Enhanced metadata parsing based on Ragie documentation
                    # Check for file_type in metadata to identify content type
                    file_type = chunk_metadata.get('file_type', 'pdf')  # Default to pdf for text chunks
                    
                    # Debug enhanced metadata structure
                    logger.info(f"🔍 Chunk metadata: file_type={file_type}, keys={list(chunk_metadata.keys())}")
                    
                    # Enhanced content type detection from text patterns
                    image_keywords = ['figure', 'diagram', 'image', 'see illustration', 'pictured', 'photo', 'picture', 'visual', 'shown below', 'see below', 'example shown', 'gourmet', 'display']
                    video_keywords = ['video', 'demonstration', 'tutorial', 'watch', 'play']
                    
                    if file_type == 'pdf':
                        if any(keyword in chunk_text.lower() for keyword in image_keywords):
                            # This text chunk refers to visual content - mark as image type
                            file_type = 'image'
                            chunk_metadata['file_type'] = 'image'
                            logger.info(f"🖼️ Detected image reference in text: {chunk_text[:100]}...")
                        elif any(keyword in chunk_text.lower() for keyword in video_keywords):
                            # This text chunk refers to video content
                            file_type = 'video'
                            chunk_metadata['file_type'] = 'video'
                            logger.info(f"🎥 Detected video reference in text: {chunk_text[:100]}...")
                    
                    # Extract source and page information
                    source = chunk_metadata.get('source') or chunk_metadata.get('original_filename') or getattr(chunk, 'document_name', 'Unknown')
                    page_number = chunk_metadata.get('page_number', None)
                    
                    # Extract image information based on content type
                    images = []
                    url = None
                    
                    # Check for direct image URLs in various metadata fields
                    if 'images' in chunk_metadata:
                        images = chunk_metadata['images']
                        logger.info(f"🖼️ Found images in metadata: {len(images)}")
                    elif 'image_urls' in chunk_metadata:
                        images = [{'url': url} for url in chunk_metadata['image_urls']]
                        logger.info(f"🖼️ Found image_urls in metadata: {len(images)}")
                    elif 'url' in chunk_metadata:
                        url = chunk_metadata['url']
                        images = [{'url': url, 'caption': chunk_text[:100]}]
                        logger.info(f"🖼️ Found direct URL in metadata: {url}")
                    elif hasattr(chunk, 'images') and chunk.images:
                        images = chunk.images
                        logger.info(f"🖼️ Found images in chunk attributes: {len(images)}")
                    elif hasattr(chunk, 'links') and chunk.links:
                        # Check if links contain image references
                        links = chunk.links
                        if isinstance(links, list):
                            for link in links:
                                if hasattr(link, 'url') and any(ext in link.url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                    images.append({
                                        'url': link.url,
                                        'caption': getattr(link, 'text', chunk_text[:100]),
                                        'type': 'image'
                                    })
                        logger.info(f"🖼️ Found images in links: {len(images)}")
                    
                    # Enhance metadata with parsed information
                    enhanced_metadata = {
                        **chunk_metadata,
                        'file_type': file_type,
                        'source': source,
                        'page_number': page_number,
                        'content_type': file_type,
                        'has_images': len(images) > 0,
                        'image_count': len(images)
                    }
                    
                    # Add equipment-specific metadata if detected
                    if any(equip in chunk_text.lower() for equip in ['fryer', 'grill', 'oven', 'freezer', 'equipment']):
                        enhanced_metadata['equipment_type'] = 'kitchen_equipment'
                        if 'cleaning' in chunk_text.lower() or 'maintenance' in chunk_text.lower():
                            enhanced_metadata['procedure'] = 'maintenance'
                        elif 'cooking' in chunk_text.lower() or 'operating' in chunk_text.lower():
                            enhanced_metadata['procedure'] = 'operation'
                    
                    result = RagieSearchResult(
                        text=chunk_text,
                        score=chunk.score,
                        document_id=getattr(chunk, 'document_id', ''),
                        chunk_id=getattr(chunk, 'chunk_id', ''),
                        metadata=enhanced_metadata,
                        images=images if images else None
                    )
                    results.append(result)
            
            logger.info(f"✅ Found {len(results)} results from Ragie")
            return results
            
        except Exception as e:
            logger.error(f"Ragie search failed: {e}")
            return []
    
    async def get_document_images(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Try to get images from a Ragie document
        This is experimental - checking if Ragie provides image access
        """
        if not self.client:
            return []
        
        try:
            # This might not exist in the current Ragie API
            # But let's try different approaches
            logger.info(f"🖼️ Attempting to retrieve images for document: {document_id}")
            
            # Check if there's a way to get document details including images
            # This is exploratory - the actual API might be different
            return []
            
        except Exception as e:
            logger.debug(f"Image retrieval not supported or failed: {e}")
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
            
            # Prepare metadata for Ragie (exclude reserved keys)
            ragie_metadata = {
                "equipment_type": metadata.get("equipment_type", "general"),
                "qsr_document_type": "manual",  # Renamed to avoid 'document_type' reserved key
                "upload_source": "line_lead_qsr",
                "original_filename": metadata.get("original_filename", ""),
                "file_size": metadata.get("file_size", 0),
                "pages_count": metadata.get("pages_count", 0)
            }
            
            # Upload document using SDK pattern from reference app
            with open(file_path, 'rb') as f:
                create_request = {
                    "file": {
                        "file_name": Path(file_path).name,
                        "content": f,
                    },
                    "metadata": ragie_metadata,
                    "mode": "hi_res",  # Extract images and tables for QSR manuals
                    "partition": self.partition
                }
                
                response = self.client.documents.create(request=create_request)
            
            if response and response.id:
                logger.info(f"✅ Document uploaded to Ragie: {response.id}")
                logger.info(f"📊 Ragie processing stats: {getattr(response, 'chunk_count', 'unknown')} chunks, {getattr(response, 'page_count', 'unknown')} pages")
                
                return RagieUploadResult(
                    success=True,
                    document_id=response.id,
                    filename=Path(file_path).name,
                    chunk_count=getattr(response, 'chunk_count', None)
                )
            else:
                logger.error("❌ Ragie upload returned invalid response")
                return RagieUploadResult(success=False, error="Invalid response from Ragie")
                
            
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