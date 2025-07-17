#!/usr/bin/env python3
"""
Ragie Document Source Service
=============================

Integrates Ragie's document source API to provide original media file access
for rendering images, videos, and audio in the Line Lead QSR MVP.

Based on BaseChat implementation patterns:
- Direct document source API integration
- Proper authentication with Ragie API key
- Error handling and fallback mechanisms
- Caching strategy for performance

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import aiofiles
import aiohttp
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
class DocumentSourceResult:
    """Result from document source API"""
    success: bool
    content: Optional[bytes] = None
    content_type: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None
    error: Optional[str] = None
    cached: bool = False
    document_id: Optional[str] = None

@dataclass
class DocumentMetadata:
    """Document metadata from Ragie"""
    document_id: str
    name: str
    content_type: str
    size: int
    created_at: str
    metadata: Dict[str, Any]

class RagieDocumentSourceService:
    """
    Service for accessing original document files from Ragie
    
    Following BaseChat patterns for document source integration
    """
    
    def __init__(self):
        """Initialize Ragie document source service"""
        self.api_key = os.getenv("RAGIE_API_KEY")
        self.partition = os.getenv("RAGIE_PARTITION", "qsr_manuals")
        self.base_url = "https://api.ragie.ai"
        
        # Cache configuration
        self.cache_dir = Path("cache/ragie_sources")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)  # Cache for 24 hours
        
        # Initialize Ragie client
        self.client = None
        if self.api_key and RAGIE_AVAILABLE:
            try:
                self.client = Ragie(auth=self.api_key)
                logger.info("✅ Ragie Document Source Service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Ragie client: {e}")
                self.client = None
        else:
            logger.warning("❌ Ragie Document Source Service not available")
            
    def is_available(self) -> bool:
        """Check if service is available"""
        return self.client is not None and self.api_key is not None
    
    def _get_cache_path(self, document_id: str) -> Path:
        """Get cache file path for document"""
        # Use document ID hash for cache filename
        cache_key = hashlib.md5(f"{document_id}_{self.partition}".encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.cache"
    
    def _get_cache_metadata_path(self, document_id: str) -> Path:
        """Get cache metadata file path for document"""
        cache_key = hashlib.md5(f"{document_id}_{self.partition}".encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.meta"
    
    async def _is_cache_valid(self, document_id: str) -> bool:
        """Check if cached document is still valid"""
        cache_path = self._get_cache_path(document_id)
        meta_path = self._get_cache_metadata_path(document_id)
        
        if not cache_path.exists() or not meta_path.exists():
            return False
            
        try:
            # Check if cache is within TTL
            cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if datetime.now() - cache_time > self.cache_ttl:
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Cache validation error for {document_id}: {e}")
            return False
    
    async def _get_cached_document(self, document_id: str) -> Optional[DocumentSourceResult]:
        """Get document from cache if available"""
        try:
            if not await self._is_cache_valid(document_id):
                return None
            
            cache_path = self._get_cache_path(document_id)
            meta_path = self._get_cache_metadata_path(document_id)
            
            # Load metadata
            async with aiofiles.open(meta_path, 'r') as f:
                import json
                metadata = json.loads(await f.read())
            
            # Load content
            async with aiofiles.open(cache_path, 'rb') as f:
                content = await f.read()
            
            logger.info(f"📦 Cache hit for document {document_id}")
            
            return DocumentSourceResult(
                success=True,
                content=content,
                content_type=metadata.get('content_type'),
                filename=metadata.get('filename'),
                size=metadata.get('size'),
                cached=True,
                document_id=document_id
            )
            
        except Exception as e:
            logger.warning(f"Cache read error for {document_id}: {e}")
            return None
    
    async def _cache_document(self, document_id: str, result: DocumentSourceResult) -> None:
        """Cache document content and metadata"""
        try:
            if not result.success or not result.content:
                return
                
            cache_path = self._get_cache_path(document_id)
            meta_path = self._get_cache_metadata_path(document_id)
            
            # Save content
            async with aiofiles.open(cache_path, 'wb') as f:
                await f.write(result.content)
            
            # Save metadata
            metadata = {
                'content_type': result.content_type,
                'filename': result.filename,
                'size': result.size,
                'document_id': document_id,
                'cached_at': datetime.now().isoformat()
            }
            
            async with aiofiles.open(meta_path, 'w') as f:
                import json
                await f.write(json.dumps(metadata))
            
            logger.info(f"💾 Cached document {document_id} ({result.size} bytes)")
            
        except Exception as e:
            logger.warning(f"Cache write error for {document_id}: {e}")
    
    async def get_document_source(self, document_id: str) -> DocumentSourceResult:
        """
        Get original document file from Ragie
        
        Args:
            document_id: Ragie document ID
            
        Returns:
            DocumentSourceResult with file content and metadata
        """
        if not self.is_available():
            return DocumentSourceResult(
                success=False,
                error="Ragie Document Source Service not available"
            )
        
        try:
            # Check cache first
            cached_result = await self._get_cached_document(document_id)
            if cached_result:
                return cached_result
            
            logger.info(f"📥 Fetching document source for {document_id}")
            start_time = time.time()
            
            # Use aiohttp for async HTTP requests
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/documents/{document_id}/source"
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Partition': self.partition
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('Content-Type', 'application/octet-stream')
                        
                        # Try to extract filename from Content-Disposition header
                        content_disposition = response.headers.get('Content-Disposition', '')
                        filename = None
                        if 'filename=' in content_disposition:
                            filename = content_disposition.split('filename=')[1].strip('"')
                        
                        result = DocumentSourceResult(
                            success=True,
                            content=content,
                            content_type=content_type,
                            filename=filename,
                            size=len(content),
                            document_id=document_id
                        )
                        
                        # Cache the result
                        await self._cache_document(document_id, result)
                        
                        fetch_time = time.time() - start_time
                        logger.info(f"✅ Document source fetched: {document_id} ({len(content)} bytes, {fetch_time:.2f}s)")
                        
                        return result
                    
                    elif response.status == 404:
                        return DocumentSourceResult(
                            success=False,
                            error=f"Document {document_id} not found",
                            document_id=document_id
                        )
                    
                    else:
                        error_text = await response.text()
                        return DocumentSourceResult(
                            success=False,
                            error=f"HTTP {response.status}: {error_text}",
                            document_id=document_id
                        )
                        
        except Exception as e:
            logger.error(f"❌ Error fetching document source {document_id}: {e}")
            return DocumentSourceResult(
                success=False,
                error=str(e),
                document_id=document_id
            )
    
    async def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """
        Get document metadata from Ragie
        
        Args:
            document_id: Ragie document ID
            
        Returns:
            DocumentMetadata or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            # Use the Ragie client to get document metadata
            document = self.client.documents.get(document_id=document_id, partition=self.partition)
            
            return DocumentMetadata(
                document_id=document_id,
                name=document.name,
                content_type=document.metadata.get('content_type', 'application/octet-stream'),
                size=document.metadata.get('file_size', 0),
                created_at=document.created_at,
                metadata=document.metadata
            )
            
        except Exception as e:
            logger.warning(f"Could not get metadata for document {document_id}: {e}")
            return None
    
    async def clear_cache(self) -> int:
        """
        Clear all cached documents
        
        Returns:
            Number of files cleared
        """
        try:
            files_cleared = 0
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    files_cleared += 1
            
            logger.info(f"🗑️ Cleared {files_cleared} cached files")
            return files_cleared
            
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            meta_files = list(self.cache_dir.glob("*.meta"))
            
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'cached_documents': len(cache_files),
                'metadata_files': len(meta_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_directory': str(self.cache_dir),
                'cache_ttl_hours': self.cache_ttl.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {}

# Global service instance
ragie_document_source_service = RagieDocumentSourceService()