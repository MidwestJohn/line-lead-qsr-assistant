#!/usr/bin/env python3
"""
PydanticAI Tools powered by Ragie for Universal Use
==================================================

Create PydanticAI Tools that use Ragie knowledge for both text and voice interactions.
These tools provide intelligent QSR assistance powered by Ragie's document retrieval.

Key Features:
- Context-aware Ragie queries
- Multi-modal content extraction
- Equipment-specific retrieval
- Safety priority handling
- Visual citations integration
- Universal text/voice compatibility

CLEAN IMPLEMENTATION: Uses ONLY Ragie + PydanticAI, no Graph-RAG dependencies.

Author: Generated with Memex (https://memex.tech)
"""

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal
from enum import Enum
import logging
import asyncio
import time
from datetime import datetime
import hashlib
import json

# Import Ragie service
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.ragie_service_clean import clean_ragie_service, RagieSearchResult
    from services.multimodal_citation_service import MultiModalCitationService
    RAGIE_AVAILABLE = True
except ImportError:
    RAGIE_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===============================================================================
# TOOL RESULT MODELS
# ===============================================================================

class ToolExecutionContext(BaseModel):
    """Context for tool execution"""
    query: str
    user_intent: str = "general"
    interaction_mode: Literal["text", "voice", "hybrid"] = "text"
    equipment_context: Optional[str] = None
    safety_priority: bool = False
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)

class RagieToolResult(BaseModel):
    """Base result from Ragie-powered tools"""
    success: bool
    content: str
    confidence: float
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float
    tool_name: str
    
    # Enhanced features
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    equipment_context: Optional[Dict[str, Any]] = None
    suggested_actions: List[str] = Field(default_factory=list)

class RagieKnowledgeResult(RagieToolResult):
    """Result from RagieKnowledgeTool"""
    knowledge_type: str = "general"
    relevance_score: float = 0.0
    context_enhanced: bool = False

class RagieVisualResult(RagieToolResult):
    """Result from RagieVisualTool"""
    visual_count: int = 0
    image_urls: List[str] = Field(default_factory=list)
    diagram_references: List[str] = Field(default_factory=list)
    page_references: List[int] = Field(default_factory=list)

class RagieEquipmentResult(RagieToolResult):
    """Result from RagieEquipmentTool"""
    equipment_name: str
    equipment_type: str = "unknown"
    maintenance_required: bool = False
    safety_level: Literal["low", "medium", "high", "critical"] = "medium"
    troubleshooting_steps: List[str] = Field(default_factory=list)

class RagieProcedureResult(RagieToolResult):
    """Result from RagieProcedureTool"""
    procedure_name: str
    step_count: int = 0
    estimated_time: Optional[str] = None
    difficulty_level: Literal["easy", "medium", "hard"] = "medium"
    required_tools: List[str] = Field(default_factory=list)
    procedure_steps: List[Dict[str, Any]] = Field(default_factory=list)

class RagieSafetyResult(RagieToolResult):
    """Result from RagieSafetyTool"""
    safety_level: Literal["low", "medium", "high", "critical"] = "medium"
    risk_factors: List[str] = Field(default_factory=list)
    emergency_procedures: List[str] = Field(default_factory=list)
    compliance_notes: List[str] = Field(default_factory=list)
    immediate_actions: List[str] = Field(default_factory=list)

# ===============================================================================
# BASE RAGIE TOOL CLASS
# ===============================================================================

