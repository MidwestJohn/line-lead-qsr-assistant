#!/usr/bin/env python3
"""
QSR Support Agent with PydanticAI Tools
=======================================

Type-safe PydanticAI agent implementing the comprehensive philosophy:
- @support_agent.tool patterns for structured interactions
- QSR-optimized dependency injection
- Structured responses with safety warnings, steps, equipment
- Production-ready error handling and fallbacks

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# PydanticAI imports
try:
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.models.openai import OpenAIModel
    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    PYDANTIC_AI_AVAILABLE = False
    logging.warning(f"PydanticAI not available: {e}")
    # Create placeholder classes
    class Agent:
        pass
    class RunContext:
        pass
    class OpenAIModel:
        pass

# Import our QSR models and services
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.qsr_models import (
        QSRTaskResponse, QSRSearchRequest, QSRSearchResult,
        EquipmentReference, SafetyWarning, ProcedureStep
    )
    from models.qsr_response import CleanedQSRResponse, EnhancedQSRTaskResponse
    from services.qsr_ragie_service import qsr_ragie_service
    from services.response_processor import response_cleaner
    from utils.stepcard_formatter import stepcard_formatter
    QSR_IMPORTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"QSR imports not available: {e}")
    QSR_IMPORTS_AVAILABLE = False
    # Create placeholder classes to prevent crashes
    class QSRTaskResponse:
        pass
    class QSRSearchRequest:
        pass
    class CleanedQSRResponse:
        pass
    class EnhancedQSRTaskResponse:
        pass
    qsr_ragie_service = None
    response_cleaner = None
    stepcard_formatter = None

logger = logging.getLogger(__name__)

@dataclass
class QSRDependencies:
    """
    QSR-specific dependencies for PydanticAI RunContext
    Following the philosophy's dependency injection pattern
    """
    ragie_service: Any  # QSRRagieService instance
    user_context: Dict[str, Any]  # User session and preferences
    restaurant_config: Dict[str, Any]  # Restaurant-specific configuration
    safety_level: str = "high"  # Default safety level for responses
    
    def __post_init__(self):
        """Validate dependencies on initialization"""
        if not self.ragie_service or not self.ragie_service.is_available():
            logger.warning("Ragie service not available in dependencies")
        
        # Set default restaurant config if not provided
        if not self.restaurant_config:
            self.restaurant_config = {
                "equipment_types": ["fryer", "grill", "oven", "ice_machine"],
                "safety_standards": "FDA",
                "operating_hours": "6am-11pm",
                "language": "en"
            }

# Initialize QSR Support Agent with OpenAI model
if PYDANTIC_AI_AVAILABLE:
    qsr_support_agent = Agent(
        model=OpenAIModel('gpt-4'),
        result_type=QSRTaskResponse,
        system_prompt="""
        You are a QSR (Quick Service Restaurant) support specialist with expertise in:
        - Equipment operation and maintenance procedures
        - Food safety protocols and compliance
        - Staff training and operational efficiency
        - Troubleshooting and problem resolution
        
        Always prioritize safety in your responses and provide:
        - Clear step-by-step procedures
        - Relevant safety warnings with severity levels
        - Specific equipment requirements
        - Estimated completion times
        - Visual aid references when available
        
        Use your tools to search for accurate, up-to-date information from restaurant manuals and procedures.
        Ensure all responses are actionable and appropriate for the restaurant environment.
        """,
        deps_type=QSRDependencies
    )
    
    @qsr_support_agent.tool
    async def get_formatted_procedure(
        ctx: RunContext[QSRDependencies], 
        procedure_type: str,
        equipment: str = None,
        include_images: bool = True
    ) -> CleanedQSRResponse:
        """
        Get comprehensive formatted procedure with cleaning pipeline integration
        
        Args:
            procedure_type: Type of procedure (cleaning, maintenance, troubleshooting, setup)
            equipment: Specific equipment name (optional)
            include_images: Whether to prioritize visual content
        
        Returns:
            CleanedQSRResponse with structured, readable format
        """
        try:
            # Build search query
            if equipment:
                query = f"{equipment} {procedure_type}"
            else:
                query = procedure_type
            
            # Create search request
            search_request = QSRSearchRequest(
                query=query,
                equipment_type=equipment,
                procedure_type=procedure_type,
                include_images=include_images,
                max_results=5
            )
            
            logger.info(f"🔍 Searching for formatted procedure: {query}")
            
            # Search Ragie using existing search function
            ragie_results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            
            # Process and clean using new processor
            logger.info(f"🧹 Processing {len(ragie_results)} Ragie results through cleaning pipeline")
            processed_data = response_cleaner.process_ragie_chunks(ragie_results)
            
            # Create cleaned response
            cleaned_response = CleanedQSRResponse(**processed_data)
            
            logger.info(f"✅ Generated cleaned procedure with {len(cleaned_response.steps)} steps")
            return cleaned_response
            
        except Exception as e:
            logger.error(f"❌ Formatted procedure search failed: {e}")
            # Return fallback response
            return CleanedQSRResponse(
                title=f"Error: {procedure_type} for {equipment or 'equipment'}",
                steps=[],
                overall_time="Unknown",
                procedure_type=procedure_type,
                confidence_score=0.0
            )
    
    @qsr_support_agent.tool
    async def search_equipment_procedures(
        ctx: RunContext[QSRDependencies], 
        equipment: str,
        procedure_type: str = "maintenance",
        include_images: bool = True
    ) -> List[QSRSearchResult]:
        """
        Search for equipment-specific procedures with structured output
        
        Args:
            equipment: Equipment name (e.g., "Baxter OV520E1", "fryer", "grill")
            procedure_type: Type of procedure (cleaning, maintenance, troubleshooting, setup)
            include_images: Whether to prioritize results with visual content
        
        Returns:
            List of structured search results with QSR metadata
        """
        try:
            search_request = QSRSearchRequest(
                query=f"{equipment} {procedure_type}",
                equipment_type=equipment,
                procedure_type=procedure_type,
                include_images=include_images,
                max_results=5
            )
            
            logger.info(f"🔍 Searching for {equipment} {procedure_type} procedures")
            results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            
            logger.info(f"✅ Found {len(results)} procedures for {equipment}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Equipment procedure search failed: {e}")
            return []
    
    @qsr_support_agent.tool
    async def get_safety_protocols(
        ctx: RunContext[QSRDependencies],
        equipment_or_task: str,
        safety_level: Optional[str] = None
    ) -> List[SafetyWarning]:
        """
        Get safety protocols and warnings for specific equipment or tasks
        
        Args:
            equipment_or_task: Equipment name or task description
            safety_level: Filter by safety level (critical, high, medium, low)
        
        Returns:
            List of structured safety warnings with severity and PPE requirements
        """
        try:
            search_request = QSRSearchRequest(
                query=f"safety {equipment_or_task} warning caution",
                safety_level=safety_level or ctx.deps.safety_level,
                max_results=8
            )
            
            logger.info(f"🛡️ Searching safety protocols for {equipment_or_task}")
            results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            
            # Extract safety warnings from results
            safety_warnings = []
            for result in results:
                if result.safety_level in ['critical', 'high']:
                    # Extract safety content
                    lines = result.content.split('\n')
                    for line in lines:
                        if any(word in line.lower() for word in ['warning', 'caution', 'danger', 'safety']):
                            safety_warnings.append(SafetyWarning(
                                level=result.safety_level,
                                message=line.strip(),
                                consequences=f"Risk associated with {equipment_or_task}",
                                required_ppe=["gloves", "safety glasses"] if "chemical" in line.lower() else []
                            ))
            
            logger.info(f"✅ Found {len(safety_warnings)} safety protocols")
            return safety_warnings[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"❌ Safety protocol search failed: {e}")
            return []
    
    @qsr_support_agent.tool 
    async def get_equipment_specifications(
        ctx: RunContext[QSRDependencies],
        equipment_name: str
    ) -> List[EquipmentReference]:
        """
        Get detailed equipment specifications and information
        
        Args:
            equipment_name: Name or model of equipment
        
        Returns:
            List of structured equipment references with specifications
        """
        try:
            search_request = QSRSearchRequest(
                query=f"{equipment_name} specifications model manual",
                equipment_type=equipment_name,
                include_images=True,
                max_results=3
            )
            
            logger.info(f"🔧 Searching specifications for {equipment_name}")
            results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            
            # Convert results to equipment references
            equipment_refs = []
            for result in results:
                # Extract equipment information from content
                equipment_ref = EquipmentReference(
                    name=equipment_name,
                    type=result.procedure_type or "equipment",
                    manufacturer=self._extract_manufacturer(result.content),
                    model_number=self._extract_model_number(result.content),
                    location=self._extract_location(result.content)
                )
                equipment_refs.append(equipment_ref)
            
            logger.info(f"✅ Found specifications for {len(equipment_refs)} equipment items")
            return equipment_refs
            
        except Exception as e:
            logger.error(f"❌ Equipment specification search failed: {e}")
            return []
    
    @qsr_support_agent.tool
    async def get_troubleshooting_steps(
        ctx: RunContext[QSRDependencies],
        equipment: str,
        problem_description: str
    ) -> List[ProcedureStep]:
        """
        Get troubleshooting steps for specific equipment problems
        
        Args:
            equipment: Equipment with the problem
            problem_description: Description of the issue
        
        Returns:
            List of structured troubleshooting steps
        """
        try:
            search_request = QSRSearchRequest(
                query=f"{equipment} troubleshooting {problem_description} fix repair",
                equipment_type=equipment,
                procedure_type="troubleshooting",
                max_results=5
            )
            
            logger.info(f"🔧 Searching troubleshooting for {equipment}: {problem_description}")
            results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            
            # Extract troubleshooting steps
            all_steps = []
            step_number = 1
            
            for result in results:
                if result.contains_steps:
                    lines = result.content.split('\n')
                    for line in lines:
                        line_stripped = line.strip()
                        if (len(line_stripped) > 15 and 
                            any(pattern in line_stripped.lower() for pattern in ['step', 'check', 'verify', 'test', 'replace'])):
                            
                            all_steps.append(ProcedureStep(
                                step_number=step_number,
                                instruction=line_stripped,
                                duration="2-5 minutes",
                                tools_needed=self._extract_tools_from_step(line_stripped),
                                safety_notes=self._extract_safety_from_step(line_stripped),
                                verification=f"Confirm {equipment} operates normally"
                            ))
                            step_number += 1
            
            logger.info(f"✅ Found {len(all_steps)} troubleshooting steps")
            return all_steps[:12]  # Limit to reasonable number
            
        except Exception as e:
            logger.error(f"❌ Troubleshooting search failed: {e}")
            return []
    
    @qsr_support_agent.tool
    async def get_opening_procedures(
        ctx: RunContext[QSRDependencies],
        equipment_type: str = None
    ) -> CleanedQSRResponse:
        """
        Get opening procedures with time-based formatting
        
        Args:
            equipment_type: Specific equipment to focus on (optional)
            
        Returns:
            CleanedQSRResponse formatted for opening procedures
        """
        try:
            query = f"opening procedures {equipment_type}" if equipment_type else "opening procedures"
            
            search_request = QSRSearchRequest(
                query=query,
                equipment_type=equipment_type,
                procedure_type="setup",
                include_images=True,
                max_results=5
            )
            
            logger.info(f"🌅 Searching opening procedures for {equipment_type or 'all equipment'}")
            
            ragie_results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            processed_data = response_cleaner.process_ragie_chunks(ragie_results)
            
            # Enhance for opening procedures
            processed_data['procedure_type'] = 'setup'
            processed_data['frequency'] = 'daily'
            processed_data['title'] = f"Opening Procedures - {equipment_type}" if equipment_type else "Daily Opening Procedures"
            
            return CleanedQSRResponse(**processed_data)
            
        except Exception as e:
            logger.error(f"❌ Opening procedures search failed: {e}")
            return CleanedQSRResponse(
                title="Opening Procedures Error",
                steps=[],
                overall_time="Unknown",
                procedure_type="setup",
                confidence_score=0.0
            )
    
    @qsr_support_agent.tool
    async def get_cleaning_procedures(
        ctx: RunContext[QSRDependencies],
        equipment: str,
        cleaning_type: str = "daily"
    ) -> CleanedQSRResponse:
        """
        Get cleaning procedures with safety emphasis
        
        Args:
            equipment: Equipment to clean
            cleaning_type: Type of cleaning (daily, weekly, deep)
            
        Returns:
            CleanedQSRResponse with safety warnings emphasized
        """
        try:
            query = f"{cleaning_type} cleaning {equipment}"
            
            search_request = QSRSearchRequest(
                query=query,
                equipment_type=equipment,
                procedure_type="cleaning",
                safety_level="high",
                include_images=True,
                max_results=5
            )
            
            logger.info(f"🧽 Searching cleaning procedures for {equipment}")
            
            ragie_results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            processed_data = response_cleaner.process_ragie_chunks(ragie_results)
            
            # Enhance for cleaning procedures
            processed_data['procedure_type'] = 'cleaning'
            processed_data['frequency'] = cleaning_type
            processed_data['title'] = f"{cleaning_type.title()} Cleaning - {equipment}"
            
            return CleanedQSRResponse(**processed_data)
            
        except Exception as e:
            logger.error(f"❌ Cleaning procedures search failed: {e}")
            return CleanedQSRResponse(
                title=f"Cleaning Procedures Error - {equipment}",
                steps=[],
                overall_time="Unknown",
                procedure_type="cleaning",
                confidence_score=0.0
            )
    
    @qsr_support_agent.tool
    async def get_maintenance_procedures(
        ctx: RunContext[QSRDependencies],
        equipment: str,
        maintenance_type: str = "routine"
    ) -> CleanedQSRResponse:
        """
        Get maintenance procedures with step verification
        
        Args:
            equipment: Equipment to maintain
            maintenance_type: Type of maintenance (routine, preventive, corrective)
            
        Returns:
            CleanedQSRResponse with verification checkpoints
        """
        try:
            query = f"{maintenance_type} maintenance {equipment}"
            
            search_request = QSRSearchRequest(
                query=query,
                equipment_type=equipment,
                procedure_type="maintenance",
                include_images=True,
                max_results=5
            )
            
            logger.info(f"🔧 Searching maintenance procedures for {equipment}")
            
            ragie_results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            processed_data = response_cleaner.process_ragie_chunks(ragie_results)
            
            # Enhance for maintenance procedures
            processed_data['procedure_type'] = 'maintenance'
            processed_data['title'] = f"{maintenance_type.title()} Maintenance - {equipment}"
            
            return CleanedQSRResponse(**processed_data)
            
        except Exception as e:
            logger.error(f"❌ Maintenance procedures search failed: {e}")
            return CleanedQSRResponse(
                title=f"Maintenance Procedures Error - {equipment}",
                steps=[],
                overall_time="Unknown",
                procedure_type="maintenance",
                confidence_score=0.0
            )
    
    @qsr_support_agent.tool
    async def get_troubleshooting_procedures(
        ctx: RunContext[QSRDependencies],
        equipment: str,
        problem_description: str
    ) -> CleanedQSRResponse:
        """
        Get troubleshooting procedures with decision tree formatting
        
        Args:
            equipment: Equipment with the problem
            problem_description: Description of the issue
            
        Returns:
            CleanedQSRResponse formatted as troubleshooting steps
        """
        try:
            query = f"{equipment} troubleshooting {problem_description}"
            
            search_request = QSRSearchRequest(
                query=query,
                equipment_type=equipment,
                procedure_type="troubleshooting",
                include_images=True,
                max_results=5
            )
            
            logger.info(f"🔧 Searching troubleshooting for {equipment}: {problem_description}")
            
            ragie_results = await ctx.deps.ragie_service.search_qsr_procedures(search_request)
            processed_data = response_cleaner.process_ragie_chunks(ragie_results)
            
            # Enhance for troubleshooting procedures
            processed_data['procedure_type'] = 'troubleshooting'
            processed_data['title'] = f"Troubleshooting - {equipment}: {problem_description}"
            processed_data['difficulty_level'] = 'intermediate'
            
            return CleanedQSRResponse(**processed_data)
            
        except Exception as e:
            logger.error(f"❌ Troubleshooting procedures search failed: {e}")
            return CleanedQSRResponse(
                title=f"Troubleshooting Error - {equipment}",
                steps=[],
                overall_time="Unknown",
                procedure_type="troubleshooting",
                confidence_score=0.0
            )
    
    # Helper methods for data extraction
    def _extract_manufacturer(self, content: str) -> Optional[str]:
        """Extract manufacturer from content"""
        manufacturers = ["Baxter", "Taylor", "Grote", "Henny Penny", "Frymaster"]
        for manufacturer in manufacturers:
            if manufacturer.lower() in content.lower():
                return manufacturer
        return None
    
    def _extract_model_number(self, content: str) -> Optional[str]:
        """Extract model number from content"""
        import re
        # Look for patterns like OV520E1, C602, etc.
        pattern = r'\b[A-Z]{1,3}\d{3,4}[A-Z]?\d?\b'
        matches = re.findall(pattern, content)
        return matches[0] if matches else None
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract typical location from content"""
        locations = ["kitchen", "prep area", "back of house", "front counter", "drive-thru"]
        for location in locations:
            if location.lower() in content.lower():
                return location
        return None
    
    def _extract_tools_from_step(self, step_text: str) -> List[str]:
        """Extract tools needed for a specific step"""
        tools = []
        tool_keywords = ["wrench", "screwdriver", "cleaning solution", "cloth", "brush", "multimeter"]
        
        for tool in tool_keywords:
            if tool in step_text.lower():
                tools.append(tool)
        
        return tools
    
    def _extract_safety_from_step(self, step_text: str) -> List[str]:
        """Extract safety notes for a specific step"""
        safety_notes = []
        
        if any(word in step_text.lower() for word in ["electrical", "power", "voltage"]):
            safety_notes.append("Ensure power is disconnected before proceeding")
        
        if any(word in step_text.lower() for word in ["hot", "temperature", "heat"]):
            safety_notes.append("Allow equipment to cool before handling")
        
        if any(word in step_text.lower() for word in ["chemical", "cleaning", "sanitizer"]):
            safety_notes.append("Wear appropriate PPE including gloves and eye protection")
        
        return safety_notes

