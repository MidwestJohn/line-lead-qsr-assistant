#!/usr/bin/env python3
"""
Enhanced Ragie Service for PydanticAI Integration
================================================

Combines the clean architecture from ragie_service_clean.py with the enhanced
functionality from ragie_service.py for optimal PydanticAI integration.

Features:
- Clean dependency injection patterns for PydanticAI RunContext
- QSR-optimized search with equipment/procedure detection  
- Multi-modal content support and visual citations
- Async-first design with proper error handling
- Production-ready with fallback strategies

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import time
import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import json
from pathlib import Path
from dotenv import load_dotenv
import asyncio

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
    """Enhanced result from Ragie search with QSR optimization"""
    text: str
    score: float
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any]
    images: Optional[List[Dict[str, Any]]] = None
    equipment_context: Optional[str] = None
    procedure_context: Optional[str] = None
    safety_level: Optional[str] = None

@dataclass
class RagieUploadResult:
    """Result from Ragie upload with enhanced metadata"""
    success: bool
    document_id: Optional[str] = None
    filename: Optional[str] = None
    chunk_count: Optional[int] = None
    page_count: Optional[int] = None
    qsr_metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class QSRContext:
    """QSR-specific context for enhanced search"""
    equipment_type: Optional[str] = None
    procedure_type: Optional[str] = None
    safety_level: Optional[str] = None
    conversation_history: List[str] = field(default_factory=list)

class EnhancedRagieService:
    """Enhanced Ragie service optimized for PydanticAI integration"""
    
    def __init__(self):
        """Initialize service with QSR optimization"""
        self.api_key = os.getenv("RAGIE_API_KEY")
        self.partition = os.getenv("RAGIE_PARTITION", "qsr_manuals")
        
        # Sanitize API key for HTTP headers to prevent Unicode encoding errors
        if self.api_key:
            try:
                self.api_key = self.api_key.encode('ascii', 'ignore').decode('ascii').strip()
                logger.info(f"🧹 Ragie API key sanitized for HTTP headers")
            except Exception as e:
                logger.warning(f"⚠️ Failed to sanitize API key: {e}")
                self.api_key = None
        
        self.available = RAGIE_AVAILABLE and bool(self.api_key)
        
        if self.available:
            self.client = Ragie(auth=self.api_key)
            logger.info(f"✅ Enhanced Ragie client initialized with partition: {self.partition}")
        else:
            logger.warning("❌ Ragie service not available (missing API key or SDK)")
            
        # QSR-specific configuration
        self.qsr_equipment_types = {
            "fryer", "grill", "oven", "ice_machine", "pos_system", 
            "drive_thru", "prep_station", "dishwasher", "mixer",
            "taylor", "grote", "canotto", "romana"  # Brand-specific
        }
        
        self.qsr_procedure_types = {
            "cleaning", "maintenance", "troubleshooting", "setup", 
            "safety", "daily_ops", "opening", "closing"
        }
        
        # Cache for search results
        self._search_cache = {}
        self._cache_ttl = int(os.getenv("RAGIE_CACHE_TTL", "300"))  # 5 minutes
    
    def is_available(self) -> bool:
        """Check if Ragie service is available"""
        return self.available
    
    async def search_with_qsr_context(
        self, 
        query: str, 
        qsr_context: Optional[QSRContext] = None,
        top_k: int = 5
    ) -> List[RagieSearchResult]:
        """
        Enhanced search with QSR context optimization
        
        Designed for PydanticAI RunContext integration:
        
        @agent.tool
        async def search_equipment_docs(ctx: RunContext[QSRRunContext], equipment: str) -> List[RagieSearchResult]:
            return await ctx.deps.ragie_service.search_with_qsr_context(
                query=f"equipment {equipment}",
                qsr_context=QSRContext(equipment_type=equipment)
            )
        """
        if not self.available:
            logger.warning("Ragie service not available for search")
            return []
            
        try:
            # Sanitize query to prevent encoding issues
            logger.info(f"🔤 Original query: {repr(query)}")
            sanitized_query = self._sanitize_query(query)
            logger.info(f"🧹 Sanitized query: {repr(sanitized_query)}")
            
            # Check cache first
            cache_key = f"{sanitized_query}:{hash(str(qsr_context))}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"🎯 Cache hit for query: {sanitized_query[:50]}...")
                return cached_result
            
            # Detect QSR intent if context not provided
            if not qsr_context:
                qsr_context = self._detect_qsr_context(sanitized_query)
            
            # Build search filters
            filters = self._build_search_filters(qsr_context)
            
            # Log request details before making API call
            logger.info(f"🌐 Making Ragie API request with query: {repr(sanitized_query)}")
            logger.info(f"📁 Partition: {self.partition}")
            logger.info(f"🔢 Top K: {top_k}")
            
            # Perform Ragie search with sanitized query
            response = self.client.retrievals.retrieve(request={
                "query": sanitized_query,
                "partition": self.partition,
                "top_k": top_k,
                "filter": filters if filters else {},
                "mode": "hybrid"  # Best for QSR technical content
            })
            
            # Parse and enhance results
            results = []
            for chunk in response.scored_chunks:
                result = RagieSearchResult(
                    text=chunk.text,
                    score=chunk.score,
                    document_id=getattr(chunk, 'document_id', 'unknown'),
                    chunk_id=getattr(chunk, 'chunk_id', getattr(chunk, 'id', 'unknown')),
                    metadata=getattr(chunk, 'metadata', {}) or {},
                    equipment_context=qsr_context.equipment_type if qsr_context else None,
                    procedure_context=qsr_context.procedure_type if qsr_context else None,
                    safety_level=qsr_context.safety_level if qsr_context else None
                )
                
                # Enhance with images if available
                if hasattr(chunk, 'images') and chunk.images:
                    result.images = [{"url": img.url, "caption": img.caption} for img in chunk.images]
                
                results.append(result)
            
            # Cache results
            self._cache_results(cache_key, results)
            
            logger.info(f"📚 Retrieved {len(results)} QSR-optimized chunks for: {sanitized_query[:50]}...")
            return results
            
        except UnicodeEncodeError as e:
            logger.error(f"❌ Unicode encoding error in Ragie search: {e}")
            logger.error(f"🔤 Problematic query: {repr(query)}")
            logger.error(f"🧹 Sanitized query: {repr(sanitized_query if 'sanitized_query' in locals() else 'Not set')}")
            # Try with super-safe ASCII-only query
            try:
                safe_query = ''.join(c for c in query if ord(c) < 128)
                logger.info(f"🔒 Retrying with ASCII-only query: {repr(safe_query)}")
                response = self.client.retrievals.retrieve(request={
                    "query": safe_query,
                    "partition": self.partition,
                    "top_k": top_k,
                    "filter": {},
                    "mode": "hybrid"
                })
                logger.info(f"✅ ASCII-only retry successful")
                # Process response normally...
                results = []
                for chunk in response.scored_chunks:
                    result = RagieSearchResult(
                        text=chunk.text,
                        score=chunk.score,
                        document_id=getattr(chunk, 'document_id', 'unknown'),
                        chunk_id=getattr(chunk, 'chunk_id', getattr(chunk, 'id', 'unknown')),
                        metadata=getattr(chunk, 'metadata', {}) or {},
                        equipment_context=qsr_context.equipment_type if qsr_context else None,
                        procedure_context=qsr_context.procedure_type if qsr_context else None,
                        safety_level=qsr_context.safety_level if qsr_context else None
                    )
                    results.append(result)
                return results
            except Exception as retry_error:
                logger.error(f"❌ ASCII-only retry also failed: {retry_error}")
                return []
        except Exception as e:
            logger.error(f"Enhanced Ragie search failed: {e}")
            return []
    
    async def upload_document(
        self, 
        file_path: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> RagieUploadResult:
        """Upload document with QSR metadata enhancement"""
        if not self.available:
            return RagieUploadResult(success=False, error="Ragie service not available")
        
        try:
            # Enhance metadata with QSR tags
            enhanced_metadata = self._enhance_qsr_metadata(file_path, metadata or {})
            
            # Upload to Ragie
            with open(file_path, 'rb') as f:
                response = self.client.documents.create(request={
                    "file": {
                        "file_name": Path(file_path).name,
                        "content": f,
                    },
                    "mode": "hi_res",  # Extract images for QSR diagrams
                    "metadata": enhanced_metadata,
                    "partition": self.partition,
                    "name": enhanced_metadata.get("display_name", Path(file_path).name)
                })
            
            logger.info(f"✅ Uploaded {Path(file_path).name} to Ragie: {response.id}")
            
            return RagieUploadResult(
                success=True,
                document_id=response.id,
                filename=Path(file_path).name,
                chunk_count=getattr(response, 'chunk_count', None),
                page_count=getattr(response, 'page_count', None),
                qsr_metadata=enhanced_metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            return RagieUploadResult(success=False, error=str(e))
    
    async def get_visual_citations(self, query: str) -> List[Dict[str, Any]]:
        """Extract visual citations for frontend display"""
        results = await self.search_with_qsr_context(query, top_k=3)
        
        citations = []
        for result in results:
            if result.images:
                for img in result.images:
                    citations.append({
                        "type": "image",
                        "url": img["url"],
                        "caption": img.get("caption", ""),
                        "source_document": result.metadata.get("filename", "Unknown"),
                        "relevance_score": result.score
                    })
            
            # Add text citations
            citations.append({
                "type": "text",
                "content": result.text[:200] + "..." if len(result.text) > 200 else result.text,
                "source_document": result.metadata.get("filename", "Unknown"),
                "page": result.metadata.get("page_number"),
                "relevance_score": result.score
            })
        
        return citations
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize query to handle Unicode and encoding issues"""
        try:
            # Ensure we have a string
            if not isinstance(query, str):
                query = str(query)
            
            # Replace problematic Unicode characters with ASCII equivalents
            query = query.replace('"', '"').replace('"', '"')  # Smart quotes
            query = query.replace(''', "'").replace(''', "'")  # Smart apostrophes  
            query = query.replace('—', '-').replace('–', '-')  # Em/en dashes
            query = query.replace('…', '...')  # Ellipsis
            
            # Encode to ASCII, replacing problematic characters
            query = query.encode('ascii', 'ignore').decode('ascii')
            
            # Clean up extra whitespace
            query = ' '.join(query.split())
            
            return query
        except Exception as e:
            logger.warning(f"Query sanitization failed: {e}, using fallback")
            # Fallback: keep only alphanumeric, spaces, and basic punctuation
            import re
            return re.sub(r'[^\w\s\-\.\,\?\!]', '', str(query))

    def _detect_qsr_context(self, query: str) -> QSRContext:
        """Detect QSR context from query text"""
        # Sanitize query first to prevent encoding errors
        query = self._sanitize_query(query)
        query_lower = query.lower()
        
        # Detect equipment
        equipment_type = None
        for equipment in self.qsr_equipment_types:
            if equipment in query_lower:
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
        if any(word in query_lower for word in ["danger", "warning", "caution", "safety"]):
            safety_level = "high"
        elif any(word in query_lower for word in ["careful", "notice", "important"]):
            safety_level = "medium"
        
        return QSRContext(
            equipment_type=equipment_type,
            procedure_type=procedure_type,
            safety_level=safety_level
        )
    
    def _build_search_filters(self, qsr_context: QSRContext) -> Dict[str, Any]:
        """Build Ragie search filters from QSR context"""
        # TEMP FIX: Disable restrictive filters that block results
        # The documents don't have structured metadata, so filters are too restrictive
        # Instead, rely on the query text matching and QSR context for ranking
        filters = {}
        
        # TODO: Re-enable filters once document metadata is properly structured
        # if qsr_context.equipment_type:
        #     filters["equipment_type"] = qsr_context.equipment_type
        # if qsr_context.procedure_type:
        #     filters["procedure_type"] = qsr_context.procedure_type
        # if qsr_context.safety_level:
        #     filters["safety_level"] = qsr_context.safety_level
        
        return filters
    
    def _enhance_qsr_metadata(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata with QSR-specific tags"""
        enhanced = metadata.copy()
        filename = Path(file_path).name.lower()
        
        # Auto-detect equipment from filename
        for equipment in self.qsr_equipment_types:
            if equipment in filename:
                enhanced["equipment_type"] = equipment
                break
        
        # Auto-detect document type
        if any(word in filename for word in ["manual", "guide", "instruction"]):
            enhanced["document_type"] = "manual"
        elif any(word in filename for word in ["sop", "procedure", "process"]):
            enhanced["document_type"] = "procedure"
        elif any(word in filename for word in ["safety", "msds", "hazard"]):
            enhanced["document_type"] = "safety"
            enhanced["safety_level"] = "high"
        
        # Add upload timestamp
        enhanced["upload_timestamp"] = datetime.datetime.now().isoformat()
        enhanced["display_name"] = metadata.get("original_filename", Path(file_path).name)
        
        return enhanced
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[RagieSearchResult]]:
        """Get results from cache if still valid"""
        if cache_key in self._search_cache:
            cached_data = self._search_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self._cache_ttl:
                return cached_data["results"]
            else:
                # Remove expired cache entry
                del self._search_cache[cache_key]
        return None
    
    def _cache_results(self, cache_key: str, results: List[RagieSearchResult]):
        """Cache search results"""
        self._search_cache[cache_key] = {
            "results": results,
            "timestamp": time.time()
        }

# Global service instance for dependency injection
enhanced_ragie_service = EnhancedRagieService()

# Backward compatibility alias
clean_ragie_service = enhanced_ragie_service