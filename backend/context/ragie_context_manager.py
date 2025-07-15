#!/usr/bin/env python3
"""
Universal Ragie Context Manager
=============================

Creates context management for text + voice with Ragie that works seamlessly
across both interaction modes while preserving Ragie knowledge and context.

Key Features:
- Universal context for text and voice interactions
- Ragie knowledge preservation across sessions
- Context compression and optimization
- Agent coordination with shared context
- Performance tracking and analytics
- Session persistence

Author: Generated with Memex (https://memex.tech)
"""

import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path
import pickle

# Import Ragie tools for context integration
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.ragie_tools import (
        RagieKnowledgeResult,
        RagieVisualResult,
        RagieEquipmentResult,
        RagieProcedureResult,
        RagieSafetyResult,
        ToolExecutionContext
    )
    RAGIE_TOOLS_AVAILABLE = True
except ImportError:
    RAGIE_TOOLS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===============================================================================
# CONTEXT MODELS AND ENUMS
# ===============================================================================

class InteractionMode(str, Enum):
    """Interaction modes for universal context"""
    TEXT = "text"
    VOICE = "voice"
    MIXED = "mixed"  # Session that has both text and voice

class ContextCompressionStrategy(str, Enum):
    """Strategy for compressing context when it gets too large"""
    NONE = "none"
    RECENT_ONLY = "recent_only"
    SUMMARIZE = "summarize"
    INTELLIGENT = "intelligent"