class BaseRagieTool:
    """Base class for Ragie-powered tools"""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.logger = logging.getLogger(f"{__name__}.{tool_name}")
        self.ragie_service = clean_ragie_service if RAGIE_AVAILABLE else None
        self.citation_service = MultiModalCitationService() if RAGIE_AVAILABLE else None
        
        # Performance tracking
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.success_count = 0
        
    def is_available(self) -> bool:
        """Check if tool is available"""
        return RAGIE_AVAILABLE and self.ragie_service and self.ragie_service.is_available()
    
    async def _query_ragie(self, query: str, context: ToolExecutionContext, limit: int = 5) -> List[RagieSearchResult]:
        """Query Ragie with context enhancement"""
        if not self.is_available():
            return []
        
        try:
            # Enhance query with context
            enhanced_query = self._enhance_query_with_context(query, context)
            
            # Query Ragie
            results = await self.ragie_service.search(enhanced_query, limit=limit)
            
            self.logger.info(f"📊 Ragie query: '{query}' → {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Ragie query failed: {e}")
            return []
    
    def _enhance_query_with_context(self, query: str, context: ToolExecutionContext) -> str:
        """Enhance query with context information"""
        
        query_parts = [query]
        
        # Add tool-specific context
        if hasattr(self, 'tool_context_keywords'):
            query_parts.extend(self.tool_context_keywords)
        
        # Add equipment context
        if context.equipment_context:
            query_parts.append(f"equipment: {context.equipment_context}")
        
        # Add safety context
        if context.safety_priority:
            query_parts.append("safety critical emergency")
        
        # Add interaction mode context
        if context.interaction_mode == "voice":
            query_parts.append("voice instructions spoken")
        
        return " ".join(query_parts)
    
    async def _extract_visual_citations(self, query: str, results: List[RagieSearchResult]) -> List[Dict[str, Any]]:
        """Extract visual citations from Ragie results"""
        if not self.citation_service:
            return []
        
        try:
            # Combine result text for analysis
            text_to_analyze = f"{query} " + " ".join([r.text for r in results[:3]])
            
            # Extract visual references
            visual_refs = self.citation_service._detect_references_in_text(text_to_analyze)
            
            citations = []
            for ref in visual_refs[:5]:  # Limit to 5 citations
                citation = {
                    'citation_id': hashlib.md5(f"{ref['type']}_{ref['matched_text']}".encode()).hexdigest()[:8],
                    'type': self._map_citation_type(ref['type']),
                    'source': 'QSR Manual',
                    'title': f"{ref['type'].title()}: {ref['matched_text']}",
                    'description': f"Visual reference for {ref['matched_text']}",
                    'confidence': 0.8,
                    'context': ref.get('context', '')
                }
                citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Visual citation extraction failed: {e}")
            return []
    
    def _map_citation_type(self, ref_type: str) -> str:
        """Map reference types to valid citation types"""
        type_mapping = {
            'safety': 'diagram',
            'equipment': 'diagram',
            'procedure': 'flowchart',
            'steps': 'flowchart',
            'temperature': 'table',
            'measurement': 'table',
            'visual': 'image',
            'picture': 'image',
            'photo': 'image'
        }
        return type_mapping.get(ref_type, 'diagram')
    
    async def _analyze_safety_level(self, query: str, content: str) -> tuple[str, List[str]]:
        """Analyze safety level and generate warnings"""
        
        critical_keywords = ['emergency', 'fire', 'burn', 'toxic', 'hazard', 'danger']
        high_keywords = ['safety', 'hot', 'electrical', 'chemical', 'caution']
        medium_keywords = ['warning', 'attention', 'careful', 'proper']
        
        combined_text = f"{query} {content}".lower()
        
        warnings = []
        
        if any(keyword in combined_text for keyword in critical_keywords):
            safety_level = "critical"
            warnings.append("⚠️ CRITICAL SAFETY: Follow all safety protocols immediately")
        elif any(keyword in combined_text for keyword in high_keywords):
            safety_level = "high"
            warnings.append("⚠️ HIGH SAFETY: Exercise caution and follow safety procedures")
        elif any(keyword in combined_text for keyword in medium_keywords):
            safety_level = "medium"
            warnings.append("⚠️ SAFETY: Follow standard safety procedures")
        else:
            safety_level = "low"
        
        return safety_level, warnings
    
    def _update_performance_metrics(self, execution_time: float, success: bool):
        """Update performance metrics"""
        self.execution_count += 1
        self.total_execution_time += execution_time
        if success:
            self.success_count += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get tool performance metrics"""
        return {
            'tool_name': self.tool_name,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'success_rate': self.success_count / max(self.execution_count, 1),
            'avg_execution_time_ms': self.total_execution_time / max(self.execution_count, 1),
            'total_execution_time_ms': self.total_execution_time,
            'available': self.is_available()
        }

# ===============================================================================
# RAGIE KNOWLEDGE TOOL
# ===============================================================================

class RagieKnowledgeTool(BaseRagieTool):
    """
    General knowledge tool powered by Ragie
    
    Provides context-aware search across all QSR documentation
    with multi-modal content extraction and intelligent routing.
    """
    
    def __init__(self):
        super().__init__("RagieKnowledgeTool")
        self.tool_context_keywords = [
            "QSR restaurant operations knowledge information"
        ]
    
    async def search_knowledge(self, query: str, context: ToolExecutionContext) -> RagieKnowledgeResult:
        """
        Search for general knowledge using Ragie
        
        Args:
            query: Search query
            context: Execution context
            
        Returns:
            RagieKnowledgeResult with knowledge and metadata
        """
        
        start_time = time.time()
        
        try:
            if not self.is_available():
                return RagieKnowledgeResult(
                    success=False,
                    content="Knowledge search not available - Ragie service unavailable",
                    confidence=0.0,
                    execution_time_ms=0.0,
                    tool_name=self.tool_name
                )
            
            # Query Ragie
            results = await self._query_ragie(query, context, limit=8)
            
            if not results:
                return RagieKnowledgeResult(
                    success=False,
                    content=f"No relevant knowledge found for: {query}",
                    confidence=0.3,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    tool_name=self.tool_name
                )
            
            # Process results
            primary_result = results[0]
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(query, results)
            
            # Analyze safety
            safety_level, safety_warnings = await self._analyze_safety_level(query, primary_result.text)
            
            # Format sources
            sources = []
            for result in results:
                sources.append({
                    'content': result.text,
                    'score': result.score,
                    'source': result.metadata.get('source', 'QSR Manual'),
                    'document_id': result.document_id,
                    'metadata': result.metadata
                })
            
            # Determine knowledge type
            knowledge_type = self._determine_knowledge_type(query, primary_result.text)
            
            # Calculate relevance score
            relevance_score = min(primary_result.score * 1.2, 1.0)
            
            # Generate suggested actions
            suggested_actions = self._generate_suggested_actions(query, primary_result.text, knowledge_type)
            
            execution_time = (time.time() - start_time) * 1000
            
            result = RagieKnowledgeResult(
                success=True,
                content=primary_result.text,
                confidence=min(primary_result.score, 0.95),
                sources=sources,
                metadata={
                    'query': query,
                    'total_results': len(results),
                    'knowledge_type': knowledge_type,
                    'context_enhanced': len(context.conversation_history) > 0
                },
                execution_time_ms=execution_time,
                tool_name=self.tool_name,
                visual_citations=visual_citations,
                safety_warnings=safety_warnings,
                suggested_actions=suggested_actions,
                knowledge_type=knowledge_type,
                relevance_score=relevance_score,
                context_enhanced=len(context.conversation_history) > 0
            )
            
            self._update_performance_metrics(execution_time, True)
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Knowledge search failed: {e}")
            
            self._update_performance_metrics(execution_time, False)
            return RagieKnowledgeResult(
                success=False,
                content=f"Knowledge search encountered an error: {str(e)}",
                confidence=0.2,
                execution_time_ms=execution_time,
                tool_name=self.tool_name
            )
    
    def _determine_knowledge_type(self, query: str, content: str) -> str:
        """Determine the type of knowledge based on query and content"""
        
        combined_text = f"{query} {content}".lower()
        
        if any(keyword in combined_text for keyword in ['equipment', 'machine', 'fryer', 'grill', 'oven']):
            return "equipment"
        elif any(keyword in combined_text for keyword in ['procedure', 'steps', 'how to', 'process']):
            return "procedure"
        elif any(keyword in combined_text for keyword in ['safety', 'emergency', 'hazard', 'danger']):
            return "safety"
        elif any(keyword in combined_text for keyword in ['clean', 'maintenance', 'sanitize']):
            return "maintenance"
        elif any(keyword in combined_text for keyword in ['recipe', 'ingredients', 'cooking']):
            return "recipe"
        else:
            return "general"
    
    def _generate_suggested_actions(self, query: str, content: str, knowledge_type: str) -> List[str]:
        """Generate suggested actions based on knowledge type"""
        
        actions = []
        
        if knowledge_type == "equipment":
            actions.extend([
                "Check equipment manual for detailed specifications",
                "Verify proper maintenance schedule",
                "Ensure safety protocols are followed"
            ])
        elif knowledge_type == "procedure":
            actions.extend([
                "Review step-by-step instructions",
                "Gather required tools and materials",
                "Follow safety guidelines throughout"
            ])
        elif knowledge_type == "safety":
            actions.extend([
                "Review emergency procedures",
                "Ensure all safety equipment is available",
                "Train staff on safety protocols"
            ])
        elif knowledge_type == "maintenance":
            actions.extend([
                "Schedule regular maintenance",
                "Document maintenance activities",
                "Use proper cleaning supplies"
            ])
        
        return actions

# ===============================================================================
# RAGIE VISUAL TOOL
# ===============================================================================

class RagieVisualTool(BaseRagieTool):
    """
    Visual content extraction tool powered by Ragie
    
    Extracts visual citations, equipment images, diagrams, and PDF references
    from Ragie search results with coordination from MultiModalCitationService.
    """
    
    def __init__(self):
        super().__init__("RagieVisualTool")
        self.tool_context_keywords = [
            "visual image diagram picture photo illustration"
        ]
    
    async def extract_visual_content(self, query: str, context: ToolExecutionContext) -> RagieVisualResult:
        """
        Extract visual content and citations from Ragie
        
        Args:
            query: Search query for visual content
            context: Execution context
            
        Returns:
            RagieVisualResult with visual content and citations
        """
        
        start_time = time.time()
        
        try:
            if not self.is_available():
                return RagieVisualResult(
                    success=False,
                    content="Visual content extraction not available - Ragie service unavailable",
                    confidence=0.0,
                    execution_time_ms=0.0,
                    tool_name=self.tool_name
                )
            
            # Enhance query for visual content
            visual_query = self._enhance_visual_query(query, context)
            
            # Query Ragie
            results = await self._query_ragie(visual_query, context, limit=10)
            
            if not results:
                return RagieVisualResult(
                    success=False,
                    content=f"No visual content found for: {query}",
                    confidence=0.3,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    tool_name=self.tool_name
                )
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(query, results)
            
            # Process visual content
            image_urls = []
            diagram_references = []
            page_references = []
            
            for result in results:
                # Extract image URLs from metadata
                if result.images:
                    for image in result.images:
                        if isinstance(image, dict) and 'url' in image:
                            image_urls.append(image['url'])
                
                # Extract diagram references
                if any(keyword in result.text.lower() for keyword in ['diagram', 'figure', 'illustration']):
                    diagram_references.append(result.text[:100] + "...")
                
                # Extract page references
                if 'page_number' in result.metadata:
                    page_references.append(result.metadata['page_number'])
            
            # Format visual content summary
            visual_content = self._format_visual_content_summary(results, visual_citations)
            
            # Analyze safety for visual content
            safety_level, safety_warnings = await self._analyze_safety_level(query, visual_content)
            
            # Generate suggested actions
            suggested_actions = self._generate_visual_actions(query, visual_citations)
            
            execution_time = (time.time() - start_time) * 1000
            
            result = RagieVisualResult(
                success=True,
                content=visual_content,
                confidence=0.85 if visual_citations else 0.6,
                sources=[{
                    'content': r.text,
                    'score': r.score,
                    'source': r.metadata.get('source', 'QSR Manual'),
                    'document_id': r.document_id,
                    'metadata': r.metadata
                } for r in results],
                metadata={
                    'query': query,
                    'visual_query': visual_query,
                    'total_results': len(results),
                    'visual_content_found': len(visual_citations) > 0
                },
                execution_time_ms=execution_time,
                tool_name=self.tool_name,
                visual_citations=visual_citations,
                safety_warnings=safety_warnings,
                suggested_actions=suggested_actions,
                visual_count=len(visual_citations),
                image_urls=image_urls,
                diagram_references=diagram_references,
                page_references=list(set(page_references))  # Remove duplicates
            )
            
            self._update_performance_metrics(execution_time, True)
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Visual content extraction failed: {e}")
            
            self._update_performance_metrics(execution_time, False)
            return RagieVisualResult(
                success=False,
                content=f"Visual content extraction encountered an error: {str(e)}",
                confidence=0.2,
                execution_time_ms=execution_time,
                tool_name=self.tool_name
            )
    
    def _enhance_visual_query(self, query: str, context: ToolExecutionContext) -> str:
        """Enhance query specifically for visual content"""
        
        visual_keywords = [
            "image", "picture", "photo", "diagram", "illustration", 
            "figure", "chart", "visual", "shown", "display", "example"
        ]
        
        query_parts = [query]
        
        # Add visual-specific keywords
        if not any(keyword in query.lower() for keyword in visual_keywords):
            query_parts.extend(["visual", "diagram", "illustration"])
        
        # Add equipment-specific visual terms
        if context.equipment_context:
            query_parts.extend([f"{context.equipment_context} diagram", "equipment visual"])
        
        return " ".join(query_parts)
    
    def _format_visual_content_summary(self, results: List[RagieSearchResult], visual_citations: List[Dict[str, Any]]) -> str:
        """Format visual content summary"""
        
        if not visual_citations:
            return f"Found {len(results)} related documents, but no specific visual content was identified."
        
        summary_parts = [
            f"Found {len(visual_citations)} visual references:"
        ]
        
        for citation in visual_citations[:3]:  # Limit to 3 for summary
            summary_parts.append(f"• {citation['title']}: {citation['description']}")
        
        if len(visual_citations) > 3:
            summary_parts.append(f"• ... and {len(visual_citations) - 3} more visual references")
        
        return "\n".join(summary_parts)
    
    def _generate_visual_actions(self, query: str, visual_citations: List[Dict[str, Any]]) -> List[str]:
        """Generate suggested actions for visual content"""
        
        actions = []
        
        if visual_citations:
            actions.extend([
                "Review visual references for detailed illustrations",
                "Cross-reference with equipment manuals",
                "Use visual guides for step-by-step procedures"
            ])
        
        if any('diagram' in citation.get('type', '') for citation in visual_citations):
            actions.append("Study diagrams for equipment layout and connections")
        
        if any('image' in citation.get('type', '') for citation in visual_citations):
            actions.append("Examine images for proper technique and appearance")
        
        return actions

# ===============================================================================
# RAGIE EQUIPMENT TOOL
# ===============================================================================

class RagieEquipmentTool(BaseRagieTool):
    """
    Equipment-specific tool powered by Ragie
    
    Provides equipment documentation, troubleshooting guides,
    maintenance procedures, and safety information from Ragie.
    """
    
    def __init__(self):
        super().__init__("RagieEquipmentTool")
        self.tool_context_keywords = [
            "equipment machine fryer grill oven troubleshooting repair maintenance"
        ]
    
    async def get_equipment_info(self, equipment_name: str, context: ToolExecutionContext) -> RagieEquipmentResult:
        """
        Get comprehensive equipment information from Ragie
        
        Args:
            equipment_name: Name of the equipment
            context: Execution context
            
        Returns:
            RagieEquipmentResult with equipment information
        """
        
        start_time = time.time()
        
        try:
            if not self.is_available():
                return RagieEquipmentResult(
                    success=False,
                    content="Equipment information not available - Ragie service unavailable",
                    confidence=0.0,
                    execution_time_ms=0.0,
                    tool_name=self.tool_name,
                    equipment_name=equipment_name
                )
            
            # Enhance query for equipment
            equipment_query = self._enhance_equipment_query(equipment_name, context)
            
            # Query Ragie
            results = await self._query_ragie(equipment_query, context, limit=10)
            
            if not results:
                return RagieEquipmentResult(
                    success=False,
                    content=f"No equipment information found for: {equipment_name}",
                    confidence=0.3,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    tool_name=self.tool_name,
                    equipment_name=equipment_name
                )
            
            # Process equipment information
            primary_result = results[0]
            
            # Determine equipment type
            equipment_type = self._determine_equipment_type(equipment_name, primary_result.text)
            
            # Analyze maintenance requirements
            maintenance_required = self._analyze_maintenance_requirements(primary_result.text)
            
            # Determine safety level
            safety_level, safety_warnings = await self._analyze_safety_level(equipment_query, primary_result.text)
            
            # Extract troubleshooting steps
            troubleshooting_steps = self._extract_troubleshooting_steps(primary_result.text)
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(equipment_query, results)
            
            # Generate equipment context
            equipment_context = {
                'equipment_name': equipment_name,
                'equipment_type': equipment_type,
                'maintenance_schedule': 'Regular maintenance required' if maintenance_required else 'Standard maintenance',
                'safety_considerations': safety_warnings,
                'documentation_available': len(results) > 1
            }
            
            # Generate suggested actions
            suggested_actions = self._generate_equipment_actions(equipment_name, equipment_type, maintenance_required)
            
            execution_time = (time.time() - start_time) * 1000
            
            result = RagieEquipmentResult(
                success=True,
                content=primary_result.text,
                confidence=min(primary_result.score, 0.95),
                sources=[{
                    'content': r.text,
                    'score': r.score,
                    'source': r.metadata.get('source', 'QSR Manual'),
                    'document_id': r.document_id,
                    'metadata': r.metadata
                } for r in results],
                metadata={
                    'query': equipment_query,
                    'total_results': len(results),
                    'equipment_analyzed': True
                },
                execution_time_ms=execution_time,
                tool_name=self.tool_name,
                visual_citations=visual_citations,
                safety_warnings=safety_warnings,
                equipment_context=equipment_context,
                suggested_actions=suggested_actions,
                equipment_name=equipment_name,
                equipment_type=equipment_type,
                maintenance_required=maintenance_required,
                safety_level=safety_level,
                troubleshooting_steps=troubleshooting_steps
            )
            
            self._update_performance_metrics(execution_time, True)
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Equipment information retrieval failed: {e}")
            
            self._update_performance_metrics(execution_time, False)
            return RagieEquipmentResult(
                success=False,
                content=f"Equipment information retrieval encountered an error: {str(e)}",
                confidence=0.2,
                execution_time_ms=execution_time,
                tool_name=self.tool_name,
                equipment_name=equipment_name
            )
    
    def _enhance_equipment_query(self, equipment_name: str, context: ToolExecutionContext) -> str:
        """Enhance query specifically for equipment information"""
        
        query_parts = [equipment_name]
        
        # Add equipment-specific keywords
        query_parts.extend([
            "equipment", "operation", "maintenance", "troubleshooting", 
            "specifications", "manual", "guide"
        ])
        
        # Add context-specific terms
        if "repair" in context.query.lower() or "fix" in context.query.lower():
            query_parts.extend(["repair", "troubleshooting", "problem", "issue"])
        
        if "clean" in context.query.lower():
            query_parts.extend(["cleaning", "maintenance", "sanitize"])
        
        if context.safety_priority:
            query_parts.extend(["safety", "precautions", "hazards"])
        
        return " ".join(query_parts)
    
    def _determine_equipment_type(self, equipment_name: str, content: str) -> str:
        """Determine equipment type from name and content"""
        
        equipment_name_lower = equipment_name.lower()
        content_lower = content.lower()
        
        if any(keyword in equipment_name_lower for keyword in ['fryer', 'fry']):
            return "fryer"
        elif any(keyword in equipment_name_lower for keyword in ['grill', 'griddle']):
            return "grill"
        elif any(keyword in equipment_name_lower for keyword in ['oven', 'baker']):
            return "oven"
        elif any(keyword in equipment_name_lower for keyword in ['freezer', 'refrigerator', 'cooler']):
            return "cooling"
        elif any(keyword in equipment_name_lower for keyword in ['mixer', 'blend']):
            return "mixer"
        elif any(keyword in equipment_name_lower for keyword in ['ice', 'dispenser']):
            return "ice_machine"
        else:
            return "general"
    
    def _analyze_maintenance_requirements(self, content: str) -> bool:
        """Analyze if maintenance is required based on content"""
        
        maintenance_keywords = [
            'maintenance', 'clean', 'service', 'replace', 'filter', 
            'schedule', 'regular', 'daily', 'weekly', 'monthly'
        ]
        
        return any(keyword in content.lower() for keyword in maintenance_keywords)
    
    def _extract_troubleshooting_steps(self, content: str) -> List[str]:
        """Extract troubleshooting steps from content"""
        
        steps = []
        
        # Look for common troubleshooting patterns
        troubleshooting_patterns = [
            'check', 'verify', 'ensure', 'test', 'replace', 'adjust', 'clean'
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            if any(pattern in sentence.lower() for pattern in troubleshooting_patterns):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 10:  # Avoid very short sentences
                    steps.append(clean_sentence)
        
        return steps[:5]  # Limit to 5 steps
    
    def _generate_equipment_actions(self, equipment_name: str, equipment_type: str, maintenance_required: bool) -> List[str]:
        """Generate suggested actions for equipment"""
        
        actions = []
        
        # General equipment actions
        actions.extend([
            f"Review {equipment_name} operation manual",
            "Check equipment safety protocols",
            "Verify proper installation and setup"
        ])
        
        # Maintenance-specific actions
        if maintenance_required:
            actions.extend([
                "Schedule regular maintenance checks",
                "Document maintenance activities",
                "Ensure proper cleaning procedures"
            ])
        
        # Equipment-type specific actions
        if equipment_type == "fryer":
            actions.append("Monitor oil temperature and quality")
        elif equipment_type == "grill":
            actions.append("Check grill temperature and surface condition")
        elif equipment_type == "oven":
            actions.append("Verify oven temperature calibration")
        elif equipment_type == "cooling":
            actions.append("Monitor temperature and defrost cycles")
        
        return actions

# ===============================================================================
# RAGIE PROCEDURE TOOL
# ===============================================================================

class RagieProcedureTool(BaseRagieTool):
    """
    Procedure-specific tool powered by Ragie
    
    Provides step-by-step procedures, visual guides, and context-aware
    recommendations with navigation and tracking capabilities.
    """
    
    def __init__(self):
        super().__init__("RagieProcedureTool")
        self.tool_context_keywords = [
            "procedure steps instructions process workflow guide how-to"
        ]
    
    async def get_procedure_info(self, procedure_name: str, context: ToolExecutionContext) -> RagieProcedureResult:
        """
        Get comprehensive procedure information from Ragie
        
        Args:
            procedure_name: Name of the procedure
            context: Execution context
            
        Returns:
            RagieProcedureResult with procedure information
        """
        
        start_time = time.time()
        
        try:
            if not self.is_available():
                return RagieProcedureResult(
                    success=False,
                    content="Procedure information not available - Ragie service unavailable",
                    confidence=0.0,
                    execution_time_ms=0.0,
                    tool_name=self.tool_name,
                    procedure_name=procedure_name
                )
            
            # Enhance query for procedure
            procedure_query = self._enhance_procedure_query(procedure_name, context)
            
            # Query Ragie
            results = await self._query_ragie(procedure_query, context, limit=8)
            
            if not results:
                return RagieProcedureResult(
                    success=False,
                    content=f"No procedure information found for: {procedure_name}",
                    confidence=0.3,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    tool_name=self.tool_name,
                    procedure_name=procedure_name
                )
            
            # Process procedure information
            primary_result = results[0]
            
            # Extract procedure steps
            procedure_steps = self._extract_procedure_steps(primary_result.text)
            
            # Determine difficulty level
            difficulty_level = self._determine_difficulty_level(primary_result.text, len(procedure_steps))
            
            # Estimate time
            estimated_time = self._estimate_procedure_time(primary_result.text, len(procedure_steps))
            
            # Extract required tools
            required_tools = self._extract_required_tools(primary_result.text)
            
            # Analyze safety
            safety_level, safety_warnings = await self._analyze_safety_level(procedure_query, primary_result.text)
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(procedure_query, results)
            
            # Generate suggested actions
            suggested_actions = self._generate_procedure_actions(procedure_name, difficulty_level, len(procedure_steps))
            
            execution_time = (time.time() - start_time) * 1000
            
            result = RagieProcedureResult(
                success=True,
                content=primary_result.text,
                confidence=min(primary_result.score, 0.95),
                sources=[{
                    'content': r.text,
                    'score': r.score,
                    'source': r.metadata.get('source', 'QSR Manual'),
                    'document_id': r.document_id,
                    'metadata': r.metadata
                } for r in results],
                metadata={
                    'query': procedure_query,
                    'total_results': len(results),
                    'procedure_analyzed': True
                },
                execution_time_ms=execution_time,
                tool_name=self.tool_name,
                visual_citations=visual_citations,
                safety_warnings=safety_warnings,
                suggested_actions=suggested_actions,
                procedure_name=procedure_name,
                step_count=len(procedure_steps),
                estimated_time=estimated_time,
                difficulty_level=difficulty_level,
                required_tools=required_tools,
                procedure_steps=procedure_steps
            )
            
            self._update_performance_metrics(execution_time, True)
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Procedure information retrieval failed: {e}")
            
            self._update_performance_metrics(execution_time, False)
            return RagieProcedureResult(
                success=False,
                content=f"Procedure information retrieval encountered an error: {str(e)}",
                confidence=0.2,
                execution_time_ms=execution_time,
                tool_name=self.tool_name,
                procedure_name=procedure_name
            )
    
    def _enhance_procedure_query(self, procedure_name: str, context: ToolExecutionContext) -> str:
        """Enhance query specifically for procedure information"""
        
        query_parts = [procedure_name]
        
        # Add procedure-specific keywords
        query_parts.extend([
            "procedure", "steps", "instructions", "guide", "process", "workflow"
        ])
        
        # Add context-specific terms
        if context.interaction_mode == "voice":
            query_parts.extend(["spoken", "verbal", "voice"])
        
        return " ".join(query_parts)
    
    def _extract_procedure_steps(self, content: str) -> List[Dict[str, Any]]:
        """Extract structured procedure steps from content"""
        
        steps = []
        
        # Look for numbered steps
        import re
        
        # Pattern for numbered steps (1., 2., etc.)
        numbered_pattern = r'(\d+)\.\s*([^.]*(?:\.[^.]*)*?)(?=\d+\.|$)'
        numbered_matches = re.findall(numbered_pattern, content, re.DOTALL)
        
        for match in numbered_matches:
            step_number = int(match[0])
            step_content = match[1].strip()
            
            if len(step_content) > 10:  # Avoid very short steps
                steps.append({
                    'step_number': step_number,
                    'instruction': step_content,
                    'type': 'numbered'
                })
        
        # If no numbered steps, look for bullet points or action words
        if not steps:
            sentences = content.split('.')
            step_number = 1
            
            for sentence in sentences:
                sentence = sentence.strip()
                if any(word in sentence.lower() for word in ['first', 'then', 'next', 'finally', 'start', 'begin']):
                    if len(sentence) > 10:
                        steps.append({
                            'step_number': step_number,
                            'instruction': sentence,
                            'type': 'inferred'
                        })
                        step_number += 1
        
        return steps[:10]  # Limit to 10 steps
    
    def _determine_difficulty_level(self, content: str, step_count: int) -> str:
        """Determine difficulty level based on content and step count"""
        
        content_lower = content.lower()
        
        # Check for complexity indicators
        complex_keywords = ['complex', 'advanced', 'skilled', 'experienced', 'professional']
        easy_keywords = ['simple', 'basic', 'easy', 'quick', 'straightforward']
        
        if any(keyword in content_lower for keyword in complex_keywords) or step_count > 8:
            return "hard"
        elif any(keyword in content_lower for keyword in easy_keywords) or step_count <= 3:
            return "easy"
        else:
            return "medium"
    
    def _estimate_procedure_time(self, content: str, step_count: int) -> str:
        """Estimate procedure time based on content and step count"""
        
        content_lower = content.lower()
        
        # Look for time indicators in content
        time_patterns = [
            r'(\d+)\s*minutes?',
            r'(\d+)\s*hours?',
            r'(\d+)\s*seconds?'
        ]
        
        import re
        
        for pattern in time_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                return f"{matches[0]} minutes"
        
        # Estimate based on step count
        if step_count <= 3:
            return "5-10 minutes"
        elif step_count <= 6:
            return "10-20 minutes"
        elif step_count <= 10:
            return "20-30 minutes"
        else:
            return "30+ minutes"
    
    def _extract_required_tools(self, content: str) -> List[str]:
        """Extract required tools from content"""
        
        tools = []
        
        # Common QSR tools
        tool_keywords = [
            'thermometer', 'timer', 'spatula', 'tongs', 'whisk', 'ladle',
            'cutting board', 'knife', 'gloves', 'apron', 'towel', 'brush',
            'cleaner', 'sanitizer', 'bucket', 'mop', 'sponge'
        ]
        
        content_lower = content.lower()
        
        for tool in tool_keywords:
            if tool in content_lower:
                tools.append(tool)
        
        return tools
    
    def _generate_procedure_actions(self, procedure_name: str, difficulty_level: str, step_count: int) -> List[str]:
        """Generate suggested actions for procedure"""
        
        actions = []
        
        # General procedure actions
        actions.extend([
            f"Review all steps for {procedure_name}",
            "Gather required tools and materials",
            "Ensure proper safety equipment is available"
        ])
        
        # Difficulty-specific actions
        if difficulty_level == "hard":
            actions.extend([
                "Consider getting assistance from experienced staff",
                "Review procedure multiple times before starting",
                "Have emergency contacts readily available"
            ])
        elif difficulty_level == "easy":
            actions.append("Follow basic safety protocols")
        
        # Step-count specific actions
        if step_count > 5:
            actions.append("Break procedure into smaller segments if needed")
        
        return actions

# ===============================================================================
# RAGIE SAFETY TOOL
# ===============================================================================

class RagieSafetyTool(BaseRagieTool):
    """
    Safety-specific tool powered by Ragie
    
    Provides safety information, risk assessment, emergency procedures,
    and compliance guidance from Ragie with priority handling.
    """
    
    def __init__(self):
        super().__init__("RagieSafetyTool")
        self.tool_context_keywords = [
            "safety emergency hazard danger risk compliance regulations"
        ]
    
    async def get_safety_info(self, safety_query: str, context: ToolExecutionContext) -> RagieSafetyResult:
        """
        Get comprehensive safety information from Ragie
        
        Args:
            safety_query: Safety-related query
            context: Execution context
            
        Returns:
            RagieSafetyResult with safety information
        """
        
        start_time = time.time()
        
        try:
            if not self.is_available():
                return RagieSafetyResult(
                    success=False,
                    content="Safety information not available - Ragie service unavailable",
                    confidence=0.0,
                    execution_time_ms=0.0,
                    tool_name=self.tool_name,
                    safety_warnings=["Safety service unavailable - use extreme caution"]
                )
            
            # Enhance query for safety
            enhanced_safety_query = self._enhance_safety_query(safety_query, context)
            
            # Query Ragie with higher priority
            results = await self._query_ragie(enhanced_safety_query, context, limit=10)
            
            if not results:
                return RagieSafetyResult(
                    success=False,
                    content=f"No safety information found for: {safety_query}",
                    confidence=0.3,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    tool_name=self.tool_name,
                    safety_warnings=["No specific safety information available - follow general safety protocols"]
                )
            
            # Process safety information
            primary_result = results[0]
            
            # Analyze safety level
            safety_level, safety_warnings = await self._analyze_safety_level(safety_query, primary_result.text)
            
            # Extract risk factors
            risk_factors = self._extract_risk_factors(primary_result.text)
            
            # Extract emergency procedures
            emergency_procedures = self._extract_emergency_procedures(primary_result.text)
            
            # Extract compliance notes
            compliance_notes = self._extract_compliance_notes(primary_result.text)
            
            # Generate immediate actions
            immediate_actions = self._generate_immediate_actions(safety_level, risk_factors)
            
            # Extract visual citations
            visual_citations = await self._extract_visual_citations(safety_query, results)
            
            # Generate suggested actions
            suggested_actions = self._generate_safety_actions(safety_level, risk_factors, emergency_procedures)
            
            # Format safety content with priority marking
            safety_content = f"🚨 SAFETY INFORMATION: {primary_result.text}"
            
            execution_time = (time.time() - start_time) * 1000
            
            result = RagieSafetyResult(
                success=True,
                content=safety_content,
                confidence=min(primary_result.score, 0.95),
                sources=[{
                    'content': r.text,
                    'score': r.score,
                    'source': r.metadata.get('source', 'QSR Safety Manual'),
                    'document_id': r.document_id,
                    'metadata': r.metadata
                } for r in results],
                metadata={
                    'query': safety_query,
                    'enhanced_query': enhanced_safety_query,
                    'total_results': len(results),
                    'safety_priority': True
                },
                execution_time_ms=execution_time,
                tool_name=self.tool_name,
                visual_citations=visual_citations,
                safety_warnings=safety_warnings,
                suggested_actions=suggested_actions,
                safety_level=safety_level,
                risk_factors=risk_factors,
                emergency_procedures=emergency_procedures,
                compliance_notes=compliance_notes,
                immediate_actions=immediate_actions
            )
            
            self._update_performance_metrics(execution_time, True)
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Safety information retrieval failed: {e}")
            
            self._update_performance_metrics(execution_time, False)
            return RagieSafetyResult(
                success=False,
                content=f"Safety information retrieval encountered an error: {str(e)}",
                confidence=0.2,
                execution_time_ms=execution_time,
                tool_name=self.tool_name,
                safety_warnings=["Safety service error - exercise extreme caution and consult safety manual"]
            )
    
    def _enhance_safety_query(self, safety_query: str, context: ToolExecutionContext) -> str:
        """Enhance query specifically for safety information"""
        
        query_parts = [safety_query]
        
        # Add safety-specific keywords
        query_parts.extend([
            "safety", "hazard", "danger", "risk", "precaution", "emergency",
            "compliance", "regulation", "protocol", "procedure"
        ])
        
        # Add equipment-specific safety terms
        if context.equipment_context:
            query_parts.extend([f"{context.equipment_context} safety", "equipment hazards"])
        
        # Add critical safety terms
        query_parts.extend(["critical", "important", "must", "required"])
        
        return " ".join(query_parts)
    
    def _extract_risk_factors(self, content: str) -> List[str]:
        """Extract risk factors from safety content"""
        
        risk_factors = []
        
        # Risk indicator keywords
        risk_keywords = [
            'risk', 'danger', 'hazard', 'caution', 'warning', 'avoid',
            'do not', 'never', 'toxic', 'harmful', 'injury', 'burn'
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                if len(sentence) > 10:
                    risk_factors.append(sentence)
        
        return risk_factors[:5]  # Limit to 5 risk factors
    
    def _extract_emergency_procedures(self, content: str) -> List[str]:
        """Extract emergency procedures from content"""
        
        procedures = []
        
        # Emergency keywords
        emergency_keywords = [
            'emergency', 'immediately', 'urgent', 'call', 'contact',
            'evacuate', 'shut off', 'turn off', 'stop', 'disconnect'
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in emergency_keywords):
                if len(sentence) > 10:
                    procedures.append(sentence)
        
        return procedures[:5]  # Limit to 5 procedures
    
    def _extract_compliance_notes(self, content: str) -> List[str]:
        """Extract compliance notes from content"""
        
        compliance_notes = []
        
        # Compliance keywords
        compliance_keywords = [
            'regulation', 'compliance', 'standard', 'requirement', 'must',
            'shall', 'required', 'mandatory', 'law', 'code'
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in compliance_keywords):
                if len(sentence) > 10:
                    compliance_notes.append(sentence)
        
        return compliance_notes[:3]  # Limit to 3 compliance notes
    
    def _generate_immediate_actions(self, safety_level: str, risk_factors: List[str]) -> List[str]:
        """Generate immediate actions based on safety level and risks"""
        
        actions = []
        
        if safety_level == "critical":
            actions.extend([
                "STOP all activities immediately",
                "Evacuate area if necessary",
                "Contact emergency services if required",
                "Notify management immediately"
            ])
        elif safety_level == "high":
            actions.extend([
                "Stop current activity",
                "Assess immediate risks",
                "Implement safety protocols",
                "Ensure safety equipment is available"
            ])
        elif safety_level == "medium":
            actions.extend([
                "Review safety procedures",
                "Ensure proper protective equipment",
                "Proceed with caution"
            ])
        else:
            actions.extend([
                "Follow standard safety protocols",
                "Maintain awareness of surroundings"
            ])
        
        return actions
    
    def _generate_safety_actions(self, safety_level: str, risk_factors: List[str], emergency_procedures: List[str]) -> List[str]:
        """Generate suggested safety actions"""
        
        actions = []
        
        # General safety actions
        actions.extend([
            "Review all safety protocols before proceeding",
            "Ensure proper personal protective equipment",
            "Keep emergency contacts readily available"
        ])
        
        # Risk-specific actions
        if risk_factors:
            actions.append("Address identified risk factors before proceeding")
        
        # Emergency-specific actions
        if emergency_procedures:
            actions.append("Familiarize yourself with emergency procedures")
        
        # Safety level specific actions
        if safety_level in ["high", "critical"]:
            actions.extend([
                "Consider postponing activity if unsafe",
                "Ensure supervisor approval before proceeding",
                "Have emergency response plan ready"
            ])
        
        return actions

# ===============================================================================
# TOOL REGISTRY AND FACTORY
# ===============================================================================

class RagieToolRegistry:
    """Registry for all Ragie-powered tools"""
    
    def __init__(self):
        self.tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all Ragie tools"""
        
        self.tools = {
            'knowledge': RagieKnowledgeTool(),
            'visual': RagieVisualTool(),
            'equipment': RagieEquipmentTool(),
            'procedure': RagieProcedureTool(),
            'safety': RagieSafetyTool()
        }
    
    def get_tool(self, tool_name: str) -> Optional[BaseRagieTool]:
        """Get a specific tool by name"""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, BaseRagieTool]:
        """Get all available tools"""
        return self.tools
    
    def get_available_tools(self) -> Dict[str, BaseRagieTool]:
        """Get only available tools"""
        return {name: tool for name, tool in self.tools.items() if tool.is_available()}
    
    def get_tool_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all tools"""
        
        metrics = {}
        for name, tool in self.tools.items():
            metrics[name] = tool.get_performance_metrics()
        
        return metrics
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all tools"""
        
        health_status = {
            'ragie_available': RAGIE_AVAILABLE,
            'total_tools': len(self.tools),
            'available_tools': len(self.get_available_tools()),
            'tool_status': {}
        }
        
        for name, tool in self.tools.items():
            health_status['tool_status'][name] = {
                'available': tool.is_available(),
                'execution_count': tool.execution_count,
                'success_rate': tool.success_count / max(tool.execution_count, 1)
            }
        
        return health_status

