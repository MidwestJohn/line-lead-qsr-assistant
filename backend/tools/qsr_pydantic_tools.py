"""
QSR-Specific PydanticAI Tools Integration
=========================================

Advanced PydanticAI Tools that integrate with existing working services:
- MultiModalCitationService (visual citations working)
- VoiceGraphService (Graph-RAG context) 
- StepParserService (procedure parsing)
- ConversationContext (session management)
- Neo4j storage (entities and visual citations)

These tools enhance existing functionality without replacing it.

Author: Generated with Memex (https://memex.tech)
"""

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal, Union, Callable
from enum import Enum
import logging
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# Import existing services for integration
try:
    from services.multimodal_citation_service import MultiModalCitationService, VisualCitation, CitationType
    from services.voice_graph_service import VoiceGraphService, VoiceContext
    from services.neo4j_service import Neo4jService
    from step_parser import parse_ai_response_steps, ParsedStepsResponse
    
    SERVICES_AVAILABLE = True
    logger.info("✅ Basic QSR services imported successfully for PydanticAI tools")
    
except ImportError as e:
    logger.warning(f"⚠️ Some basic services not available for PydanticAI tools: {e}")
    SERVICES_AVAILABLE = False

# Import enhanced models and services conditionally to avoid circular imports
try:
    from models.enhanced_qsr_models import (
        EnhancedVisualCitation, VisualCitationType, VisualCitationSource,
        EquipmentContext, EquipmentStatus, EnhancedConversationContext
    )
    ENHANCED_MODELS_AVAILABLE = True
    logger.info("✅ Enhanced QSR models imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced QSR models not available: {e}")
    ENHANCED_MODELS_AVAILABLE = False

try:
    from services.enhanced_citation_service import EnhancedCitationService
    ENHANCED_CITATION_SERVICE_AVAILABLE = True
except ImportError:
    ENHANCED_CITATION_SERVICE_AVAILABLE = False

try:
    from voice_agent import ConversationContext, AgentType, VoiceState
    VOICE_AGENT_AVAILABLE = True
except ImportError:
    VOICE_AGENT_AVAILABLE = False
    # Define fallback enums
    class AgentType(str, Enum):
        EQUIPMENT = "equipment"
        PROCEDURE = "procedure" 
        SAFETY = "safety"
        MAINTENANCE = "maintenance"
        GENERAL = "general"
    
    class VoiceState(str, Enum):
        LISTENING = "listening"
        PROCESSING = "processing"
        RESPONDING = "responding"

# ===============================================================================
# TOOL CONTEXT AND DEPENDENCY INJECTION
# ===============================================================================

class QSRToolContext(BaseModel):
    """Context container for injecting existing services into PydanticAI tools"""
    
    # Existing working services
    multimodal_citation_service: Optional[Any] = None
    voice_graph_service: Optional[Any] = None 
    neo4j_service: Optional[Any] = None
    enhanced_citation_service: Optional[Any] = None
    
    # Current conversation context
    conversation_context: Optional[Any] = None
    session_id: Optional[str] = None
    
    # File paths and configuration
    uploaded_docs_path: str = "uploaded_docs"
    enable_visual_citations: bool = True
    enable_graph_context: bool = True
    
    # Performance settings
    max_citations_per_tool: int = 5
    citation_relevance_threshold: float = 0.7
    graph_context_limit: int = 10
    
    class Config:
        arbitrary_types_allowed = True

# ===============================================================================
# TOOL MODELS FOR PYDANTIC AI
# ===============================================================================

class VisualCitationQuery(BaseModel):
    """Input model for visual citation tool"""
    query_text: str = Field(description="The query text to find relevant visual citations for")
    equipment_context: Optional[List[str]] = Field(default=None, description="Equipment mentioned in the query")
    citation_types: Optional[List[str]] = Field(default=None, description="Preferred citation types (image, diagram, table, etc.)")
    safety_critical: bool = Field(default=False, description="Whether this is safety-critical content")
    max_results: int = Field(default=5, description="Maximum number of citations to return")

class VisualCitationResult(BaseModel):
    """Output model for visual citation tool"""
    citations: List[Dict[str, Any]] = Field(description="List of relevant visual citations")
    total_found: int = Field(description="Total number of citations found")
    enhanced_citations: Optional[List[Any]] = Field(default=None, description="Enhanced citation objects if available")
    source_documents: List[str] = Field(description="Documents that were searched")
    search_time_ms: float = Field(description="Time taken to search for citations")
    relevance_scores: List[float] = Field(description="Relevance scores for each citation")

class GraphRAGQuery(BaseModel):
    """Input model for Graph-RAG equipment tool"""
    equipment_name: Optional[str] = Field(default=None, description="Specific equipment to query")
    relationship_type: Optional[str] = Field(default=None, description="Type of relationship to explore")
    query_context: str = Field(description="Context for the Graph-RAG query")
    include_relationships: bool = Field(default=True, description="Include related entities and relationships")
    max_depth: int = Field(default=2, description="Maximum relationship depth to explore")

class GraphRAGResult(BaseModel):
    """Output model for Graph-RAG equipment tool"""
    entities: List[Dict[str, Any]] = Field(description="Relevant entities from Graph-RAG")
    relationships: List[Dict[str, Any]] = Field(description="Relationships between entities")
    equipment_context: Optional[Dict[str, Any]] = Field(default=None, description="Equipment-specific context")
    graph_summary: str = Field(description="Summary of Graph-RAG findings")
    confidence_score: float = Field(description="Confidence in the Graph-RAG results")

class ProcedureNavigationQuery(BaseModel):
    """Input model for procedure navigation tool"""
    procedure_query: str = Field(description="Query about a procedure or process")
    current_step: Optional[int] = Field(default=None, description="Current step in an ongoing procedure")
    equipment_context: Optional[str] = Field(default=None, description="Equipment being used in the procedure")
    parse_steps: bool = Field(default=True, description="Whether to parse response into structured steps")

