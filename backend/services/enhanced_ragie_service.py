#!/usr/bin/env python3
"""
Enhanced Ragie Service - Phase 2 Implementation
===============================================

Enhanced Ragie integration that works with specialist agents to provide
contextually relevant document search and retrieval. Filters and prioritizes
content based on agent type and query classification.

Features:
- Agent-specific document filtering
- Contextual search enhancement
- QSR domain-specific search optimization
- Performance optimization and caching
- Error handling and fallback mechanisms

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

import httpx
from pydantic import BaseModel, Field

# Import agent types for filtering
try:
    from ..agents.qsr_orchestrator import AgentType, QueryClassification
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from agents.qsr_orchestrator import AgentType, QueryClassification

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RagieSearchFilter(BaseModel):
    """Search filters specific to agent types"""
    agent_type: AgentType = Field(description="Agent type for filtering")
    equipment_brands: List[str] = Field(default_factory=list, description="Equipment brands to prioritize")
    document_types: List[str] = Field(default_factory=list, description="Document types to include")
    safety_keywords: List[str] = Field(default_factory=list, description="Safety-related keywords")
    urgency_boost: float = Field(default=1.0, description="Boost factor for urgent content")


class RagieSearchResult(BaseModel):
    """Enhanced search result with agent-specific scoring"""
    content: str = Field(description="Document content")
    source: str = Field(description="Source document")
    score: float = Field(description="Relevance score")
    agent_relevance: float = Field(description="Agent-specific relevance score")
    document_type: str = Field(description="Type of document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EnhancedRagieResponse(BaseModel):
    """Enhanced response from Ragie search"""
    results: List[RagieSearchResult] = Field(description="Search results")
    total_results: int = Field(description="Total number of results")
    query_used: str = Field(description="Actual query sent to Ragie")
    agent_type: AgentType = Field(description="Agent type used for filtering")
    processing_time: float = Field(description="Processing time in seconds")
    cache_hit: bool = Field(default=False, description="Whether result was cached")


@dataclass
class EnhancedRagieService:
    """
    Enhanced Ragie service with agent-specific optimization.
    
    Provides contextually relevant document search based on the agent type
    and query classification, with performance optimization and caching.
    """
    
    # Configuration
    base_url: str = field(default_factory=lambda: os.getenv("RAGIE_BASE_URL", "https://api.ragie.ai"))
    api_key: str = field(default_factory=lambda: os.getenv("RAGIE_API_KEY", ""))
    timeout: int = 30
    max_results: int = 10
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    # Performance tracking
    query_count: int = field(default=0)
    cache_hits: int = field(default=0)
    average_response_time: float = field(default=0.0)
    
    # Internal state
    _client: Optional[httpx.AsyncClient] = field(default=None, init=False)
    _cache: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)
    _initialized: bool = field(default=False, init=False)
    
    def __post_init__(self):
        """Initialize logging"""
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> None:
        """Initialize the Ragie service"""
        if self._initialized:
            return
        
        try:
            # Initialize HTTP client
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            self._initialized = True
            self.logger.info("Enhanced Ragie service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Ragie service: {e}")
            raise
    
    async def search_for_agent(
        self,
        query: str,
        agent_type: AgentType,
        classification: Optional[QueryClassification] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> EnhancedRagieResponse:
        """
        Search documents with agent-specific optimization.
        
        Args:
            query: The search query
            agent_type: Type of agent making the request
            classification: Query classification for additional context
            context: Additional context for search optimization
            
        Returns:
            Enhanced search results optimized for the agent type
        """
        
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        self.query_count += 1
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query, agent_type, classification)
            if self.enable_caching and cache_key in self._cache:
                cached_result = self._cache[cache_key]
                if datetime.now() - cached_result["timestamp"] < timedelta(seconds=self.cache_ttl):
                    self.cache_hits += 1
                    cached_result["response"].cache_hit = True
                    return cached_result["response"]
            
            # Create agent-specific search filter
            search_filter = self._create_search_filter(agent_type, classification, context)
            
            # Enhance query for agent type
            enhanced_query = self._enhance_query_for_agent(query, agent_type, classification)
            
            # Perform Ragie search
            ragie_results = await self._perform_ragie_search(enhanced_query, search_filter)
            
            # Process and score results for agent
            processed_results = self._process_results_for_agent(
                ragie_results, 
                agent_type, 
                classification,
                query
            )
            
            # Create enhanced response
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(processing_time)
            
            response = EnhancedRagieResponse(
                results=processed_results,
                total_results=len(processed_results),
                query_used=enhanced_query,
                agent_type=agent_type,
                processing_time=processing_time,
                cache_hit=False
            )
            
            # Cache the result
            if self.enable_caching:
                self._cache[cache_key] = {
                    "response": response,
                    "timestamp": datetime.now()
                }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in agent search: {e}")
            # Return empty results rather than failing
            return EnhancedRagieResponse(
                results=[],
                total_results=0,
                query_used=query,
                agent_type=agent_type,
                processing_time=(datetime.now() - start_time).total_seconds(),
                cache_hit=False
            )
    
    def _create_search_filter(
        self,
        agent_type: AgentType,
        classification: Optional[QueryClassification] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RagieSearchFilter:
        """Create search filter based on agent type"""
        
        if agent_type == AgentType.EQUIPMENT:
            return RagieSearchFilter(
                agent_type=agent_type,
                equipment_brands=["taylor", "vulcan", "hobart", "traulsen", "pitco", "frymaster"],
                document_types=["manual", "troubleshooting", "maintenance", "specs"],
                safety_keywords=["safety", "caution", "warning", "danger"],
                urgency_boost=1.2 if classification and classification.urgency == "high" else 1.0
            )
            
        elif agent_type == AgentType.SAFETY:
            return RagieSearchFilter(
                agent_type=agent_type,
                equipment_brands=[],
                document_types=["safety", "emergency", "protocols", "procedures", "training"],
                safety_keywords=["emergency", "fire", "burn", "cut", "injury", "hazard", "dangerous"],
                urgency_boost=2.0 if classification and classification.urgency == "high" else 1.5
            )
            
        elif agent_type == AgentType.OPERATIONS:
            return RagieSearchFilter(
                agent_type=agent_type,
                equipment_brands=[],
                document_types=["procedures", "operations", "management", "quality", "customer"],
                safety_keywords=["procedure", "process", "workflow", "checklist"],
                urgency_boost=1.1 if classification and classification.urgency == "high" else 1.0
            )
            
        elif agent_type == AgentType.TRAINING:
            return RagieSearchFilter(
                agent_type=agent_type,
                equipment_brands=[],
                document_types=["training", "certification", "onboarding", "skills", "assessment"],
                safety_keywords=["training", "learning", "certification", "competency"],
                urgency_boost=1.0
            )
        
        # Base agent - no specific filtering
        return RagieSearchFilter(
            agent_type=agent_type,
            equipment_brands=[],
            document_types=[],
            safety_keywords=[],
            urgency_boost=1.0
        )
    
    def _enhance_query_for_agent(
        self,
        query: str,
        agent_type: AgentType,
        classification: Optional[QueryClassification] = None
    ) -> str:
        """Enhance the search query based on agent type"""
        
        enhanced_query = query
        
        if agent_type == AgentType.EQUIPMENT:
            # Add equipment-specific terms
            equipment_terms = ["equipment", "machine", "device", "repair", "maintenance", "troubleshooting"]
            if not any(term in query.lower() for term in equipment_terms):
                enhanced_query += " equipment maintenance"
        
        elif agent_type == AgentType.SAFETY:
            # Add safety-specific terms
            safety_terms = ["safety", "emergency", "procedure", "protocol"]
            if not any(term in query.lower() for term in safety_terms):
                enhanced_query += " safety procedures"
        
        elif agent_type == AgentType.OPERATIONS:
            # Add operations-specific terms
            ops_terms = ["procedure", "process", "operation", "workflow"]
            if not any(term in query.lower() for term in ops_terms):
                enhanced_query += " operational procedures"
        
        elif agent_type == AgentType.TRAINING:
            # Add training-specific terms
            training_terms = ["training", "learning", "certification", "skill"]
            if not any(term in query.lower() for term in training_terms):
                enhanced_query += " training procedures"
        
        # Add urgency indicators for high-priority queries
        if classification and classification.urgency == "high":
            enhanced_query += " urgent emergency immediate"
        
        return enhanced_query
    
    async def _perform_ragie_search(
        self,
        query: str,
        search_filter: RagieSearchFilter
    ) -> List[Dict[str, Any]]:
        """Perform the actual Ragie API search"""
        
        try:
            # Prepare search request
            search_payload = {
                "query": query,
                "k": self.max_results,
                "filter": {
                    "document_types": search_filter.document_types,
                    "keywords": search_filter.safety_keywords
                }
            }
            
            # Make API call to Ragie
            response = await self._client.post("/search", json=search_payload)
            response.raise_for_status()
            
            results = response.json()
            return results.get("results", [])
            
        except httpx.HTTPError as e:
            self.logger.error(f"Ragie API error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error in Ragie search: {e}")
            return []
    
    def _process_results_for_agent(
        self,
        raw_results: List[Dict[str, Any]],
        agent_type: AgentType,
        classification: Optional[QueryClassification],
        original_query: str
    ) -> List[RagieSearchResult]:
        """Process and score results for the specific agent type"""
        
        processed_results = []
        
        for result in raw_results:
            # Extract basic information
            content = result.get("content", "")
            source = result.get("source", "unknown")
            base_score = result.get("score", 0.0)
            
            # Calculate agent-specific relevance
            agent_relevance = self._calculate_agent_relevance(
                content, 
                agent_type, 
                classification, 
                original_query
            )
            
            # Determine document type
            document_type = self._classify_document_type(content, source)
            
            processed_results.append(RagieSearchResult(
                content=content,
                source=source,
                score=base_score,
                agent_relevance=agent_relevance,
                document_type=document_type,
                metadata=result.get("metadata", {})
            ))
        
        # Sort by agent relevance score
        processed_results.sort(key=lambda x: x.agent_relevance, reverse=True)
        
        return processed_results[:self.max_results]
    
    def _calculate_agent_relevance(
        self,
        content: str,
        agent_type: AgentType,
        classification: Optional[QueryClassification],
        query: str
    ) -> float:
        """Calculate relevance score specific to the agent type"""
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Base relevance from query keywords
        base_relevance = 0.5
        
        # Query keyword matching
        query_words = query_lower.split()
        content_words = content_lower.split()
        keyword_matches = sum(1 for word in query_words if word in content_words)
        base_relevance += (keyword_matches / len(query_words)) * 0.3
        
        # Agent-specific scoring
        if agent_type == AgentType.EQUIPMENT:
            equipment_keywords = ["taylor", "vulcan", "hobart", "traulsen", "machine", "equipment", "repair", "maintenance", "error", "diagnostic"]
            equipment_score = sum(1 for kw in equipment_keywords if kw in content_lower) * 0.1
            base_relevance += equipment_score
            
        elif agent_type == AgentType.SAFETY:
            safety_keywords = ["safety", "emergency", "fire", "burn", "cut", "injury", "accident", "hazard", "dangerous", "caution"]
            safety_score = sum(1 for kw in safety_keywords if kw in content_lower) * 0.15
            base_relevance += safety_score
            
        elif agent_type == AgentType.OPERATIONS:
            ops_keywords = ["procedure", "process", "operation", "workflow", "checklist", "opening", "closing", "shift", "quality"]
            ops_score = sum(1 for kw in ops_keywords if kw in content_lower) * 0.1
            base_relevance += ops_score
            
        elif agent_type == AgentType.TRAINING:
            training_keywords = ["training", "certification", "learning", "skill", "competency", "onboarding", "assessment"]
            training_score = sum(1 for kw in training_keywords if kw in content_lower) * 0.1
            base_relevance += training_score
        
        # Urgency boost
        if classification and classification.urgency == "high":
            urgency_keywords = ["immediate", "urgent", "emergency", "critical"]
            if any(kw in content_lower for kw in urgency_keywords):
                base_relevance *= 1.5
        
        return min(base_relevance, 1.0)  # Cap at 1.0
    
    def _classify_document_type(self, content: str, source: str) -> str:
        """Classify the type of document based on content and source"""
        
        content_lower = content.lower()
        source_lower = source.lower()
        
        # Check source first
        if "manual" in source_lower:
            return "manual"
        elif "safety" in source_lower:
            return "safety"
        elif "training" in source_lower:
            return "training"
        elif "procedure" in source_lower:
            return "procedure"
        
        # Check content patterns
        if any(kw in content_lower for kw in ["step 1", "step 2", "procedure", "instructions"]):
            return "procedure"
        elif any(kw in content_lower for kw in ["warning", "caution", "danger", "safety"]):
            return "safety"
        elif any(kw in content_lower for kw in ["model", "specifications", "parts", "manual"]):
            return "manual"
        elif any(kw in content_lower for kw in ["training", "certification", "learning"]):
            return "training"
        
        return "general"
    
    def _generate_cache_key(
        self,
        query: str,
        agent_type: AgentType,
        classification: Optional[QueryClassification]
    ) -> str:
        """Generate cache key for the search"""
        
        key_components = [
            query.lower().strip(),
            agent_type.value,
            classification.urgency if classification else "normal"
        ]
        
        return ":".join(key_components)
    
    def _update_performance_metrics(self, response_time: float) -> None:
        """Update performance tracking metrics"""
        
        if self.query_count == 1:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                (self.average_response_time * (self.query_count - 1) + response_time) / 
                self.query_count
            )
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the Ragie service"""
        
        try:
            # Test API connectivity
            if self._client:
                response = await self._client.get("/health")
                api_healthy = response.status_code == 200
            else:
                api_healthy = False
                
            return {
                "status": "healthy" if api_healthy else "degraded",
                "api_connectivity": api_healthy,
                "initialized": self._initialized,
                "query_count": self.query_count,
                "cache_hits": self.cache_hits,
                "cache_hit_rate": self.cache_hits / max(self.query_count, 1),
                "average_response_time": self.average_response_time
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "initialized": self._initialized
            }
    
    async def clear_cache(self) -> None:
        """Clear the search cache"""
        self._cache.clear()
        self.logger.info("Ragie service cache cleared")
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self._client:
            await self._client.aclose()
        self._initialized = False
    
    @classmethod
    async def create(cls, **kwargs) -> 'EnhancedRagieService':
        """Factory method to create and initialize the service"""
        service = cls(**kwargs)
        await service.initialize()
        return service


# Factory function
async def create_enhanced_ragie_service(**kwargs) -> EnhancedRagieService:
    """Create and initialize an enhanced Ragie service"""
    return await EnhancedRagieService.create(**kwargs)


if __name__ == "__main__":
    async def test_enhanced_ragie():
        """Test the enhanced Ragie service"""
        service = await create_enhanced_ragie_service()
        
        test_queries = [
            ("Taylor machine error E01", AgentType.EQUIPMENT),
            ("Employee burn emergency", AgentType.SAFETY),
            ("Opening procedure checklist", AgentType.OPERATIONS),
            ("New employee training", AgentType.TRAINING)
        ]
        
        for query, agent_type in test_queries:
            print(f"\nTesting: {query} with {agent_type.value} agent")
            result = await service.search_for_agent(query, agent_type)
            print(f"Results: {result.total_results}")
            for i, res in enumerate(result.results[:3]):
                print(f"  {i+1}. {res.source} (score: {res.agent_relevance:.2f})")
    
    asyncio.run(test_enhanced_ragie())