#!/usr/bin/env python3
"""
Safe Ragie Enhancement Service
==============================

Low-risk Ragie integration that enhances the existing clean PydanticAI 
orchestration without complex dependency injection or experimental patterns.

Features:
- Pre-processing layer approach (not embedded in PydanticAI Tools)
- 2-second timeout on all Ragie calls
- 100% graceful fallback when Ragie unavailable
- Simple context injection through prompt enhancement
- Easy to disable/enable without affecting core functionality

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

# Safe imports with fallback
try:
    from services.enhanced_ragie_service import enhanced_ragie_service, QSRContext
    RAGIE_AVAILABLE = True
except ImportError:
    RAGIE_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class SafeRagieResult:
    """Safe result from Ragie enhancement"""
    enhanced_query: str
    visual_citations: List[Dict[str, Any]]
    ragie_enhanced: bool
    processing_time: float
    equipment_context: Optional[str] = None
    procedure_context: Optional[str] = None
    error: Optional[str] = None

class SafeRagieEnhancement:
    """Safe Ragie enhancement service with graceful fallbacks"""
    
    def __init__(self):
        """Initialize safe enhancement service"""
        self.available = RAGIE_AVAILABLE and getattr(enhanced_ragie_service, 'is_available', lambda: False)()
        self.timeout = 2.0  # Conservative timeout
        self.max_context_length = 500  # Prevent prompt bloat
        self.cache = {}  # Simple cache for repeated queries
        self.cache_ttl = 300  # 5 minutes
        
        if self.available:
            logger.info("✅ Safe Ragie enhancement available")
        else:
            logger.info("⚠️ Safe Ragie enhancement disabled (service unavailable)")
    
    async def enhance_query_safely(
        self, 
        query: str, 
        conversation_id: str = "default"
    ) -> SafeRagieResult:
        """
        Safely enhance query with Ragie knowledge
        
        This is the main enhancement method that:
        1. Attempts Ragie search with timeout
        2. Falls back gracefully if Ragie fails
        3. Returns enhanced prompt for existing PydanticAI orchestration
        """
        start_time = time.time()
        
        # Quick cache check
        cache_key = f"{query[:100]}:{conversation_id}"
        cached = self._get_cached_result(cache_key)
        if cached:
            logger.info(f"🎯 Cache hit for query enhancement")
            return cached
        
        if not self.available:
            return self._create_fallback_result(query, start_time, "Ragie service unavailable")
        
        try:
            # Attempt Ragie enhancement with strict timeout
            ragie_task = self._perform_ragie_search(query)
            ragie_result = await asyncio.wait_for(ragie_task, timeout=self.timeout)
            
            # Create enhanced result
            enhanced_result = self._create_enhanced_result(query, ragie_result, start_time)
            
            # Cache successful result
            self._cache_result(cache_key, enhanced_result)
            
            logger.info(f"✅ Ragie enhancement completed in {enhanced_result.processing_time:.2f}s")
            return enhanced_result
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Ragie enhancement timeout after {self.timeout}s")
            return self._create_fallback_result(query, start_time, "Timeout")
            
        except Exception as e:
            logger.warning(f"⚠️ Ragie enhancement failed: {e}")
            return self._create_fallback_result(query, start_time, str(e))
    
    async def _perform_ragie_search(self, query: str) -> Dict[str, Any]:
        """Perform Ragie search with QSR optimization"""
        # Detect QSR context for better search
        qsr_context = enhanced_ragie_service._detect_qsr_context(query)
        
        # Perform search
        results = await enhanced_ragie_service.search_with_qsr_context(
            query=query,
            qsr_context=qsr_context,
            top_k=2  # Keep minimal for performance
        )
        
        return {
            "results": results,
            "qsr_context": qsr_context
        }
    
    def _create_enhanced_result(
        self, 
        original_query: str, 
        ragie_data: Dict[str, Any], 
        start_time: float
    ) -> SafeRagieResult:
        """Create enhanced result from Ragie data"""
        results = ragie_data["results"]
        qsr_context = ragie_data["qsr_context"]
        
        if not results:
            return self._create_fallback_result(original_query, start_time, "No relevant results")
        
        # Build enhanced query with relevant context
        context_parts = []
        visual_citations = []
        
        for result in results[:2]:  # Max 2 results to prevent prompt bloat
            # Add text context (truncated)
            text_snippet = result.text[:200] + "..." if len(result.text) > 200 else result.text
            context_parts.append(text_snippet)
            
            # Collect visual citations
            if result.images:
                visual_citations.extend([{
                    "type": "image",
                    "url": img["url"],
                    "caption": img.get("caption", "Equipment diagram"),
                    "source": result.metadata.get("filename", "Manual"),
                    "relevance_score": result.score
                } for img in result.images[:2]])  # Max 2 images per result
        
        # Create enhanced query
        if context_parts:
            context_text = "\n".join(context_parts)[:self.max_context_length]
            enhanced_query = f"{original_query}\n\nRelevant Information:\n{context_text}"
        else:
            enhanced_query = original_query
        
        return SafeRagieResult(
            enhanced_query=enhanced_query,
            visual_citations=visual_citations[:5],  # Max 5 total citations
            ragie_enhanced=True,
            processing_time=time.time() - start_time,
            equipment_context=qsr_context.equipment_type if qsr_context else None,
            procedure_context=qsr_context.procedure_type if qsr_context else None
        )
    
    def _create_fallback_result(
        self, 
        original_query: str, 
        start_time: float, 
        reason: str
    ) -> SafeRagieResult:
        """Create fallback result when Ragie enhancement fails"""
        return SafeRagieResult(
            enhanced_query=original_query,  # Use original query unchanged
            visual_citations=[],
            ragie_enhanced=False,
            processing_time=time.time() - start_time,
            error=reason
        )
    
    def _get_cached_result(self, cache_key: str) -> Optional[SafeRagieResult]:
        """Get cached result if still valid"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["result"]
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: SafeRagieResult):
        """Cache result for future use"""
        self.cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
    
    def get_enhancement_stats(self) -> Dict[str, Any]:
        """Get enhancement performance statistics"""
        return {
            "available": self.available,
            "timeout_seconds": self.timeout,
            "max_context_length": self.max_context_length,
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl
        }

# Global safe enhancement service
safe_ragie_enhancement = SafeRagieEnhancement()

# Simple usage pattern for existing orchestrator
async def enhance_query_for_orchestrator(
    query: str, 
    conversation_id: str = "default"
) -> Dict[str, Any]:
    """
    Simple enhancement function for existing orchestrator integration
    
    Usage in existing code:
    enhanced_data = await enhance_query_for_orchestrator(query)
    response = await orchestrator.handle_query(enhanced_data["query"])
    response.visual_citations = enhanced_data["visual_citations"]
    """
    result = await safe_ragie_enhancement.enhance_query_safely(query, conversation_id)
    
    return {
        "query": result.enhanced_query,
        "visual_citations": result.visual_citations,
        "ragie_enhanced": result.ragie_enhanced,
        "equipment_context": result.equipment_context,
        "procedure_context": result.procedure_context,
        "processing_time": result.processing_time
    }