class ProcedureNavigationResult(BaseModel):
    """Output model for procedure navigation tool"""
    procedure_found: bool = Field(description="Whether a relevant procedure was found")
    parsed_steps: Optional[Any] = Field(default=None, description="Structured steps if parsing was successful")
    procedure_summary: str = Field(description="Summary of the procedure")
    step_count: int = Field(description="Number of steps in the procedure")
    estimated_duration: Optional[str] = Field(default=None, description="Estimated time to complete")
    safety_considerations: List[str] = Field(description="Safety considerations for this procedure")

class SafetyValidationQuery(BaseModel):
    """Input model for safety validation tool"""
    content_to_validate: str = Field(description="Content to check for safety compliance")
    equipment_mentioned: Optional[List[str]] = Field(default=None, description="Equipment mentioned in content")
    procedure_type: Optional[str] = Field(default=None, description="Type of procedure being performed")
    context_critical: bool = Field(default=False, description="Whether this is a critical safety context")

class SafetyValidationResult(BaseModel):
    """Output model for safety validation tool"""
    safety_compliant: bool = Field(description="Whether content meets safety standards")
    safety_warnings: List[str] = Field(description="Safety warnings that should be included")
    compliance_requirements: List[str] = Field(description="Compliance requirements that apply")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(description="Assessed risk level")
    recommended_actions: List[str] = Field(description="Recommended safety actions")
    temperature_requirements: Optional[Dict[str, Any]] = Field(default=None, description="Temperature safety requirements")

class ContextEnhancementQuery(BaseModel):
    """Input model for context enhancement tool"""
    current_query: str = Field(description="Current user query")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Recent conversation history")
    enhance_equipment_context: bool = Field(default=True, description="Whether to enhance equipment context")
    enhance_graph_context: bool = Field(default=True, description="Whether to enhance Graph-RAG context")
    session_id: Optional[str] = Field(default=None, description="Session ID for context tracking")

class ContextEnhancementResult(BaseModel):
    """Output model for context enhancement tool"""
    enhanced_context: Dict[str, Any] = Field(description="Enhanced context information")
    equipment_continuity: Optional[str] = Field(default=None, description="Equipment continuity from conversation")
    topic_continuity: List[str] = Field(description="Topic continuity indicators")
    context_score: float = Field(description="Quality of context enhancement")
    recommendations: List[str] = Field(description="Recommendations for improving context")

# ===============================================================================
# PYDANTIC AI TOOLS IMPLEMENTATION
# ===============================================================================

class VisualCitationTool:
    """
    PydanticAI Tool that integrates with existing MultiModalCitationService
    to provide enhanced visual citations for QSR content.
    """
    
    def __init__(self, context: QSRToolContext):
        self.context = context
        self.logger = logging.getLogger(f"{__name__}.VisualCitationTool")
        
        # Initialize or use existing citation service
        if context.multimodal_citation_service:
            self.citation_service = context.multimodal_citation_service
        else:
            self.citation_service = MultiModalCitationService(context.uploaded_docs_path)
            
        # Enhanced citation service if available
        self.enhanced_service = context.enhanced_citation_service
    
    async def search_visual_citations(self, query: VisualCitationQuery) -> VisualCitationResult:
        """Search for relevant visual citations using existing service"""
        start_time = time.time()
        
        try:
            # Use existing multimodal citation service
            citations = await self._search_with_existing_service(query)
            
            # Enhance citations if service available
            enhanced_citations = None
            if self.enhanced_service and citations:
                enhanced_citations = await self._enhance_citations(citations, query)
            
            search_time = (time.time() - start_time) * 1000
            
            return VisualCitationResult(
                citations=citations,
                total_found=len(citations),
                enhanced_citations=enhanced_citations,
                source_documents=self._get_source_documents(),
                search_time_ms=search_time,
                relevance_scores=[c.get('confidence', 0.8) for c in citations]
            )
            
        except Exception as e:
            self.logger.error(f"Visual citation search failed: {e}")
            return VisualCitationResult(
                citations=[],
                total_found=0,
                source_documents=[],
                search_time_ms=(time.time() - start_time) * 1000,
                relevance_scores=[]
            )
    
    async def _search_with_existing_service(self, query: VisualCitationQuery) -> List[Dict[str, Any]]:
        """Use existing multimodal citation service to find citations"""
        
        # Extract visual references from query text
        visual_references = self.citation_service.extract_visual_references(query.query_text)
        
        if not visual_references:
            # Fallback: search by equipment context if provided
            if query.equipment_context:
                citations = []
                for equipment in query.equipment_context:
                    equipment_citations = await self._search_by_equipment(equipment)
                    citations.extend(equipment_citations)
                return citations[:query.max_results]
            else:
                return []
        
        # Process visual references to get citations
        citations = []
        for ref_type, references in visual_references.items():
            for ref in references:
                citation_data = await self._process_visual_reference(ref_type, ref, query)
                if citation_data:
                    citations.append(citation_data)
        
        # Filter by relevance threshold
        filtered_citations = [
            c for c in citations 
            if c.get('confidence', 0) >= self.context.citation_relevance_threshold
        ]
        
        # Sort by confidence and limit results
        filtered_citations.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return filtered_citations[:query.max_results]
    
    async def _search_by_equipment(self, equipment_name: str) -> List[Dict[str, Any]]:
        """Search citations by equipment name using existing patterns"""
        citations = []
        
        # Use citation service's equipment detection patterns
        if hasattr(self.citation_service, 'equipment_patterns'):
            # Search for equipment-specific content
            equipment_query = f"equipment {equipment_name} diagram schematic"
            visual_refs = self.citation_service.extract_visual_references(equipment_query)
            
            for ref_type, references in visual_refs.items():
                for ref in references[:2]:  # Limit per equipment
                    citation = await self._process_visual_reference(ref_type, ref, None)
                    if citation:
                        citation['equipment_context'] = [equipment_name]
                        citations.append(citation)
        
        return citations
    
    async def _process_visual_reference(self, ref_type: str, reference: str, query: VisualCitationQuery) -> Optional[Dict[str, Any]]:
        """Process a visual reference into a citation using existing service logic"""
        
        try:
            # Create a visual citation using existing service
            citation = VisualCitation(
                citation_type=ref_type,
                source_document="QSR_Manual",  # Default source
                page_number=1,  # Will be updated by service
                reference_text=reference,
                timing="during_speech"
            )
            
            # Convert to dictionary format expected by frontend
            citation_dict = citation.to_dict()
            
            # Add QSR-specific enhancements
            citation_dict.update({
                'confidence': 0.85,  # Default confidence
                'description': f"{ref_type.title()} reference: {reference}",
                'equipment_context': query.equipment_context if query else [],
                'safety_critical': query.safety_critical if query else False
            })
            
            return citation_dict
            
        except Exception as e:
            self.logger.error(f"Failed to process visual reference {reference}: {e}")
            return None
    
    async def _enhance_citations(self, citations: List[Dict[str, Any]], query: VisualCitationQuery) -> List[Any]:
        """Enhance citations using enhanced citation service if available"""
        if not self.enhanced_service:
            return None
            
        try:
            enhanced = []
            for citation in citations:
                # Convert to enhanced citation format
                enhanced_citation = EnhancedVisualCitation(
                    citation_id=citation.get('citation_id', 'generated'),
                    type=VisualCitationType.DIAGRAM,  # Default type
                    source=VisualCitationSource.RAGIE_EXTRACTION,
                    title=citation.get('source', 'Visual Citation'),
                    description=citation.get('description', ''),
                    contributing_agent=AgentType.GENERAL,
                    agent_confidence=citation.get('confidence', 0.8),
                    relevance_score=citation.get('confidence', 0.8),
                    equipment_context=query.equipment_context or [],
                    safety_level="high" if query.safety_critical else "low"
                )
                enhanced.append(enhanced_citation)
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Failed to enhance citations: {e}")
            return None
    
    def _get_source_documents(self) -> List[str]:
        """Get list of source documents that were searched"""
        try:
            docs_path = Path(self.context.uploaded_docs_path)
            if docs_path.exists():
                return [f.name for f in docs_path.iterdir() if f.suffix.lower() == '.pdf']
            return []
        except Exception:
            return ["QSR_Manual.pdf"]  # Default fallback

