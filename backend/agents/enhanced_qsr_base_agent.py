#!/usr/bin/env python3
"""
Enhanced QSR Base Agent with Ragie Integration
==============================================

Enhanced PydanticAI Agent with Ragie knowledge integration through RunContext.
Combines the clean agent architecture with Ragie-powered knowledge retrieval.

Features:
- PydanticAI Agent with Ragie RunContext dependency injection
- QSR-optimized Tools for equipment, safety, and procedures
- Context-aware knowledge retrieval with visual citations
- Structured response handling with multi-modal content
- Production-ready error handling and fallbacks

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UnexpectedModelBehavior, ModelRetry
from pydantic_ai.messages import ModelMessage
from pydantic import BaseModel, Field

# Import enhanced Ragie service
from services.enhanced_ragie_service import (
    enhanced_ragie_service, 
    RagieSearchResult, 
    QSRContext
)

logger = logging.getLogger(__name__)

@dataclass
class QSRRunContext:
    """RunContext for QSR agents with Ragie integration"""
    ragie_service: Any  # Enhanced Ragie service
    conversation_id: str
    equipment_context: Optional[str] = None
    procedure_context: Optional[str] = None
    safety_level: Optional[str] = None
    visual_citations: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.visual_citations is None:
            self.visual_citations = []

class QSRResponse(BaseModel):
    """Enhanced QSR response with Ragie integration"""
    response: str = Field(description="Main response text")
    equipment_mentioned: List[str] = Field(default_factory=list, description="Equipment mentioned in response")
    procedures_referenced: List[str] = Field(default_factory=list, description="Procedures referenced")
    safety_warnings: List[str] = Field(default_factory=list, description="Safety warnings included")
    visual_citations: List[Dict[str, Any]] = Field(default_factory=list, description="Visual citations from Ragie")
    confidence_score: float = Field(default=1.0, description="Response confidence score")
    ragie_enhanced: bool = Field(default=False, description="Whether response was enhanced with Ragie knowledge")

class EnhancedQSRAgent:
    """Enhanced QSR Agent with Ragie knowledge integration"""
    
    def __init__(self):
        """Initialize enhanced QSR agent with Ragie tools"""
        self.agent = Agent(
            'openai:gpt-4o',
            result_type=QSRResponse,
            deps_type=QSRRunContext,
            system_prompt=self._get_system_prompt(),
            retries=2
        )
        
        # Add Ragie-powered tools
        self._add_ragie_tools()
        
        logger.info("Enhanced QSR Agent initialized with Ragie integration")
    
    def _get_system_prompt(self) -> str:
        """Enhanced system prompt with Ragie knowledge awareness"""
        return """You are an expert QSR (Quick Service Restaurant) assistant with access to comprehensive equipment manuals, safety protocols, and operational procedures through an advanced knowledge system.

**YOUR ENHANCED CAPABILITIES:**
- Access to live equipment manuals, diagrams, and troubleshooting guides
- Real-time safety protocol and procedure lookup
- Visual citations with images, videos, and step-by-step guides
- Context-aware responses based on conversation history

**EQUIPMENT EXPERTISE WITH LIVE KNOWLEDGE:**
- Taylor ice cream machines (live manual access, visual diagnostics)
- Vulcan fryers (real-time troubleshooting, safety protocols)
- Hobart mixers (operational guides, maintenance schedules)
- Traulsen refrigeration (temperature control, diagnostics)
- All QSR equipment with manual and procedure lookup

**ENHANCED SAFETY PROTOCOLS:**
- HACCP compliance with visual guides
- Emergency procedures with step-by-step instructions
- Safety training materials with video references
- Incident reporting with proper documentation

**OPERATIONAL EXCELLENCE:**
- Live procedure lookup for all operations
- Visual training materials and guides
- Context-aware operational guidance
- Equipment-specific operational procedures

**RESPONSE GUIDELINES:**
1. **Always use available tools** to search for relevant equipment manuals, procedures, or safety information
2. **Include visual citations** when available (images, diagrams, videos)
3. **Reference specific manual sections** and page numbers when applicable
4. **Provide confidence scores** based on the quality of retrieved knowledge
5. **Maintain context** across the conversation for better assistance