# ===============================================================================
# GLOBAL TOOL REGISTRY
# ===============================================================================

# Global registry instance
ragie_tools = RagieToolRegistry()

# ===============================================================================
# CONVENIENCE FUNCTIONS
# ===============================================================================

async def search_ragie_knowledge(query: str, context: Optional[ToolExecutionContext] = None) -> RagieKnowledgeResult:
    """Convenience function for knowledge search"""
    
    if context is None:
        context = ToolExecutionContext(query=query)
    
    knowledge_tool = ragie_tools.get_tool('knowledge')
    return await knowledge_tool.search_knowledge(query, context)

async def extract_ragie_visual(query: str, context: Optional[ToolExecutionContext] = None) -> RagieVisualResult:
    """Convenience function for visual content extraction"""
    
    if context is None:
        context = ToolExecutionContext(query=query)
    
    visual_tool = ragie_tools.get_tool('visual')
    return await visual_tool.extract_visual_content(query, context)

async def get_ragie_equipment_info(equipment_name: str, context: Optional[ToolExecutionContext] = None) -> RagieEquipmentResult:
    """Convenience function for equipment information"""
    
    if context is None:
        context = ToolExecutionContext(query=f"equipment {equipment_name}", equipment_context=equipment_name)
    
    equipment_tool = ragie_tools.get_tool('equipment')
    return await equipment_tool.get_equipment_info(equipment_name, context)

