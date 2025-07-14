"""
Enhanced Citation Service - Bridge between existing visual citations and enhanced models
===================================================================================

Integrates the new enhanced visual citation models with the existing:
- MultiModalCitationService 
- Ragie visual citation extraction
- PDF processing and page references
- Neo4j visual storage

This service maintains backward compatibility while adding enhanced capabilities.

Author: Generated with Memex (https://memex.tech)
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import time

logger = logging.getLogger(__name__)

# Import enhanced models
try:
    from models.enhanced_qsr_models import (
        EnhancedVisualCitation, VisualCitationCollection,
        VisualCitationType, VisualCitationSource, EquipmentContext,
        AgentType
    )
    ENHANCED_MODELS_AVAILABLE = True
except ImportError:
    ENHANCED_MODELS_AVAILABLE = False
    logger.warning("Enhanced models not available")

class EnhancedCitationService:
    """Service to bridge existing visual citations with enhanced models"""
    
    def __init__(self):
        self.citation_cache = {}
        self.performance_metrics = {
            "citations_enhanced": 0,
            "cache_hits": 0,
            "processing_time_total": 0.0
        }
        
    async def enhance_legacy_citations(
        self,
        legacy_citations: List[Dict[str, Any]],
        contributing_agent: AgentType,
        equipment_context: Optional[str] = None
    ) -> List['EnhancedVisualCitation']:
        """
        Convert legacy visual citations to enhanced format
        
        Args:
            legacy_citations: Existing visual citations from Ragie/Graph-RAG
            contributing_agent: Agent that generated the citations
            equipment_context: Current equipment context if available
            
        Returns:
            List of enhanced visual citations
        """
        if not ENHANCED_MODELS_AVAILABLE:
            logger.warning("Enhanced models not available, returning empty list")
            return []
            
        start_time = time.time()
        enhanced_citations = []
        
        for i, citation in enumerate(legacy_citations):
            try:
                enhanced_citation = await self._convert_legacy_citation(
                    citation, contributing_agent, equipment_context, i
                )
                if enhanced_citation:
                    enhanced_citations.append(enhanced_citation)
                    
            except Exception as e:
                logger.error(f"Failed to enhance citation {i}: {e}")
                continue
        
        # Update performance metrics
        processing_time = time.time() - start_time
        self.performance_metrics["citations_enhanced"] += len(enhanced_citations)
        self.performance_metrics["processing_time_total"] += processing_time
        
        logger.info(f"Enhanced {len(enhanced_citations)} citations in {processing_time:.3f}s")
        return enhanced_citations
    
    async def _convert_legacy_citation(
        self,
        citation: Dict[str, Any],
        contributing_agent: AgentType,
        equipment_context: Optional[str],
        index: int
    ) -> Optional['EnhancedVisualCitation']:
        """Convert individual legacy citation to enhanced format"""
        
        try:
            # Extract citation information
            citation_id = citation.get('citation_id', f"{contributing_agent.value}_{index}")
            citation_type = self._map_legacy_type_to_enhanced(citation.get('type', 'image'))
            source = self._determine_citation_source(citation)
            
            # Determine equipment context
            equipment_list = []
            if equipment_context:
                equipment_list.append(equipment_context)
            if citation.get('equipment_type'):
                equipment_list.append(citation['equipment_type'])
            
            # Map safety level based on agent and content
            safety_level = self._determine_safety_level(citation, contributing_agent)
            
            # Create enhanced citation
            enhanced_citation = EnhancedVisualCitation(
                citation_id=citation_id,
                type=citation_type,
                source=source,
                title=citation.get('source', citation.get('title', 'Visual Reference')),
                description=citation.get('description', citation.get('caption', '')),
                
                # Content references
                content_url=citation.get('url', citation.get('content_url')),
                pdf_url=citation.get('pdf_url'),
                page_number=citation.get('page', citation.get('page_number')),
                section=citation.get('section'),
                
                # Agent context
                contributing_agent=contributing_agent,
                agent_confidence=citation.get('confidence', citation.get('relevance_score', 0.8)),
                relevance_score=citation.get('relevance_score', citation.get('confidence', 0.8)),
                
                # QSR domain context
                equipment_context=equipment_list,
                safety_level=safety_level,
                maintenance_frequency=citation.get('maintenance_frequency'),
                
                # Visual metadata from existing citation
                visual_metadata={
                    "has_content": citation.get('has_content', False),
                    "enhanced_extraction": citation.get('enhanced_extraction', False),
                    "original_metadata": citation.get('metadata', {})
                }
            )
            
            return enhanced_citation
            
        except Exception as e:
            logger.error(f"Failed to convert citation: {e}")
            return None
    
    def _map_legacy_type_to_enhanced(self, legacy_type: str) -> VisualCitationType:
        """Map legacy citation types to enhanced types"""
        mapping = {
            'image': VisualCitationType.IMAGE,
            'diagram': VisualCitationType.DIAGRAM,
            'video': VisualCitationType.VIDEO,
            'pdf_page': VisualCitationType.PDF_PAGE,
            'equipment_schematic': VisualCitationType.EQUIPMENT_SCHEMATIC,
            'procedure_flowchart': VisualCitationType.PROCEDURE_FLOWCHART,
            'safety_poster': VisualCitationType.SAFETY_POSTER,
            'maintenance_chart': VisualCitationType.MAINTENANCE_CHART,
            'temperature_chart': VisualCitationType.TEMPERATURE_CHART,
            'cleaning_guide': VisualCitationType.CLEANING_GUIDE
        }
        
        return mapping.get(legacy_type.lower(), VisualCitationType.IMAGE)
    
    def _determine_citation_source(self, citation: Dict[str, Any]) -> VisualCitationSource:
        """Determine the source of the citation"""
        
        # Check for enhanced extraction flag
        if citation.get('enhanced_extraction'):
            return VisualCitationSource.RAGIE_EXTRACTION
        
        # Check for Graph-RAG indicators
        if citation.get('equipment_type') or citation.get('procedure'):
            return VisualCitationSource.GRAPH_RAG_ENTITY
        
        # Check for PDF indicators
        if citation.get('pdf_url') or citation.get('page'):
            return VisualCitationSource.PDF_EXTRACTION
        
        # Check for manual reference indicators
        if citation.get('source') and 'manual' in citation['source'].lower():
            return VisualCitationSource.MANUAL_REFERENCE
        
        # Default to agent generated
        return VisualCitationSource.AGENT_GENERATED
    
    def _determine_safety_level(self, citation: Dict[str, Any], agent: AgentType) -> str:
        """Determine safety level based on citation content and agent"""
        
        # Safety agent citations are high priority
        if agent == AgentType.SAFETY:
            return "high"
        
        # Check for safety keywords in description
        description = (citation.get('description', '') + ' ' + citation.get('title', '')).lower()
        
        critical_keywords = ['emergency', 'danger', 'hazard', 'toxic', 'burn', 'fire']
        high_keywords = ['safety', 'temperature', 'contamination', 'ppe', 'protective']
        medium_keywords = ['caution', 'warning', 'procedure', 'protocol']
        
        if any(keyword in description for keyword in critical_keywords):
            return "critical"
        elif any(keyword in description for keyword in high_keywords):
            return "high"
        elif any(keyword in description for keyword in medium_keywords):
            return "medium"
        else:
            return "low"
    
    async def create_citation_collection(
        self,
        enhanced_citations: List['EnhancedVisualCitation'],
        coordination_strategy: 'AgentCoordinationStrategy' = None
    ) -> 'VisualCitationCollection':
        """Create a visual citation collection from enhanced citations"""
        
        if not ENHANCED_MODELS_AVAILABLE:
            return None
        
        # Import coordination strategy
        try:
            from voice_agent import AgentCoordinationStrategy
            if coordination_strategy is None:
                coordination_strategy = AgentCoordinationStrategy.SINGLE_AGENT
        except ImportError:
            coordination_strategy = "single_agent"
        
        collection = VisualCitationCollection(
            citations=enhanced_citations,
            coordination_strategy=coordination_strategy
        )
        
        # Determine primary citation (highest relevance score)
        if enhanced_citations:
            primary = max(enhanced_citations, key=lambda c: c.relevance_score)
            collection.primary_citation = primary.citation_id
        
        # Set collection-level metadata
        all_equipment = []
        safety_critical = False
        
        for citation in enhanced_citations:
            all_equipment.extend(citation.equipment_context)
            if citation.safety_level in ["high", "critical"]:
                safety_critical = True
        
        collection.equipment_focus = list(set(all_equipment))
        collection.safety_critical = safety_critical
        
        return collection
    
    async def enhance_ragie_citations(
        self,
        ragie_results: List[Any],
        contributing_agent: AgentType
    ) -> List['EnhancedVisualCitation']:
        """
        Enhance citations from Ragie search results
        
        Args:
            ragie_results: Results from Ragie search
            contributing_agent: Agent requesting the enhancement
            
        Returns:
            Enhanced visual citations
        """
        enhanced_citations = []
        
        for result in ragie_results:
            try:
                # Extract metadata from Ragie result
                metadata = getattr(result, 'metadata', {})
                
                # Create legacy citation format first
                legacy_citation = {
                    'citation_id': f"ragie_{result.document_id}_{result.chunk_id}",
                    'type': metadata.get('file_type', 'image'),
                    'source': metadata.get('source', metadata.get('original_filename', 'Ragie Source')),
                    'description': result.text[:200] + "..." if len(result.text) > 200 else result.text,
                    'confidence': result.score,
                    'page': metadata.get('page_number'),
                    'equipment_type': metadata.get('equipment_type'),
                    'enhanced_extraction': True,
                    'metadata': metadata,
                    'has_content': metadata.get('has_images', False)
                }
                
                # Convert to enhanced format
                enhanced = await self._convert_legacy_citation(
                    legacy_citation, contributing_agent, metadata.get('equipment_type'), len(enhanced_citations)
                )
                
                if enhanced:
                    enhanced_citations.append(enhanced)
                    
            except Exception as e:
                logger.error(f"Failed to enhance Ragie citation: {e}")
                continue
        
        return enhanced_citations
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        metrics = self.performance_metrics.copy()
        
        if metrics["citations_enhanced"] > 0:
            metrics["average_processing_time"] = metrics["processing_time_total"] / metrics["citations_enhanced"]
        else:
            metrics["average_processing_time"] = 0.0
            
        return metrics
    
    async def cache_citation(self, citation_id: str, enhanced_citation: 'EnhancedVisualCitation'):
        """Cache enhanced citation for performance"""
        self.citation_cache[citation_id] = enhanced_citation
        
        # Limit cache size
        if len(self.citation_cache) > 1000:
            # Remove oldest 20% of entries
            sorted_items = sorted(
                self.citation_cache.items(),
                key=lambda x: x[1].last_accessed or time.time()
            )
            for key, _ in sorted_items[:200]:
                del self.citation_cache[key]
    
    async def get_cached_citation(self, citation_id: str) -> Optional['EnhancedVisualCitation']:
        """Get cached enhanced citation"""
        citation = self.citation_cache.get(citation_id)
        if citation:
            self.performance_metrics["cache_hits"] += 1
            citation.increment_access()
        return citation

# Global service instance
enhanced_citation_service = EnhancedCitationService()

# ===============================================================================
# INTEGRATION FUNCTIONS FOR EXISTING CODEBASE
# ===============================================================================

async def enhance_existing_visual_citations(
    visual_citations: List[Dict[str, Any]],
    agent_type: AgentType = None,
    equipment_context: str = None
) -> Optional[List['EnhancedVisualCitation']]:
    """
    Main integration function to enhance existing visual citations
    
    This function can be called from main_clean.py to enhance the visual citations
    that are already being generated by the existing system.
    
    Args:
        visual_citations: Existing visual citations from main_clean.py
        agent_type: Agent that generated the citations
        equipment_context: Current equipment context
        
    Returns:
        Enhanced visual citations or None if enhancement fails
    """
    if not visual_citations or not ENHANCED_MODELS_AVAILABLE:
        return None
    
    if agent_type is None:
        # Import AgentType if not provided
        try:
            from voice_agent import AgentType
            agent_type = AgentType.GENERAL
        except ImportError:
            return None
    
    try:
        enhanced = await enhanced_citation_service.enhance_legacy_citations(
            visual_citations, agent_type, equipment_context
        )
        return enhanced
    except Exception as e:
        logger.error(f"Failed to enhance visual citations: {e}")
        return None

async def create_enhanced_citation_collection(
    enhanced_citations: List['EnhancedVisualCitation']
) -> Optional['VisualCitationCollection']:
    """Create a citation collection from enhanced citations"""
    if not enhanced_citations or not ENHANCED_MODELS_AVAILABLE:
        return None
        
    try:
        collection = await enhanced_citation_service.create_citation_collection(enhanced_citations)
        return collection
    except Exception as e:
        logger.error(f"Failed to create citation collection: {e}")
        return None