When responding:
- Search for relevant knowledge before providing answers
- Include visual citations to support your response
- Reference specific equipment models and procedures
- Provide safety warnings when appropriate
- Maintain equipment and procedure context for follow-up questions"""

    def _add_ragie_tools(self):
        """Add Ragie-powered tools to the agent"""
        
        @self.agent.tool
        async def search_equipment_manual(ctx: RunContext[QSRRunContext], equipment: str, issue: str = "") -> str:
            """Search equipment manuals for specific equipment and issues"""
            query = f"equipment {equipment} {issue}".strip()
            qsr_context = QSRContext(equipment_type=equipment.lower())
            
            results = await ctx.deps.ragie_service.search_with_qsr_context(
                query=query,
                qsr_context=qsr_context,
                top_k=3
            )
            
            if not results:
                return f"No manual information found for {equipment}"
            
            # Extract knowledge and update context
            knowledge = []
            for result in results:
                knowledge.append(f"Manual: {result.text}")
                if result.images:
                    ctx.deps.visual_citations.extend([{
                        "type": "image",
                        "url": img["url"],
                        "caption": img.get("caption", f"{equipment} diagram"),
                        "source": result.metadata.get("filename", "Equipment Manual")
                    } for img in result.images])
            
            ctx.deps.equipment_context = equipment
            return "\n\n".join(knowledge)
        
        @self.agent.tool
        async def search_safety_procedures(ctx: RunContext[QSRRunContext], procedure: str) -> str:
            """Search safety procedures and protocols"""
            qsr_context = QSRContext(procedure_type="safety", safety_level="high")
            
            results = await ctx.deps.ragie_service.search_with_qsr_context(
                query=f"safety procedure {procedure}",
                qsr_context=qsr_context,
                top_k=3
            )
            
            if not results:
                return f"No safety procedure found for {procedure}"
            
            # Extract safety knowledge
            safety_info = []
            for result in results:
                safety_info.append(f"Safety Protocol: {result.text}")
                if result.images:
                    ctx.deps.visual_citations.extend([{
                        "type": "image", 
                        "url": img["url"],
                        "caption": img.get("caption", f"Safety: {procedure}"),
                        "source": result.metadata.get("filename", "Safety Manual")
                    } for img in result.images])
            
            ctx.deps.procedure_context = procedure
            ctx.deps.safety_level = "high"
            return "\n\n".join(safety_info)
        
        @self.agent.tool
        async def search_operational_procedures(ctx: RunContext[QSRRunContext], operation: str) -> str:
            """Search operational procedures and best practices"""
            qsr_context = QSRContext(procedure_type=operation.lower())
            
            results = await ctx.deps.ragie_service.search_with_qsr_context(
                query=f"procedure {operation}",
                qsr_context=qsr_context,
                top_k=3
            )
            
            if not results:
                return f"No operational procedure found for {operation}"
            
            # Extract operational knowledge  
            ops_info = []
            for result in results:
                ops_info.append(f"Procedure: {result.text}")
                if result.images:
                    ctx.deps.visual_citations.extend([{
                        "type": "image",
                        "url": img["url"], 
                        "caption": img.get("caption", f"Procedure: {operation}"),
                        "source": result.metadata.get("filename", "Operations Manual")
                    } for img in result.images])
            
            ctx.deps.procedure_context = operation
            return "\n\n".join(ops_info)
        
        @self.agent.tool
        async def get_visual_citations(ctx: RunContext[QSRRunContext], topic: str) -> List[Dict[str, Any]]:
            """Get visual citations (images, videos) for a topic"""
            citations = await ctx.deps.ragie_service.get_visual_citations(topic)
            ctx.deps.visual_citations.extend(citations)
            return citations
    
    async def process_query(
        self, 
        query: str, 
        conversation_id: str = "default",
        equipment_context: Optional[str] = None,
        procedure_context: Optional[str] = None
    ) -> QSRResponse:
        """Process a QSR query with Ragie knowledge enhancement"""
        
        # Create RunContext with Ragie service
        run_context = QSRRunContext(
            ragie_service=enhanced_ragie_service,
            conversation_id=conversation_id,
            equipment_context=equipment_context,
            procedure_context=procedure_context
        )
        
        try:
            # Run the agent with Ragie context
            result = await self.agent.run(query, deps=run_context)
            
            # Enhance response with Ragie data
            response = result.data
            response.visual_citations = run_context.visual_citations
            response.ragie_enhanced = len(run_context.visual_citations) > 0
            
            # Calculate confidence based on Ragie results
            if response.ragie_enhanced:
                response.confidence_score = min(1.0, 0.7 + (len(run_context.visual_citations) * 0.1))
            
            logger.info(f"Enhanced QSR response generated with {len(response.visual_citations)} visual citations")
            return response
            
        except Exception as e:
            logger.error(f"Enhanced QSR agent error: {e}")
            # Fallback response
            return QSRResponse(
                response="I encountered an issue accessing the knowledge base. Please try rephrasing your question.",
                confidence_score=0.3,
                ragie_enhanced=False
            )

# Factory function for creating enhanced agents
async def create_enhanced_qsr_agent() -> EnhancedQSRAgent:
    """Create an enhanced QSR agent instance"""
    agent = EnhancedQSRAgent()
    return agent

# Global instance for backward compatibility
enhanced_qsr_agent = None

async def get_enhanced_qsr_agent() -> EnhancedQSRAgent:
    """Get or create global enhanced QSR agent instance"""
    global enhanced_qsr_agent
    if enhanced_qsr_agent is None:
        enhanced_qsr_agent = await create_enhanced_qsr_agent()
    return enhanced_qsr_agent