class RagieKnowledgeContext(BaseModel):
    """Context for Ragie knowledge across interactions"""
    
    # Knowledge state
    active_knowledge: Dict[str, Any] = Field(default_factory=dict)
    knowledge_history: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_confidence: Dict[str, float] = Field(default_factory=dict)
    
    # Knowledge sources
    primary_sources: List[str] = Field(default_factory=list)
    secondary_sources: List[str] = Field(default_factory=list)
    source_reliability: Dict[str, float] = Field(default_factory=dict)
    
    # Knowledge validation
    last_validation: Optional[datetime] = None
    validation_score: float = 0.0
    conflicting_knowledge: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Knowledge persistence
    persistent_facts: Dict[str, Any] = Field(default_factory=dict)
    session_specific: Dict[str, Any] = Field(default_factory=dict)
    
    def add_knowledge(self, knowledge_result: Any, source: str = "ragie"):
        """Add knowledge from Ragie result"""
        
        knowledge_id = hashlib.md5(f"{source}_{knowledge_result.content}".encode()).hexdigest()[:8]
        
        knowledge_entry = {
            'id': knowledge_id,
            'content': knowledge_result.content,
            'confidence': knowledge_result.confidence,
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'tool_name': knowledge_result.tool_name,
            'knowledge_type': getattr(knowledge_result, 'knowledge_type', 'general')
        }
        
        self.active_knowledge[knowledge_id] = knowledge_entry
        self.knowledge_history.append(knowledge_entry)
        self.knowledge_confidence[knowledge_id] = knowledge_result.confidence
        
        if source not in self.primary_sources:
            self.primary_sources.append(source)
    
    def get_relevant_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant knowledge for a query"""
        
        # Simple relevance scoring based on content similarity
        relevant_knowledge = []
        query_lower = query.lower()
        
        for knowledge_id, knowledge in self.active_knowledge.items():
            content_lower = knowledge['content'].lower()
            
            # Basic relevance scoring
            score = 0.0
            query_words = query_lower.split()
            
            for word in query_words:
                if word in content_lower:
                    score += 1.0
            
            if score > 0:
                relevant_knowledge.append({
                    **knowledge,
                    'relevance_score': score
                })
        
        # Sort by relevance and return top results
        relevant_knowledge.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_knowledge[:limit]
    
    def compress_knowledge(self, strategy: ContextCompressionStrategy = ContextCompressionStrategy.RECENT_ONLY):
        """Compress knowledge context based on strategy"""
        
        if strategy == ContextCompressionStrategy.RECENT_ONLY:
            # Keep only recent knowledge
            recent_cutoff = datetime.now() - timedelta(hours=1)
            
            recent_knowledge = {}
            for knowledge_id, knowledge in self.active_knowledge.items():
                knowledge_time = datetime.fromisoformat(knowledge['timestamp'])
                if knowledge_time > recent_cutoff:
                    recent_knowledge[knowledge_id] = knowledge
            
            self.active_knowledge = recent_knowledge
        
        elif strategy == ContextCompressionStrategy.INTELLIGENT:
            # Keep high-confidence and recent knowledge
            compressed_knowledge = {}
            
            for knowledge_id, knowledge in self.active_knowledge.items():
                confidence = self.knowledge_confidence.get(knowledge_id, 0.0)
                knowledge_time = datetime.fromisoformat(knowledge['timestamp'])
                age_hours = (datetime.now() - knowledge_time).total_seconds() / 3600
                
                # Keep if high confidence or very recent
                if confidence > 0.7 or age_hours < 0.5:
                    compressed_knowledge[knowledge_id] = knowledge
            
            self.active_knowledge = compressed_knowledge

class RagieCitationContext(BaseModel):
    """Context for visual citations from Ragie"""
    
    # Citation state
    active_citations: List[Dict[str, Any]] = Field(default_factory=list)
    citation_history: List[Dict[str, Any]] = Field(default_factory=list)
    citation_groups: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    
    # Citation metadata
    citation_sources: Set[str] = Field(default_factory=set)
    citation_types: Set[str] = Field(default_factory=set)
    citation_confidence: Dict[str, float] = Field(default_factory=dict)
    
    # Citation organization
    equipment_citations: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    procedure_citations: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    safety_citations: List[Dict[str, Any]] = Field(default_factory=list)
    
    def add_citations(self, citations: List[Dict[str, Any]], source: str = "ragie"):
        """Add citations from Ragie result"""
        
        for citation in citations:
            citation_id = citation.get('citation_id', hashlib.md5(str(citation).encode()).hexdigest()[:8])
            
            enhanced_citation = {
                **citation,
                'citation_id': citation_id,
                'source': source,
                'timestamp': datetime.now().isoformat(),
                'interaction_mode': 'universal'
            }
            
            self.active_citations.append(enhanced_citation)
            self.citation_history.append(enhanced_citation)
            
            # Organize by type
            citation_type = citation.get('type', 'general')
            self.citation_types.add(citation_type)
            
            if citation_type not in self.citation_groups:
                self.citation_groups[citation_type] = []
            self.citation_groups[citation_type].append(enhanced_citation)
            
            # Organize by equipment if available
            if 'equipment_type' in citation:
                equipment_type = citation['equipment_type']
                if equipment_type not in self.equipment_citations:
                    self.equipment_citations[equipment_type] = []
                self.equipment_citations[equipment_type].append(enhanced_citation)
    
    def get_citations_for_equipment(self, equipment_name: str) -> List[Dict[str, Any]]:
        """Get citations relevant to specific equipment"""
        
        equipment_citations = []
        
        # Check equipment-specific citations
        for equipment_type, citations in self.equipment_citations.items():
            if equipment_name.lower() in equipment_type.lower():
                equipment_citations.extend(citations)
        
        # Check general citations that mention equipment
        for citation in self.active_citations:
            if equipment_name.lower() in citation.get('description', '').lower():
                equipment_citations.append(citation)
        
        return equipment_citations
    
    def get_voice_friendly_citations(self) -> List[str]:
        """Get voice-friendly citation descriptions"""
        
        descriptions = []
        
        for citation in self.active_citations[-5:]:  # Latest 5 citations
            citation_type = citation.get('type', 'reference')
            source = citation.get('source', 'manual')
            title = citation.get('title', citation_type)
            
            # Create voice-friendly description
            if citation_type == 'image':
                description = f"There's an image in the {source} showing {title.lower()}"
            elif citation_type == 'diagram':
                description = f"Check the diagram in the {source} for {title.lower()}"
            elif citation_type == 'table':
                description = f"The {source} has a table with {title.lower()}"
            else:
                description = f"See the {source} for more on {title.lower()}"
            
            descriptions.append(description)
        
        return descriptions

class RagieEquipmentContext(BaseModel):
    """Context for equipment focus from Ragie"""
    
    # Equipment state
    current_equipment: Optional[str] = None
    equipment_history: List[str] = Field(default_factory=list)
    equipment_details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Equipment relationships
    related_equipment: Dict[str, List[str]] = Field(default_factory=dict)
    equipment_groups: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Equipment knowledge
    equipment_manuals: Dict[str, List[str]] = Field(default_factory=dict)
    equipment_procedures: Dict[str, List[str]] = Field(default_factory=dict)
    equipment_safety: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Equipment status
    equipment_status: Dict[str, str] = Field(default_factory=dict)
    maintenance_schedules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    def set_current_equipment(self, equipment_name: str, equipment_result: Optional[Any] = None):
        """Set current equipment focus"""
        
        self.current_equipment = equipment_name
        
        if equipment_name not in self.equipment_history:
            self.equipment_history.append(equipment_name)
        
        # Add equipment details from Ragie result
        if equipment_result and hasattr(equipment_result, 'equipment_type'):
            self.equipment_details[equipment_name] = {
                'equipment_type': equipment_result.equipment_type,
                'maintenance_required': equipment_result.maintenance_required,
                'safety_level': equipment_result.safety_level,
                'troubleshooting_steps': equipment_result.troubleshooting_steps,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_equipment_context(self, equipment_name: str) -> Dict[str, Any]:
        """Get comprehensive equipment context"""
        
        context = {
            'equipment_name': equipment_name,
            'is_current': equipment_name == self.current_equipment,
            'details': self.equipment_details.get(equipment_name, {}),
            'related': self.related_equipment.get(equipment_name, []),
            'manuals': self.equipment_manuals.get(equipment_name, []),
            'procedures': self.equipment_procedures.get(equipment_name, []),
            'safety': self.equipment_safety.get(equipment_name, []),
            'status': self.equipment_status.get(equipment_name, 'unknown'),
            'maintenance': self.maintenance_schedules.get(equipment_name, {})
        }
        
        return context
    
    def add_equipment_procedure(self, equipment_name: str, procedure_name: str):
        """Add procedure to equipment context"""
        
        if equipment_name not in self.equipment_procedures:
            self.equipment_procedures[equipment_name] = []
        
        if procedure_name not in self.equipment_procedures[equipment_name]:
            self.equipment_procedures[equipment_name].append(procedure_name)

class RagieProcedureContext(BaseModel):
    """Context for procedure progress from Ragie"""
    
    # Procedure state
    current_procedure: Optional[str] = None
    procedure_step: Optional[int] = None
    total_steps: Optional[int] = None
    
    # Procedure details
    procedure_details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    procedure_steps: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    procedure_progress: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Procedure context
    procedure_equipment: Dict[str, str] = Field(default_factory=dict)
    procedure_safety: Dict[str, List[str]] = Field(default_factory=dict)
    procedure_tools: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Procedure execution
    active_procedures: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    completed_procedures: List[str] = Field(default_factory=list)
    
    def start_procedure(self, procedure_name: str, procedure_result: Optional[Any] = None):
        """Start a new procedure"""
        
        self.current_procedure = procedure_name
        self.procedure_step = 1
        
        if procedure_result and hasattr(procedure_result, 'step_count'):
            self.total_steps = procedure_result.step_count
            
            # Add procedure details
            self.procedure_details[procedure_name] = {
                'step_count': procedure_result.step_count,
                'estimated_time': procedure_result.estimated_time,
                'difficulty_level': procedure_result.difficulty_level,
                'required_tools': procedure_result.required_tools,
                'procedure_steps': procedure_result.procedure_steps,
                'started_at': datetime.now().isoformat()
            }
            
            # Add procedure steps
            self.procedure_steps[procedure_name] = procedure_result.procedure_steps
        
        # Track active procedure
        self.active_procedures[procedure_name] = {
            'current_step': 1,
            'total_steps': self.total_steps,
            'started_at': datetime.now().isoformat(),
            'status': 'active'
        }
    
    def advance_procedure_step(self, procedure_name: Optional[str] = None):
        """Advance to next procedure step"""
        
        procedure_name = procedure_name or self.current_procedure
        
        if procedure_name and procedure_name in self.active_procedures:
            current_step = self.active_procedures[procedure_name]['current_step']
            total_steps = self.active_procedures[procedure_name]['total_steps']
            
            if current_step < total_steps:
                self.active_procedures[procedure_name]['current_step'] += 1
                self.procedure_step = current_step + 1
            else:
                self.complete_procedure(procedure_name)
    
    def complete_procedure(self, procedure_name: Optional[str] = None):
        """Complete a procedure"""
        
        procedure_name = procedure_name or self.current_procedure
        
        if procedure_name and procedure_name in self.active_procedures:
            self.active_procedures[procedure_name]['status'] = 'completed'
            self.active_procedures[procedure_name]['completed_at'] = datetime.now().isoformat()
            
            if procedure_name not in self.completed_procedures:
                self.completed_procedures.append(procedure_name)
            
            # Reset current procedure if this was it
            if procedure_name == self.current_procedure:
                self.current_procedure = None
                self.procedure_step = None
                self.total_steps = None
    
    def get_procedure_progress(self, procedure_name: Optional[str] = None) -> Dict[str, Any]:
        """Get procedure progress information"""
        
        procedure_name = procedure_name or self.current_procedure
        
        if not procedure_name:
            return {}
        
        progress = {
            'procedure_name': procedure_name,
            'current_step': self.procedure_step,
            'total_steps': self.total_steps,
            'is_active': procedure_name in self.active_procedures,
            'is_completed': procedure_name in self.completed_procedures,
            'details': self.procedure_details.get(procedure_name, {}),
            'steps': self.procedure_steps.get(procedure_name, [])
        }
        
        if procedure_name in self.active_procedures:
            progress.update(self.active_procedures[procedure_name])
        
        return progress

class RagieAgentContext(BaseModel):
    """Context for agent coordination with Ragie"""
    
    # Agent state
    active_agents: Set[str] = Field(default_factory=set)
    agent_history: List[Dict[str, Any]] = Field(default_factory=list)
    agent_performance: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Agent coordination
    primary_agent: Optional[str] = None
    agent_handoffs: List[Dict[str, Any]] = Field(default_factory=list)
    agent_collaboration: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Agent knowledge
    agent_knowledge: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    agent_specialization: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Agent optimization
    agent_preferences: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    agent_success_rate: Dict[str, float] = Field(default_factory=dict)
    
    def set_primary_agent(self, agent_name: str):
        """Set primary agent for interaction"""
        
        self.primary_agent = agent_name
        self.active_agents.add(agent_name)
        
        # Track agent usage
        self.agent_history.append({
            'agent': agent_name,
            'action': 'set_primary',
            'timestamp': datetime.now().isoformat()
        })
    
    def add_agent_knowledge(self, agent_name: str, knowledge_result: Any):
        """Add knowledge from specific agent"""
        
        if agent_name not in self.agent_knowledge:
            self.agent_knowledge[agent_name] = {}
        
        knowledge_entry = {
            'content': knowledge_result.content,
            'confidence': knowledge_result.confidence,
            'tool_name': knowledge_result.tool_name,
            'timestamp': datetime.now().isoformat()
        }
        
        knowledge_id = hashlib.md5(f"{agent_name}_{knowledge_result.content}".encode()).hexdigest()[:8]
        self.agent_knowledge[agent_name][knowledge_id] = knowledge_entry
    
    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """Get agent performance metrics"""
        
        return self.agent_performance.get(agent_name, {
            'queries_handled': 0,
            'success_rate': 0.0,
            'avg_confidence': 0.0,
            'last_active': None
        })
    
    def update_agent_performance(self, agent_name: str, success: bool, confidence: float):
        """Update agent performance metrics"""
        
        if agent_name not in self.agent_performance:
            self.agent_performance[agent_name] = {
                'queries_handled': 0,
                'successful_queries': 0,
                'total_confidence': 0.0,
                'last_active': None
            }
        
        metrics = self.agent_performance[agent_name]
        metrics['queries_handled'] += 1
        metrics['last_active'] = datetime.now().isoformat()
        
        if success:
            metrics['successful_queries'] += 1
        
        metrics['total_confidence'] += confidence
        
        # Calculate rates
        metrics['success_rate'] = metrics['successful_queries'] / metrics['queries_handled']
        metrics['avg_confidence'] = metrics['total_confidence'] / metrics['queries_handled']

class RagiePerformanceContext(BaseModel):
    """Context for performance tracking with Ragie"""
    
    # Performance metrics
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_response_time: float = 0.0
    
    # Query analytics
    query_history: List[Dict[str, Any]] = Field(default_factory=list)
    query_patterns: Dict[str, int] = Field(default_factory=dict)
    query_success_rate: Dict[str, float] = Field(default_factory=dict)
    
    # Tool performance
    tool_usage: Dict[str, int] = Field(default_factory=dict)
    tool_performance: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Session analytics
    session_duration: float = 0.0
    session_queries: int = 0
    session_success_rate: float = 0.0
    
    # Context optimization
    context_compression_count: int = 0
    cache_hit_rate: float = 0.0
    
    def record_query(self, query: str, tool_name: str, success: bool, response_time: float, confidence: float):
        """Record query performance"""
        
        self.total_queries += 1
        
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        
        # Update average response time
        self.avg_response_time = (
            (self.avg_response_time * (self.total_queries - 1) + response_time) / self.total_queries
        )
        
        # Track query
        query_entry = {
            'query': query,
            'tool_name': tool_name,
            'success': success,
            'response_time': response_time,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        self.query_history.append(query_entry)
        
        # Track tool usage
        if tool_name not in self.tool_usage:
            self.tool_usage[tool_name] = 0
        self.tool_usage[tool_name] += 1
        
        # Update tool performance
        if tool_name not in self.tool_performance:
            self.tool_performance[tool_name] = {
                'queries': 0,
                'successes': 0,
                'total_time': 0.0,
                'total_confidence': 0.0
            }
        
        tool_metrics = self.tool_performance[tool_name]
        tool_metrics['queries'] += 1
        tool_metrics['total_time'] += response_time
        tool_metrics['total_confidence'] += confidence
        
        if success:
            tool_metrics['successes'] += 1
        
        # Calculate tool rates
        tool_metrics['success_rate'] = tool_metrics['successes'] / tool_metrics['queries']
        tool_metrics['avg_time'] = tool_metrics['total_time'] / tool_metrics['queries']
        tool_metrics['avg_confidence'] = tool_metrics['total_confidence'] / tool_metrics['queries']
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        
        return {
            'total_queries': self.total_queries,
            'success_rate': self.successful_queries / max(self.total_queries, 1),
            'failure_rate': self.failed_queries / max(self.total_queries, 1),
            'avg_response_time': self.avg_response_time,
            'session_duration': self.session_duration,
            'session_queries': self.session_queries,
            'tool_usage': self.tool_usage,
            'cache_hit_rate': self.cache_hit_rate,
            'context_compressions': self.context_compression_count
        }

class UniversalRagieContext(BaseModel):
    """Universal context that works across text and voice with Ragie"""
    
    # Session metadata
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    interaction_mode: InteractionMode = InteractionMode.MIXED
    
    # Context components
    knowledge_context: RagieKnowledgeContext = Field(default_factory=RagieKnowledgeContext)
    citation_context: RagieCitationContext = Field(default_factory=RagieCitationContext)
    equipment_context: RagieEquipmentContext = Field(default_factory=RagieEquipmentContext)
    procedure_context: RagieProcedureContext = Field(default_factory=RagieProcedureContext)
    agent_context: RagieAgentContext = Field(default_factory=RagieAgentContext)
    performance_context: RagiePerformanceContext = Field(default_factory=RagiePerformanceContext)
    
    # Interaction tracking
    text_interactions: int = 0
    voice_interactions: int = 0
    total_interactions: int = 0
    
    # Context state
    compressed_count: int = 0
    context_size: int = 0
    max_context_size: int = 10000  # Maximum context size before compression
    
    def update_interaction_mode(self, mode: InteractionMode):
        """Update interaction mode tracking"""
        
        if mode == InteractionMode.TEXT:
            self.text_interactions += 1
        elif mode == InteractionMode.VOICE:
            self.voice_interactions += 1
        
        self.total_interactions += 1
        
        # Update overall mode
        if self.text_interactions > 0 and self.voice_interactions > 0:
            self.interaction_mode = InteractionMode.MIXED
        elif self.text_interactions > 0:
            self.interaction_mode = InteractionMode.TEXT
        elif self.voice_interactions > 0:
            self.interaction_mode = InteractionMode.VOICE
        
        self.last_updated = datetime.now()
    
    def add_ragie_result(self, result: Any, interaction_mode: InteractionMode):
        """Add result from Ragie tool"""
        
        self.update_interaction_mode(interaction_mode)
        
        # Add to knowledge context
        self.knowledge_context.add_knowledge(result)
        
        # Add citations if available
        if hasattr(result, 'visual_citations') and result.visual_citations:
            self.citation_context.add_citations(result.visual_citations)
        
        # Add equipment context if available
        if hasattr(result, 'equipment_name'):
            self.equipment_context.set_current_equipment(result.equipment_name, result)
        
        # Add procedure context if available
        if hasattr(result, 'procedure_name'):
            self.procedure_context.start_procedure(result.procedure_name, result)
        
        # Record performance
        self.performance_context.record_query(
            query=getattr(result, 'query', ''),
            tool_name=result.tool_name,
            success=result.success,
            response_time=result.execution_time_ms,
            confidence=result.confidence
        )
    
    def get_context_for_query(self, query: str, interaction_mode: InteractionMode) -> Dict[str, Any]:
        """Get relevant context for a query"""
        
        context = {
            'session_id': self.session_id,
            'interaction_mode': interaction_mode.value,
            'total_interactions': self.total_interactions,
            'relevant_knowledge': self.knowledge_context.get_relevant_knowledge(query),
            'current_equipment': self.equipment_context.current_equipment,
            'current_procedure': self.procedure_context.get_procedure_progress(),
            'primary_agent': self.agent_context.primary_agent,
            'session_duration': (datetime.now() - self.created_at).total_seconds()
        }
        
        # Add interaction-specific context
        if interaction_mode == InteractionMode.VOICE:
            context['voice_citations'] = self.citation_context.get_voice_friendly_citations()
        else:
            context['visual_citations'] = self.citation_context.active_citations
        
        return context
    
    def compress_context(self, strategy: ContextCompressionStrategy = ContextCompressionStrategy.INTELLIGENT):
        """Compress context to manage size"""
        
        self.knowledge_context.compress_knowledge(strategy)
        self.compressed_count += 1
        self.performance_context.context_compression_count += 1
        
        # Update context size estimate
        self.context_size = len(str(self.dict()))
        
        logger.info(f"Context compressed using {strategy.value} strategy. Size: {self.context_size}")
    
    def should_compress(self) -> bool:
        """Check if context should be compressed"""
        
        current_size = len(str(self.dict()))
        self.context_size = current_size
        
        return current_size > self.max_context_size
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get context health status"""
        
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'interaction_mode': self.interaction_mode.value,
            'total_interactions': self.total_interactions,
            'text_interactions': self.text_interactions,
            'voice_interactions': self.voice_interactions,
            'context_size': self.context_size,
            'compressed_count': self.compressed_count,
            'knowledge_entries': len(self.knowledge_context.active_knowledge),
            'active_citations': len(self.citation_context.active_citations),
            'current_equipment': self.equipment_context.current_equipment,
            'current_procedure': self.procedure_context.current_procedure,
            'performance_summary': self.performance_context.get_performance_summary()
        }