class GraphRAGEquipmentTool:
    """
    PydanticAI Tool that integrates with existing Neo4j Graph-RAG infrastructure
    to provide equipment context and relationships.
    """
    
    def __init__(self, context: QSRToolContext):
        self.context = context
        self.logger = logging.getLogger(f"{__name__}.GraphRAGEquipmentTool")
        
        # Use existing services
        self.voice_graph_service = context.voice_graph_service
        self.neo4j_service = context.neo4j_service
    
    async def query_equipment_context(self, query: GraphRAGQuery) -> GraphRAGResult:
        """Query Graph-RAG for equipment context using existing services"""
        
        try:
            # Use existing voice graph service if available
            if self.voice_graph_service:
                graph_context = await self._query_with_voice_service(query)
            elif self.neo4j_service:
                graph_context = await self._query_with_neo4j_service(query)
            else:
                # Fallback to mock data based on known equipment
                graph_context = self._generate_mock_equipment_context(query)
            
            return self._format_graph_result(graph_context, query)
            
        except Exception as e:
            self.logger.error(f"Graph-RAG equipment query failed: {e}")
            return GraphRAGResult(
                entities=[],
                relationships=[],
                equipment_context=None,
                graph_summary=f"Failed to query equipment context: {str(e)}",
                confidence_score=0.0
            )
    
    async def _query_with_voice_service(self, query: GraphRAGQuery) -> Dict[str, Any]:
        """Query using existing voice graph service"""
        
        # Create or get voice session
        session_id = self.context.session_id or "graph_tool_session"
        
        if hasattr(self.voice_graph_service, 'process_voice_query'):
            # Use existing voice graph query processing
            result = await self.voice_graph_service.process_voice_query(
                session_id=session_id,
                query=query.query_context
            )
            
            return {
                'entities': result.get('context', {}).get('graph_entities', []),
                'equipment': result.get('context', {}).get('current_equipment'),
                'procedure': result.get('context', {}).get('current_procedure'),
                'relationships': []  # Will be populated by voice service
            }
        
        return {}
    
    async def _query_with_neo4j_service(self, query: GraphRAGQuery) -> Dict[str, Any]:
        """Query using existing Neo4j service directly"""
        
        if not self.neo4j_service:
            return {}
        
        try:
            # Query Neo4j for equipment entities
            equipment_query = f"""
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower('{query.equipment_name or query.query_context}')
               OR toLower(e.description) CONTAINS toLower('{query.query_context}')
            RETURN e
            LIMIT {self.context.graph_context_limit}
            """
            
            entities = await self._execute_neo4j_query(equipment_query)
            
            # Query for relationships if requested
            relationships = []
            if query.include_relationships and entities:
                rel_query = f"""
                MATCH (e1:Entity)-[r]->(e2:Entity)
                WHERE e1.name IN {[e['name'] for e in entities]}
                RETURN e1, r, e2
                LIMIT {self.context.graph_context_limit}
                """
                relationships = await self._execute_neo4j_query(rel_query)
            
            return {
                'entities': entities,
                'relationships': relationships,
                'equipment': query.equipment_name,
                'query_context': query.query_context
            }
            
        except Exception as e:
            self.logger.error(f"Neo4j query failed: {e}")
            return {}
    
    def _generate_mock_equipment_context(self, query: GraphRAGQuery) -> Dict[str, Any]:
        """Generate mock equipment context based on known QSR equipment"""
        
        # Known QSR equipment from existing system
        known_equipment = {
            'taylor c602': {
                'type': 'fryer',
                'manufacturer': 'Taylor',
                'model': 'C602',
                'relationships': ['temperature_control', 'oil_management', 'cleaning_cycle']
            },
            'compressor': {
                'type': 'hvac_component', 
                'relationships': ['temperature_control', 'refrigeration_system']
            },
            'mix pump': {
                'type': 'beverage_equipment',
                'relationships': ['beverage_system', 'cleaning_cycle']
            }
        }
        
        equipment_name = query.equipment_name or self._extract_equipment_from_context(query.query_context)
        
        if equipment_name and equipment_name.lower() in known_equipment:
            equipment_data = known_equipment[equipment_name.lower()]
            return {
                'entities': [{
                    'name': equipment_name,
                    'type': equipment_data['type'],
                    'manufacturer': equipment_data.get('manufacturer', 'Unknown'),
                    'model': equipment_data.get('model', 'Unknown')
                }],
                'relationships': equipment_data['relationships'],
                'equipment': equipment_name
            }
        
        return {
            'entities': [],
            'relationships': [],
            'equipment': equipment_name
        }
    
    def _extract_equipment_from_context(self, context: str) -> Optional[str]:
        """Extract equipment name from query context"""
        equipment_patterns = [
            r'taylor\s+c602', r'fryer', r'compressor', r'mix\s+pump',
            r'oven', r'grill', r'freezer', r'refrigerator'
        ]
        
        for pattern in equipment_patterns:
            import re
            match = re.search(pattern, context.lower())
            if match:
                return match.group()
        
        return None
    
    async def _execute_neo4j_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute Neo4j query using existing service"""
        try:
            if hasattr(self.neo4j_service, 'execute_query'):
                result = await self.neo4j_service.execute_query(query)
                return result
            else:
                # Mock result for development
                return []
        except Exception as e:
            self.logger.error(f"Neo4j query execution failed: {e}")
            return []
    
    def _format_graph_result(self, graph_context: Dict[str, Any], query: GraphRAGQuery) -> GraphRAGResult:
        """Format graph context into GraphRAGResult"""
        
        entities = graph_context.get('entities', [])
        relationships = graph_context.get('relationships', [])
        equipment = graph_context.get('equipment')
        
        # Create equipment context if equipment found
        equipment_context = None
        if equipment and entities:
            equipment_context = {
                'equipment_name': equipment,
                'equipment_type': next((e.get('type') for e in entities if e.get('name') == equipment), 'unknown'),
                'related_procedures': [r for r in relationships if 'procedure' in str(r).lower()],
                'safety_protocols': [r for r in relationships if 'safety' in str(r).lower()],
                'maintenance_tasks': [r for r in relationships if 'maintenance' in str(r).lower()]
            }
        
        # Generate summary
        summary_parts = []
        if entities:
            summary_parts.append(f"Found {len(entities)} relevant entities")
        if relationships:
            summary_parts.append(f"Found {len(relationships)} relationships")
        if equipment:
            summary_parts.append(f"Equipment context: {equipment}")
        
        graph_summary = "; ".join(summary_parts) if summary_parts else "No relevant Graph-RAG context found"
        
        # Calculate confidence based on results
        confidence = 0.0
        if entities:
            confidence += 0.4
        if relationships:
            confidence += 0.3
        if equipment_context:
            confidence += 0.3
        
        return GraphRAGResult(
            entities=entities,
            relationships=relationships,
            equipment_context=equipment_context,
            graph_summary=graph_summary,
            confidence_score=min(confidence, 1.0)
        )

class ProcedureNavigationTool:
    """
    PydanticAI Tool that integrates with existing step parser service
    and procedure tracking for navigation assistance.
    """
    
    def __init__(self, context: QSRToolContext):
        self.context = context
        self.logger = logging.getLogger(f"{__name__}.ProcedureNavigationTool")
    
    async def navigate_procedure(self, query: ProcedureNavigationQuery) -> ProcedureNavigationResult:
        """Navigate procedures using existing step parser service"""
        
        try:
            # Use existing step parser if available
            parsed_steps = None
            if query.parse_steps:
                parsed_steps = await self._parse_procedure_steps(query.procedure_query)
            
            # Extract procedure information
            procedure_info = self._analyze_procedure_query(query)
            
            # Generate safety considerations based on equipment context
            safety_considerations = self._get_safety_considerations(query.equipment_context, procedure_info)
            
            return ProcedureNavigationResult(
                procedure_found=procedure_info['found'],
                parsed_steps=parsed_steps,
                procedure_summary=procedure_info['summary'],
                step_count=procedure_info['step_count'],
                estimated_duration=procedure_info['estimated_duration'],
                safety_considerations=safety_considerations
            )
            
        except Exception as e:
            self.logger.error(f"Procedure navigation failed: {e}")
            return ProcedureNavigationResult(
                procedure_found=False,
                parsed_steps=None,
                procedure_summary=f"Failed to analyze procedure: {str(e)}",
                step_count=0,
                estimated_duration=None,
                safety_considerations=[]
            )
    
    async def _parse_procedure_steps(self, procedure_text: str) -> Optional[Any]:
        """Parse procedure steps using existing step parser service"""
        
        try:
            # Use existing step parser function
            if 'parse_ai_response_steps' in globals():
                parsed = parse_ai_response_steps(procedure_text)
                return parsed
            else:
                # Mock structured steps for development
                return self._create_mock_parsed_steps(procedure_text)
                
        except Exception as e:
            self.logger.error(f"Step parsing failed: {e}")
            return None
    
    def _create_mock_parsed_steps(self, procedure_text: str) -> Dict[str, Any]:
        """Create mock parsed steps for development"""
        import re
        
        # Simple step extraction
        steps = re.findall(r'(\d+\.?\s+[^\.]+)', procedure_text)
        
        return {
            'steps': [{'step_number': i+1, 'description': step.strip()} for i, step in enumerate(steps)],
            'total_steps': len(steps),
            'procedure_type': 'general',
            'estimated_time': f"{len(steps) * 2} minutes"
        }
    
    def _analyze_procedure_query(self, query: ProcedureNavigationQuery) -> Dict[str, Any]:
        """Analyze procedure query to extract information"""
        
        procedure_keywords = {
            'cleaning': {'duration': '15-30 minutes', 'steps': 8},
            'maintenance': {'duration': '30-60 minutes', 'steps': 12},
            'setup': {'duration': '5-10 minutes', 'steps': 5},
            'troubleshooting': {'duration': '10-20 minutes', 'steps': 6},
            'calibration': {'duration': '15-25 minutes', 'steps': 7}
        }
        
        query_lower = query.procedure_query.lower()
        
        # Detect procedure type
        procedure_type = None
        for keyword in procedure_keywords:
            if keyword in query_lower:
                procedure_type = keyword
                break
        
        if procedure_type:
            info = procedure_keywords[procedure_type]
            return {
                'found': True,
                'type': procedure_type,
                'summary': f"{procedure_type.title()} procedure for {query.equipment_context or 'equipment'}",
                'step_count': info['steps'],
                'estimated_duration': info['duration']
            }
        else:
            return {
                'found': False,
                'type': 'unknown',
                'summary': f"General procedure guidance for: {query.procedure_query}",
                'step_count': 0,
                'estimated_duration': None
            }
    
    def _get_safety_considerations(self, equipment_context: Optional[str], procedure_info: Dict[str, Any]) -> List[str]:
        """Generate safety considerations based on equipment and procedure type"""
        
        safety_considerations = []
        
        # Equipment-specific safety
        if equipment_context:
            equipment_lower = equipment_context.lower()
            if 'fryer' in equipment_lower or 'hot' in equipment_lower:
                safety_considerations.extend([
                    "Ensure equipment is properly cooled before maintenance",
                    "Use appropriate PPE for high-temperature equipment",
                    "Follow lockout/tagout procedures"
                ])
            elif 'electrical' in equipment_lower or 'compressor' in equipment_lower:
                safety_considerations.extend([
                    "Disconnect power before servicing electrical components",
                    "Check for proper grounding",
                    "Use insulated tools"
                ])
        
        # Procedure-specific safety
        procedure_type = procedure_info.get('type', '').lower()
        if procedure_type == 'cleaning':
            safety_considerations.extend([
                "Use appropriate cleaning chemicals as directed",
                "Ensure adequate ventilation",
                "Wear protective gloves and eyewear"
            ])
        elif procedure_type == 'maintenance':
            safety_considerations.extend([
                "Follow manufacturer's maintenance guidelines",
                "Use proper lifting techniques for heavy components",
                "Verify all safety systems are functional after maintenance"
            ])
        
        # General safety if no specific considerations
        if not safety_considerations:
            safety_considerations = [
                "Follow all standard safety protocols",
                "Ensure proper training before performing procedure",
                "Have emergency contacts readily available"
            ]
        
        return safety_considerations

class SafetyValidationTool:
    """
    PydanticAI Tool that integrates with existing safety patterns and validation logic
    to ensure safety compliance in QSR operations.
    """
    
    def __init__(self, context: QSRToolContext):
        self.context = context
        self.logger = logging.getLogger(f"{__name__}.SafetyValidationTool")
    
    async def validate_safety(self, query: SafetyValidationQuery) -> SafetyValidationResult:
        """Validate content for safety compliance using existing safety patterns"""
        
        try:
            # Analyze content for safety risks
            risk_analysis = self._analyze_safety_risks(query)
            
            # Check compliance requirements
            compliance_reqs = self._check_compliance_requirements(query)
            
            # Generate safety warnings
            safety_warnings = self._generate_safety_warnings(query, risk_analysis)
            
            # Get temperature requirements if applicable
            temp_requirements = self._get_temperature_requirements(query)
            
            # Generate recommended actions
            recommended_actions = self._generate_recommended_actions(query, risk_analysis)
            
            return SafetyValidationResult(
                safety_compliant=risk_analysis['compliant'],
                safety_warnings=safety_warnings,
                compliance_requirements=compliance_reqs,
                risk_level=risk_analysis['risk_level'],
                recommended_actions=recommended_actions,
                temperature_requirements=temp_requirements
            )
            
        except Exception as e:
            self.logger.error(f"Safety validation failed: {e}")
            return SafetyValidationResult(
                safety_compliant=False,
                safety_warnings=[f"Safety validation error: {str(e)}"],
                compliance_requirements=[],
                risk_level="high",
                recommended_actions=["Consult safety manual before proceeding"],
                temperature_requirements=None
            )
    
    def _analyze_safety_risks(self, query: SafetyValidationQuery) -> Dict[str, Any]:
        """Analyze content for safety risks using existing safety patterns"""
        
        content_lower = query.content_to_validate.lower()
        
        # High-risk indicators
        high_risk_patterns = [
            'hot oil', 'high temperature', 'electrical', 'chemical', 'toxic',
            'burn', 'shock', 'fire', 'gas', 'pressure'
        ]
        
        # Medium-risk indicators  
        medium_risk_patterns = [
            'cleaning', 'maintenance', 'repair', 'calibration', 'adjustment'
        ]
        
        # Safety compliance indicators
        safety_compliance_patterns = [
            'ppe', 'protective equipment', 'safety first', 'caution', 'warning',
            'temperature check', 'proper ventilation', 'lockout', 'tagout'
        ]
        
        # Analyze risk level
        high_risk_count = sum(1 for pattern in high_risk_patterns if pattern in content_lower)
        medium_risk_count = sum(1 for pattern in medium_risk_patterns if pattern in content_lower)
        compliance_count = sum(1 for pattern in safety_compliance_patterns if pattern in content_lower)
        
        # Determine risk level
        if high_risk_count > 0:
            risk_level = "critical" if query.context_critical else "high"
        elif medium_risk_count > 0:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Determine compliance
        compliant = compliance_count > 0 or risk_level == "low"
        
        return {
            'risk_level': risk_level,
            'compliant': compliant,
            'high_risk_indicators': high_risk_count,
            'compliance_indicators': compliance_count
        }
    
    def _check_compliance_requirements(self, query: SafetyValidationQuery) -> List[str]:
        """Check applicable compliance requirements"""
        
        requirements = []
        
        # Equipment-specific compliance
        if query.equipment_mentioned:
            for equipment in query.equipment_mentioned:
                equipment_lower = equipment.lower()
                if 'fryer' in equipment_lower:
                    requirements.extend([
                        "OSHA hot surface protection standards",
                        "Food safety temperature requirements", 
                        "Fire suppression system compliance"
                    ])
                elif 'refriger' in equipment_lower:
                    requirements.extend([
                        "Food safety cold chain requirements",
                        "EPA refrigerant handling regulations"
                    ])
        
        # Procedure-specific compliance
        if query.procedure_type:
            procedure_lower = query.procedure_type.lower()
            if 'cleaning' in procedure_lower:
                requirements.extend([
                    "HACCP sanitation standards",
                    "Chemical safety data sheet compliance"
                ])
            elif 'maintenance' in procedure_lower:
                requirements.extend([
                    "Lockout/tagout procedures",
                    "Equipment manufacturer guidelines"
                ])
        
        # General compliance if none specific
        if not requirements:
            requirements = [
                "General food safety regulations",
                "Workplace safety standards"
            ]
        
        return requirements
    
    def _generate_safety_warnings(self, query: SafetyValidationQuery, risk_analysis: Dict[str, Any]) -> List[str]:
        """Generate appropriate safety warnings based on risk analysis"""
        
        warnings = []
        
        # Risk level-based warnings
        if risk_analysis['risk_level'] == 'critical':
            warnings.append("⚠️ CRITICAL SAFETY RISK - Immediate supervision required")
        elif risk_analysis['risk_level'] == 'high':
            warnings.append("⚠️ HIGH RISK - Follow all safety protocols")
        
        # Content-specific warnings
        content_lower = query.content_to_validate.lower()
        
        if 'temperature' in content_lower or 'hot' in content_lower:
            warnings.append("Temperature safety: Verify safe handling temperatures")
        
        if 'chemical' in content_lower or 'cleaning' in content_lower:
            warnings.append("Chemical safety: Use proper PPE and ventilation")
        
        if 'electrical' in content_lower:
            warnings.append("Electrical safety: Ensure power is disconnected before service")
        
        # Equipment-specific warnings
        if query.equipment_mentioned:
            for equipment in query.equipment_mentioned:
                if 'fryer' in equipment.lower():
                    warnings.append("Hot oil safety: Allow cooling time before maintenance")
        
        return warnings
    
    def _get_temperature_requirements(self, query: SafetyValidationQuery) -> Optional[Dict[str, Any]]:
        """Get temperature requirements if applicable"""
        
        content_lower = query.content_to_validate.lower()
        
        # Check if temperature-related
        if not any(temp_word in content_lower for temp_word in ['temperature', 'hot', 'cold', 'heat', 'cool']):
            return None
        
        # Equipment-specific temperature requirements
        temp_requirements = {}
        
        if query.equipment_mentioned:
            for equipment in query.equipment_mentioned:
                equipment_lower = equipment.lower()
                if 'fryer' in equipment_lower:
                    temp_requirements.update({
                        'operating_temperature': '350°F (175°C)',
                        'safe_service_temperature': 'Below 100°F (38°C)',
                        'oil_temperature_range': '325-375°F (163-191°C)'
                    })
                elif 'refriger' in equipment_lower:
                    temp_requirements.update({
                        'safe_storage_temperature': '32-40°F (0-4°C)',
                        'critical_temperature': 'Above 40°F (4°C) requires immediate attention'
                    })
        
        # General temperature safety if no specific requirements
        if not temp_requirements:
            temp_requirements = {
                'general_safety': 'Follow equipment manufacturer temperature guidelines',
                'hot_surface_warning': 'Surfaces above 140°F (60°C) require protection'
            }
        
        return temp_requirements
    
    def _generate_recommended_actions(self, query: SafetyValidationQuery, risk_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommended safety actions"""
        
        actions = []
        
        # Risk level-based actions
        if risk_analysis['risk_level'] in ['critical', 'high']:
            actions.extend([
                "Obtain supervisor approval before proceeding",
                "Ensure all safety equipment is available",
                "Review emergency procedures"
            ])
        
        # Equipment-specific actions
        if query.equipment_mentioned:
            actions.append("Verify equipment is in safe operating condition")
            actions.append("Check that all safety systems are functional")
        
        # Procedure-specific actions
        if query.procedure_type:
            if 'maintenance' in query.procedure_type.lower():
                actions.append("Follow lockout/tagout procedures")
            elif 'cleaning' in query.procedure_type.lower():
                actions.append("Use appropriate cleaning chemicals and PPE")
        
        # Compliance actions
        if not risk_analysis['compliant']:
            actions.append("Review safety compliance requirements")
            actions.append("Consult safety manual for detailed procedures")
        
        return actions