else:
    # Fallback when PydanticAI not available
    logger.warning("PydanticAI not available - QSR support agent disabled")
    qsr_support_agent = None

# Convenience function to create agent with dependencies
def create_qsr_agent_context(
    user_id: str = "anonymous",
    restaurant_id: str = "default",
    safety_level: str = "high"
) -> QSRDependencies:
    """
    Create QSR dependencies for agent context
    
    Args:
        user_id: User identifier for session tracking
        restaurant_id: Restaurant identifier for configuration
        safety_level: Safety level for responses
    
    Returns:
        QSR dependencies ready for agent use
    """
    return QSRDependencies(
        ragie_service=qsr_ragie_service,
        user_context={
            "user_id": user_id,
            "session_start": datetime.now(),
            "restaurant_id": restaurant_id
        },
        restaurant_config={
            "equipment_types": ["fryer", "grill", "oven", "ice_machine", "pos_system"],
            "safety_standards": "FDA",
            "operating_hours": "6am-11pm",
            "language": "en"
        },
        safety_level=safety_level
    )

# Main agent interaction function
async def get_qsr_assistance(
    user_query: str,
    user_id: str = "anonymous",
    restaurant_id: str = "default",
    use_cleaning_pipeline: bool = True
) -> QSRTaskResponse:
    """
    Get comprehensive QSR assistance using the agent
    
    Args:
        user_query: User's question or request
        user_id: User identifier
        restaurant_id: Restaurant identifier
    
    Returns:
        Structured QSR response with procedures, safety, equipment info
    """
    if not PYDANTIC_AI_AVAILABLE or not qsr_support_agent:
        logger.error("QSR support agent not available")
        # Return fallback response
        return QSRTaskResponse(
            task_title="Service Unavailable",
            steps=[ProcedureStep(
                step_number=1,
                instruction="QSR support agent is not available. Please contact management.",
                safety_notes=["System requires PydanticAI installation"]
            )],
            estimated_time="N/A",
            confidence_level=0.0,
            procedure_type='training',
            source_documents=[]
        )
    
    try:
        # Create agent context with dependencies
        qsr_deps = create_qsr_agent_context(user_id, restaurant_id)
        
        # Determine if we should use cleaning pipeline
        if use_cleaning_pipeline and _should_use_cleaning_pipeline(user_query):
            logger.info(f"🧹 Using cleaning pipeline for procedural query: {user_query}")
            
            # Use cleaning pipeline for procedural queries
            search_request = QSRSearchRequest(
                query=user_query,
                procedure_type=_infer_procedure_type(user_query),
                equipment_type=_infer_equipment_type(user_query),
                include_images=True,
                max_results=5
            )
            
            ragie_results = await qsr_deps.ragie_service.search_qsr_procedures(search_request)
            processed_data = response_cleaner.process_ragie_chunks(ragie_results)
            
            # Convert to EnhancedQSRTaskResponse for backward compatibility
            cleaned_response = EnhancedQSRTaskResponse(**processed_data)
            
            logger.info(f"✅ Generated cleaned QSR response with {len(cleaned_response.steps)} steps")
            return cleaned_response
        else:
            # Use standard agent for non-procedural queries
            logger.info(f"🤖 Using standard agent for query: {user_query}")
            result = await qsr_support_agent.run(user_query, deps=qsr_deps)
            
            logger.info(f"✅ Generated standard QSR response")
            return result.data
        
    except Exception as e:
        logger.error(f"❌ QSR agent failed: {e}")
        # Return error response
        return QSRTaskResponse(
            task_title=f"Error Processing Request",
            steps=[ProcedureStep(
                step_number=1,
                instruction=f"Unable to process request: {str(e)}",
                safety_notes=["Contact technical support for assistance"]
            )],
            estimated_time="N/A", 
            confidence_level=0.0,
            procedure_type='training',
            source_documents=[]
        )