# ===============================================================================
# RAGIE CONTEXT MANAGER
# ===============================================================================

class RagieContextManager:
    """Universal context manager for Ragie integration"""
    
    def __init__(self, persistence_path: Optional[str] = None):
        self.contexts: Dict[str, UniversalRagieContext] = {}
        self.persistence_path = Path(persistence_path) if persistence_path else None
        
        # Manager settings
        self.max_sessions = 1000
        self.session_timeout = timedelta(hours=24)
        self.auto_compression = True
        self.compression_strategy = ContextCompressionStrategy.INTELLIGENT
        
        # Performance tracking
        self.manager_metrics = {
            'total_sessions': 0,
            'active_sessions': 0,
            'compressed_sessions': 0,
            'persistent_sessions': 0
        }
        
        # Load persisted contexts
        if self.persistence_path:
            self._load_persisted_contexts()
    
    def create_context(self, session_id: str, interaction_mode: InteractionMode = InteractionMode.MIXED) -> UniversalRagieContext:
        """Create new universal context"""
        
        if session_id in self.contexts:
            return self.contexts[session_id]
        
        context = UniversalRagieContext(
            session_id=session_id,
            interaction_mode=interaction_mode
        )
        
        self.contexts[session_id] = context
        self.manager_metrics['total_sessions'] += 1
        self.manager_metrics['active_sessions'] += 1
        
        logger.info(f"Created new universal context for session: {session_id}")
        
        return context
    
    def get_context(self, session_id: str) -> Optional[UniversalRagieContext]:
        """Get existing context"""
        
        return self.contexts.get(session_id)
    
    def get_or_create_context(self, session_id: str, interaction_mode: InteractionMode = InteractionMode.MIXED) -> UniversalRagieContext:
        """Get existing context or create new one"""
        
        context = self.get_context(session_id)
        if context:
            return context
        
        return self.create_context(session_id, interaction_mode)
    
    async def process_ragie_result(self, session_id: str, result: Any, interaction_mode: InteractionMode):
        """Process Ragie result and update context"""
        
        context = self.get_or_create_context(session_id, interaction_mode)
        context.add_ragie_result(result, interaction_mode)
        
        # Check if compression needed
        if self.auto_compression and context.should_compress():
            context.compress_context(self.compression_strategy)
            self.manager_metrics['compressed_sessions'] += 1
        
        # Persist if enabled
        if self.persistence_path:
            await self._persist_context(context)
    
    def get_context_for_query(self, session_id: str, query: str, interaction_mode: InteractionMode) -> Dict[str, Any]:
        """Get context for query processing"""
        
        context = self.get_or_create_context(session_id, interaction_mode)
        return context.get_context_for_query(query, interaction_mode)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, context in self.contexts.items():
            if current_time - context.last_updated > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.contexts[session_id]
            self.manager_metrics['active_sessions'] -= 1
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_manager_metrics(self) -> Dict[str, Any]:
        """Get manager performance metrics"""
        
        return {
            **self.manager_metrics,
            'active_sessions': len(self.contexts),
            'avg_context_size': sum(ctx.context_size for ctx in self.contexts.values()) / max(len(self.contexts), 1),
            'total_interactions': sum(ctx.total_interactions for ctx in self.contexts.values()),
            'compression_rate': self.manager_metrics['compressed_sessions'] / max(self.manager_metrics['total_sessions'], 1)
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        
        return {
            'manager_metrics': self.get_manager_metrics(),
            'active_sessions': len(self.contexts),
            'ragie_tools_available': RAGIE_TOOLS_AVAILABLE,
            'persistence_enabled': self.persistence_path is not None,
            'auto_compression': self.auto_compression,
            'compression_strategy': self.compression_strategy.value,
            'session_timeout_hours': self.session_timeout.total_seconds() / 3600
        }
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        
        sessions = []
        
        for session_id, context in self.contexts.items():
            sessions.append({
                'session_id': session_id,
                'interaction_mode': context.interaction_mode.value,
                'total_interactions': context.total_interactions,
                'created_at': context.created_at.isoformat(),
                'last_updated': context.last_updated.isoformat(),
                'context_size': context.context_size,
                'current_equipment': context.equipment_context.current_equipment,
                'current_procedure': context.procedure_context.current_procedure
            })
        
        return sessions
    
    async def _persist_context(self, context: UniversalRagieContext):
        """Persist context to storage"""
        
        if not self.persistence_path:
            return
        
        try:
            self.persistence_path.mkdir(parents=True, exist_ok=True)
            
            context_file = self.persistence_path / f"{context.session_id}.json"
            
            with open(context_file, 'w') as f:
                json.dump(context.dict(), f, indent=2, default=str)
            
            self.manager_metrics['persistent_sessions'] += 1
            
        except Exception as e:
            logger.error(f"Failed to persist context {context.session_id}: {e}")
    
    def _load_persisted_contexts(self):
        """Load persisted contexts from storage"""
        
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        try:
            for context_file in self.persistence_path.glob("*.json"):
                with open(context_file, 'r') as f:
                    context_data = json.load(f)
                
                # Convert back to UniversalRagieContext
                context = UniversalRagieContext(**context_data)
                self.contexts[context.session_id] = context
                
                logger.info(f"Loaded persisted context: {context.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to load persisted contexts: {e}")

# ===============================================================================
# GLOBAL CONTEXT MANAGER
# ===============================================================================

# Global universal context manager
universal_context_manager = RagieContextManager()

# ===============================================================================
# CONVENIENCE FUNCTIONS
# ===============================================================================

def get_universal_context(session_id: str, interaction_mode: InteractionMode = InteractionMode.MIXED) -> UniversalRagieContext:
    """Get universal context for session"""
    
    return universal_context_manager.get_or_create_context(session_id, interaction_mode)

async def process_ragie_result_with_context(session_id: str, result: Any, interaction_mode: InteractionMode):
    """Process Ragie result with context management"""
    
    await universal_context_manager.process_ragie_result(session_id, result, interaction_mode)

def get_context_for_query(session_id: str, query: str, interaction_mode: InteractionMode) -> Dict[str, Any]:
    """Get context for query processing"""
    
    return universal_context_manager.get_context_for_query(session_id, query, interaction_mode)

def get_context_health() -> Dict[str, Any]:
    """Get context system health"""
    
    return universal_context_manager.get_health_status()

def list_active_sessions() -> List[Dict[str, Any]]:
    """List all active sessions"""
    
    return universal_context_manager.list_active_sessions()

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    'RagieContextManager',
    'UniversalRagieContext',
    'RagieKnowledgeContext',
    'RagieCitationContext',
    'RagieEquipmentContext',
    'RagieProcedureContext',
    'RagieAgentContext',
    'RagiePerformanceContext',
    'InteractionMode',
    'ContextCompressionStrategy',
    'universal_context_manager',
    'get_universal_context',
    'process_ragie_result_with_context',
    'get_context_for_query',
    'get_context_health',
    'list_active_sessions'
]