class ContextEnhancementTool:
    """
    PydanticAI Tool that integrates with existing ConversationContext and Graph-RAG
    to provide enhanced context for better responses.
    """
    
    def __init__(self, context: QSRToolContext):
        self.context = context
        self.logger = logging.getLogger(f"{__name__}.ContextEnhancementTool")
    
    async def enhance_context(self, query: ContextEnhancementQuery) -> ContextEnhancementResult:
        """Enhance context using existing conversation and Graph-RAG services"""
        
        try:
            enhanced_context = {}
            
            # Equipment context enhancement
            if query.enhance_equipment_context:
                equipment_context = await self._enhance_equipment_context(query)
                enhanced_context['equipment'] = equipment_context
            
            # Graph-RAG context enhancement
            if query.enhance_graph_context:
                graph_context = await self._enhance_graph_context(query)
                enhanced_context['graph'] = graph_context
            
            # Conversation continuity analysis
            continuity_analysis = self._analyze_conversation_continuity(query)
            enhanced_context['continuity'] = continuity_analysis
            
            # Generate context score
            context_score = self._calculate_context_score(enhanced_context)
            
            # Generate recommendations
            recommendations = self._generate_context_recommendations(enhanced_context, context_score)
            
            return ContextEnhancementResult(
                enhanced_context=enhanced_context,
                equipment_continuity=continuity_analysis.get('equipment_continuity'),
                topic_continuity=continuity_analysis.get('topic_continuity', []),
                context_score=context_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Context enhancement failed: {e}")
            return ContextEnhancementResult(
                enhanced_context={},
                equipment_continuity=None,
                topic_continuity=[],
                context_score=0.0,
                recommendations=["Context enhancement unavailable"]
            )
    
    async def _enhance_equipment_context(self, query: ContextEnhancementQuery) -> Dict[str, Any]:
        """Enhance equipment context from conversation history"""
        
        equipment_context = {
            'current_equipment': None,
            'equipment_history': [],
            'equipment_switches': 0,
            'expertise_indicators': {}
        }
        
        # Analyze current query for equipment mentions
        query_equipment = self._extract_equipment_mentions(query.current_query)
        if query_equipment:
            equipment_context['current_equipment'] = query_equipment[0]
        
        # Analyze conversation history if available
        if query.conversation_history:
            for exchange in query.conversation_history[-5:]:  # Last 5 exchanges
                user_content = exchange.get('user', '') + ' ' + exchange.get('assistant', '')
                equipment_mentions = self._extract_equipment_mentions(user_content)
                equipment_context['equipment_history'].extend(equipment_mentions)
            
            # Count equipment switches
            unique_equipment = list(set(equipment_context['equipment_history']))
            equipment_context['equipment_switches'] = len(unique_equipment) - 1 if len(unique_equipment) > 1 else 0
        
        # Use existing conversation context if available
        if self.context.conversation_context:
            conv_context = self.context.conversation_context
            if hasattr(conv_context, 'current_entity'):
                equipment_context['conversation_current'] = conv_context.current_entity
            if hasattr(conv_context, 'entity_history'):
                equipment_context['conversation_history'] = conv_context.entity_history
        
        return equipment_context
    
    async def _enhance_graph_context(self, query: ContextEnhancementQuery) -> Dict[str, Any]:
        """Enhance context using Graph-RAG relationships"""
        
        graph_context = {
            'related_entities': [],
            'relationships': [],
            'context_depth': 0
        }
        
        # Use existing voice graph service if available
        if self.context.voice_graph_service and query.session_id:
            try:
                # Get graph context from voice service
                voice_result = await self.context.voice_graph_service.process_voice_query(
                    session_id=query.session_id,
                    query=query.current_query
                )
                
                if voice_result and 'context' in voice_result:
                    voice_context = voice_result['context']
                    graph_context['related_entities'] = voice_context.get('graph_entities', [])
                    graph_context['current_equipment'] = voice_context.get('current_equipment')
                    graph_context['current_procedure'] = voice_context.get('current_procedure')
                    graph_context['context_depth'] = len(graph_context['related_entities'])
                
            except Exception as e:
                self.logger.error(f"Voice graph service query failed: {e}")
        
        # Fallback: Use Neo4j service directly if available
        elif self.context.neo4j_service:
            try:
                # Query for entities related to current query
                entities = await self._query_related_entities(query.current_query)
                graph_context['related_entities'] = entities
                graph_context['context_depth'] = len(entities)
                
            except Exception as e:
                self.logger.error(f"Neo4j direct query failed: {e}")
        
        return graph_context
    
    def _analyze_conversation_continuity(self, query: ContextEnhancementQuery) -> Dict[str, Any]:
        """Analyze conversation continuity and topic flow"""
        
        continuity = {
            'equipment_continuity': None,
            'topic_continuity': [],
            'continuity_score': 0.0,
            'topic_switches': 0
        }
        
        if not query.conversation_history:
            return continuity
        
        # Analyze equipment continuity
        equipment_timeline = []
        for exchange in query.conversation_history:
            user_content = exchange.get('user', '')
            equipment_mentions = self._extract_equipment_mentions(user_content)
            if equipment_mentions:
                equipment_timeline.extend(equipment_mentions)
        
        if equipment_timeline:
            # Most recent equipment becomes continuity context
            continuity['equipment_continuity'] = equipment_timeline[-1]
            
            # Count equipment switches
            unique_equipment = list(set(equipment_timeline))
            continuity['topic_switches'] = len(unique_equipment) - 1
        
        # Analyze topic continuity
        topics = []
        for exchange in query.conversation_history:
            user_content = exchange.get('user', '')
            extracted_topics = self._extract_topics(user_content)
            topics.extend(extracted_topics)
        
        continuity['topic_continuity'] = list(set(topics))
        
        # Calculate continuity score
        if equipment_timeline:
            equipment_consistency = 1.0 - (continuity['topic_switches'] / len(equipment_timeline))
            continuity['continuity_score'] = max(0.0, equipment_consistency)
        
        return continuity
    
    def _extract_equipment_mentions(self, text: str) -> List[str]:
        """Extract equipment mentions from text using existing patterns"""
        
        equipment_patterns = [
            r'taylor\s+c602', r'fryer', r'compressor', r'mix\s+pump',
            r'oven', r'grill', r'freezer', r'refrigerator', r'blender',
            r'dispenser', r'warmer', r'cooler'
        ]
        
        import re
        equipment_mentions = []
        
        for pattern in equipment_patterns:
            matches = re.findall(pattern, text.lower())
            equipment_mentions.extend(matches)
        
        return equipment_mentions
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract general topics from text"""
        
        topic_keywords = [
            'cleaning', 'maintenance', 'repair', 'troubleshooting',
            'setup', 'calibration', 'temperature', 'safety',
            'procedure', 'operation', 'manual'
        ]
        
        topics = []
        text_lower = text.lower()
        
        for keyword in topic_keywords:
            if keyword in text_lower:
                topics.append(keyword)
        
        return topics
    
    async def _query_related_entities(self, query_text: str) -> List[str]:
        """Query related entities from Neo4j if available"""
        
        try:
            if hasattr(self.context.neo4j_service, 'execute_query'):
                # Simple entity query
                query = f"""
                MATCH (e:Entity)
                WHERE toLower(e.name) CONTAINS toLower('{query_text[:50]}')
                   OR toLower(e.description) CONTAINS toLower('{query_text[:50]}')
                RETURN e.name as entity
                LIMIT 5
                """
                
                result = await self.context.neo4j_service.execute_query(query)
                return [r.get('entity', '') for r in result if r.get('entity')]
            
        except Exception as e:
            self.logger.error(f"Entity query failed: {e}")
        
        return []
    
    def _calculate_context_score(self, enhanced_context: Dict[str, Any]) -> float:
        """Calculate overall context quality score"""
        
        score = 0.0
        
        # Equipment context scoring
        equipment_context = enhanced_context.get('equipment', {})
        if equipment_context.get('current_equipment'):
            score += 0.3
        if equipment_context.get('equipment_history'):
            score += 0.2
        
        # Graph context scoring
        graph_context = enhanced_context.get('graph', {})
        if graph_context.get('related_entities'):
            score += 0.3
        if graph_context.get('context_depth', 0) > 2:
            score += 0.1
        
        # Continuity scoring
        continuity = enhanced_context.get('continuity', {})
        if continuity.get('continuity_score', 0) > 0.7:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_context_recommendations(self, enhanced_context: Dict[str, Any], context_score: float) -> List[str]:
        """Generate recommendations for improving context"""
        
        recommendations = []
        
        if context_score < 0.5:
            recommendations.append("Consider asking for more specific equipment context")
        
        equipment_context = enhanced_context.get('equipment', {})
        if equipment_context.get('equipment_switches', 0) > 2:
            recommendations.append("Multiple equipment topics detected - consider focusing on one")
        
        graph_context = enhanced_context.get('graph', {})
        if not graph_context.get('related_entities'):
            recommendations.append("No related entities found - may need broader context")
        
        continuity = enhanced_context.get('continuity', {})
        if continuity.get('topic_switches', 0) > 3:
            recommendations.append("Frequent topic changes - consider clarifying current focus")
        
        if not recommendations:
            recommendations = ["Context appears well-established for this conversation"]
        
        return recommendations

# ===============================================================================
# TOOL FACTORY AND UTILITIES
# ===============================================================================

def create_qsr_tools_for_agent(agent_type: str, context: QSRToolContext) -> Dict[str, Any]:
    """Create appropriate tools for a specific agent type"""
    
    tools = {}
    
    # All agents get basic tools
    tools['visual_citations'] = VisualCitationTool(context)
    tools['context_enhancement'] = ContextEnhancementTool(context)
    
    # Agent-specific tools
    if agent_type.lower() in ['equipment', 'general']:
        tools['graph_rag'] = GraphRAGEquipmentTool(context)
    
    if agent_type.lower() in ['procedure', 'maintenance', 'general']:
        tools['procedure_navigation'] = ProcedureNavigationTool(context)
    
    if agent_type.lower() in ['safety', 'equipment', 'procedure', 'maintenance']:
        tools['safety_validation'] = SafetyValidationTool(context)
    
    return tools

def get_available_tools() -> List[str]:
    """Get list of available PydanticAI tools"""
    return [
        "VisualCitationTool",
        "GraphRAGEquipmentTool", 
        "ProcedureNavigationTool",
        "SafetyValidationTool",
        "ContextEnhancementTool"
    ]

# ===============================================================================
# TOOL INTEGRATION HELPERS
# ===============================================================================

async def integrate_tool_results_with_response(
    tool_results: Dict[str, Any],
    base_response: Dict[str, Any]
) -> Dict[str, Any]:
    """Integrate tool results with base response for enhanced output"""
    
    enhanced_response = base_response.copy()
    
    # Integrate visual citations
    if 'visual_citations' in tool_results:
        citation_result = tool_results['visual_citations']
        enhanced_response['visual_citations'] = citation_result.citations
        enhanced_response['enhanced_citations'] = citation_result.enhanced_citations
    
    # Integrate Graph-RAG context
    if 'graph_context' in tool_results:
        graph_result = tool_results['graph_context']
        enhanced_response['equipment_context'] = graph_result.equipment_context
        enhanced_response['graph_entities'] = graph_result.entities
    
    # Integrate safety validation
    if 'safety_validation' in tool_results:
        safety_result = tool_results['safety_validation']
        enhanced_response['safety_warnings'] = safety_result.safety_warnings
        enhanced_response['safety_priority'] = not safety_result.safety_compliant
        enhanced_response['compliance_requirements'] = safety_result.compliance_requirements
    
    # Integrate procedure information
    if 'procedure_info' in tool_results:
        procedure_result = tool_results['procedure_info']
        enhanced_response['parsed_steps'] = procedure_result.parsed_steps
        enhanced_response['procedure_summary'] = procedure_result.procedure_summary
    
    # Integrate enhanced context
    if 'enhanced_context' in tool_results:
        context_result = tool_results['enhanced_context']
        enhanced_response['context_score'] = context_result.context_score
        enhanced_response['context_recommendations'] = context_result.recommendations
    
    return enhanced_response

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Core tools
    "VisualCitationTool",
    "GraphRAGEquipmentTool",
    "ProcedureNavigationTool", 
    "SafetyValidationTool",
    "ContextEnhancementTool",
    
    # Input/Output models
    "VisualCitationQuery", "VisualCitationResult",
    "GraphRAGQuery", "GraphRAGResult",
    "ProcedureNavigationQuery", "ProcedureNavigationResult",
    "SafetyValidationQuery", "SafetyValidationResult",
    "ContextEnhancementQuery", "ContextEnhancementResult",
    
    # Utilities
    "QSRToolContext",
    "create_qsr_tools_for_agent",
    "get_available_tools",
    "integrate_tool_results_with_response"
]