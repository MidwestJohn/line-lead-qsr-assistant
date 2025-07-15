#!/usr/bin/env python3
"""
Shared Types for QSR Agents
===========================

Common types, enums, and data structures shared across all QSR agents
to avoid circular imports between orchestrator and individual agents.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Available specialist agent types"""
    BASE = "base"
    EQUIPMENT = "equipment"
    SAFETY = "safety"
    OPERATIONS = "operations"
    TRAINING = "training"
    # Legacy voice_agent compatibility
    PROCEDURE = "procedure"
    MAINTENANCE = "maintenance"
    GENERAL = "general"


class AgentCoordinationStrategy(str, Enum):
    """Agent coordination strategies"""
    SINGLE_AGENT = "single_agent"          # Use one specialized agent
    PARALLEL_CONSULTATION = "parallel"     # Multiple agents, synthesize
    SEQUENTIAL_HANDOFF = "sequential"      # Pass between agents
    HIERARCHICAL = "hierarchical"          # Primary agent with specialist backup


class ConversationIntent(str, Enum):
    """Detected user intents for better response handling"""
    EQUIPMENT_QUESTION = "equipment_question"
    FOLLOW_UP = "follow_up"
    NEW_TOPIC = "new_topic"
    CLARIFICATION = "clarification"
    COMPLETION = "completion"
    EMERGENCY = "emergency"


class QueryClassification(BaseModel):
    """Results of query classification for agent routing"""
    primary_agent: AgentType = Field(description="Primary agent to handle the query")
    secondary_agent: Optional[AgentType] = Field(default=None, description="Secondary agent for complex queries")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in classification")
    keywords: List[str] = Field(default_factory=list, description="Key terms that influenced classification")
    urgency: str = Field(default="normal", description="Query urgency level")
    reasoning: str = Field(description="Explanation of classification decision")
    # Enhanced fields for Ragie integration
    equipment_mentioned: List[str] = Field(default_factory=list, description="Equipment mentioned in query")
    procedure_detected: Optional[str] = Field(default=None, description="Procedure type detected")
    safety_critical: bool = Field(default=False, description="Whether query is safety critical")


class OrchestratorResponse(BaseModel):
    """Enhanced response with orchestration metadata"""
    response: str = Field(description="The actual response content")
    agent_used: AgentType = Field(description="Which agent provided the response")
    classification: QueryClassification = Field(description="How the query was classified")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance data")
    context_preserved: bool = Field(default=True, description="Whether context was preserved")
    handoff_occurred: bool = Field(default=False, description="Whether agent handoff occurred")


# Export all types
__all__ = [
    "AgentType",
    "AgentCoordinationStrategy",
    "ConversationIntent",
    "QueryClassification", 
    "OrchestratorResponse"
]