async def get_ragie_procedure_info(procedure_name: str, context: Optional[ToolExecutionContext] = None) -> RagieProcedureResult:
    """Convenience function for procedure information"""
    
    if context is None:
        context = ToolExecutionContext(query=f"procedure {procedure_name}")
    
    procedure_tool = ragie_tools.get_tool('procedure')
    return await procedure_tool.get_procedure_info(procedure_name, context)

async def get_ragie_safety_info(safety_query: str, context: Optional[ToolExecutionContext] = None) -> RagieSafetyResult:
    """Convenience function for safety information"""
    
    if context is None:
        context = ToolExecutionContext(query=safety_query, safety_priority=True)
    
    safety_tool = ragie_tools.get_tool('safety')
    return await safety_tool.get_safety_info(safety_query, context)

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Tool classes
    'BaseRagieTool',
    'RagieKnowledgeTool',
    'RagieVisualTool', 
    'RagieEquipmentTool',
    'RagieProcedureTool',
    'RagieSafetyTool',
    
    # Result models
    'RagieToolResult',
    'RagieKnowledgeResult',
    'RagieVisualResult',
    'RagieEquipmentResult',
    'RagieProcedureResult',
    'RagieSafetyResult',
    
    # Context models
    'ToolExecutionContext',
    
    # Registry
    'RagieToolRegistry',
    'ragie_tools',
    
    # Convenience functions
    'search_ragie_knowledge',
    'extract_ragie_visual',
    'get_ragie_equipment_info',
    'get_ragie_procedure_info',
    'get_ragie_safety_info'
]