def _should_use_cleaning_pipeline(query: str) -> bool:
    """Determine if query should use cleaning pipeline"""
    procedural_indicators = [
        'how to', 'procedure', 'steps', 'process', 'clean', 'maintain',
        'troubleshoot', 'setup', 'opening', 'closing', 'daily', 'routine'
    ]
    
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in procedural_indicators)

def _infer_procedure_type(query: str) -> str:
    """Infer procedure type from query"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['clean', 'wash', 'sanitize', 'disinfect']):
        return 'cleaning'
    elif any(word in query_lower for word in ['repair', 'fix', 'maintain', 'service']):
        return 'maintenance'
    elif any(word in query_lower for word in ['troubleshoot', 'problem', 'issue', 'broken']):
        return 'troubleshooting'
    elif any(word in query_lower for word in ['setup', 'start', 'open', 'initialize']):
        return 'setup'
    elif any(word in query_lower for word in ['safety', 'emergency', 'hazard']):
        return 'safety'
    else:
        return 'training'

def _infer_equipment_type(query: str) -> Optional[str]:
    """Infer equipment type from query"""
    query_lower = query.lower()
    
    equipment_keywords = {
        'fryer': ['fryer', 'fry', 'deep fryer'],
        'grill': ['grill', 'griddle', 'grill top'],
        'oven': ['oven', 'bake', 'roast'],
        'ice_machine': ['ice machine', 'ice maker', 'ice'],
        'dishwasher': ['dishwasher', 'dish machine', 'washing'],
        'pos_system': ['pos', 'register', 'point of sale'],
        'mixer': ['mixer', 'mixing', 'dough'],
        'baxter': ['baxter'],
        'taylor': ['taylor'],
        'grote': ['grote']
    }
    
    for equipment, keywords in equipment_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            return equipment
    
    return None