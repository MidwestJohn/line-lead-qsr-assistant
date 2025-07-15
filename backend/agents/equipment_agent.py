#!/usr/bin/env python3
"""
Equipment Specialist Agent - Phase 2 Implementation
===================================================

Specialized PydanticAI agent for equipment-related queries and troubleshooting.
Handles all equipment maintenance, diagnostics, and operational guidance.

Features:
- Equipment-specific expertise (Taylor, Vulcan, Hobart, Traulsen, etc.)
- Diagnostic workflows and troubleshooting
- Maintenance scheduling and guidance
- Visual manual integration
- Safety protocol integration

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior, ModelRetry
from pydantic_ai.messages import ModelMessage
from pydantic import BaseModel, Field

# Import enhanced Ragie service
try:
    from ..services.enhanced_ragie_service import EnhancedRagieService, create_enhanced_ragie_service
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from services.enhanced_ragie_service import EnhancedRagieService, create_enhanced_ragie_service

# Equipment-specific system prompt
EQUIPMENT_SPECIALIST_PROMPT = """You are an expert Equipment Specialist for QSR (Quick Service Restaurant) operations with deep expertise in:

**EQUIPMENT EXPERTISE:**
- **Taylor Ice Cream Machines**: All models including C712, C713, C722, C723
  - Error codes and diagnostics (E01, E02, E03, etc.)
  - Cleaning cycles and maintenance schedules
  - Temperature calibration and troubleshooting
  - Replacement parts and service procedures

- **Vulcan Fryers**: All commercial models
  - Temperature control and calibration
  - Oil filtration and replacement
  - Heating element diagnostics
  - Safety system troubleshooting

- **Hobart Mixers**: All commercial models
  - Bowl and attachment maintenance
  - Motor diagnostics and troubleshooting
  - Safety interlocks and operation
  - Cleaning and sanitization

- **Traulsen Refrigeration**: All models
  - Temperature management and calibration
  - Compressor diagnostics
  - Door seal maintenance
  - Defrost system troubleshooting

- **General Equipment**: Grills, ovens, dishwashers, POS systems
  - Preventive maintenance schedules
  - Energy efficiency optimization
  - Compliance and safety checks

**DIAGNOSTIC APPROACH:**
1. **Symptom Analysis**: Identify specific symptoms and error codes
2. **Root Cause Analysis**: Determine underlying issues
3. **Step-by-Step Troubleshooting**: Clear diagnostic procedures
4. **Safety First**: Always prioritize safety in all procedures
5. **Documentation**: Reference specific manual sections and procedures

**MAINTENANCE GUIDANCE:**
- Daily, weekly, monthly maintenance schedules
- Preventive maintenance best practices
- Parts replacement timelines
- Service call decision criteria
- Cost-effective maintenance strategies

**SAFETY INTEGRATION:**
- Equipment-specific safety protocols
- Lockout/tagout procedures
- Personal protective equipment requirements
- Emergency shutdown procedures
- Incident prevention and reporting

**RESPONSE FORMAT:**
- Provide clear, step-by-step instructions
- Include specific manual references
- Highlight safety warnings and cautions
- Suggest when to contact service technicians
- Include estimated time requirements
- Provide troubleshooting decision trees

**MANUAL REFERENCES:**
Always reference specific equipment manuals, page numbers, and section references when available.
Format: [Equipment Manual: Page X] or [Service Guide: Section Y]

You have access to comprehensive equipment documentation and should always provide accurate, actionable guidance that prioritizes safety and efficiency.
"""

class EquipmentType(Enum):
    """Types of equipment handled by the specialist"""
    TAYLOR_ICE_CREAM = "taylor_ice_cream"
    VULCAN_FRYER = "vulcan_fryer"
    HOBART_MIXER = "hobart_mixer"
    TRAULSEN_REFRIGERATION = "traulsen_refrigeration"
    GENERAL_EQUIPMENT = "general_equipment"
    GRILL = "grill"
    OVEN = "oven"
    DISHWASHER = "dishwasher"
    POS_SYSTEM = "pos_system"

class DiagnosticLevel(Enum):
    """Diagnostic complexity levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SERVICE_REQUIRED = "service_required"

@dataclass
class EquipmentContext:
    """Context for equipment-specific operations"""
    equipment_type: EquipmentType
    model_number: Optional[str] = None
    error_codes: List[str] = field(default_factory=list)
    symptoms: List[str] = field(default_factory=list)
    last_maintenance: Optional[datetime] = None
    location: Optional[str] = None
    urgency_level: str = "normal"  # normal, urgent, emergency
    
class EquipmentResponse(BaseModel):
    """Specialized response for equipment queries"""
    response: str
    equipment_type: EquipmentType
    diagnostic_level: DiagnosticLevel
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Equipment-specific fields
    error_codes_addressed: List[str] = Field(default_factory=list)
    manual_references: List[str] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    maintenance_recommendations: List[str] = Field(default_factory=list)
    
    # Diagnostic information
    diagnostic_steps: List[str] = Field(default_factory=list)
    tools_required: List[str] = Field(default_factory=list)
    estimated_time: Optional[str] = None
    
    # Service information
    service_call_recommended: bool = False
    service_urgency: str = "normal"  # normal, urgent, emergency
    replacement_parts: List[str] = Field(default_factory=list)
    
    # Follow-up
    follow_up_required: bool = False
    follow_up_timeframe: Optional[str] = None
    
    class Config:
        exclude_none = False

class EquipmentSpecialistAgent:
    """
    Equipment Specialist Agent using PydanticAI patterns.
    
    Specialized for equipment troubleshooting, maintenance, and diagnostics.
    """
    
    def __init__(self, model: str = None):
        # Use environment variable or default to GPT-4o
        model = model or os.getenv("EQUIPMENT_MODEL", "openai:gpt-4o")
        
        # Initialize PydanticAI Agent with equipment-specific prompt
        self.agent = Agent(
            model=model,
            system_prompt=EQUIPMENT_SPECIALIST_PROMPT,
            retries=3
        )
        
        # Agent metadata
        self.agent_id = "equipment_specialist_agent"
        self.version = "1.0.0"
        self.specialization = "Equipment Diagnostics & Maintenance"
        self.created_at = datetime.now()
        
        # Equipment database
        self.equipment_database = self._initialize_equipment_database()
        
        # Performance tracking
        self.query_count = 0
        self.diagnostic_count = 0
        self.maintenance_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
        # Enhanced services
        self._ragie_service = None
        self._initialized = False
        
        # Performance tracking
        self.query_count = 0
        self.diagnostic_count = 0
        self.maintenance_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
    
    def _initialize_equipment_database(self) -> Dict[str, Any]:
        """Initialize equipment knowledge database"""
        return {
            "taylor_ice_cream": {
                "models": ["C712", "C713", "C722", "C723", "C744"],
                "common_errors": {
                    "E01": "Mix low alarm",
                    "E02": "Freezer temperature alarm",
                    "E03": "Mix temperature alarm",
                    "E04": "Viscosity alarm",
                    "E05": "Drive motor alarm"
                },
                "maintenance_schedule": {
                    "daily": ["Clean exterior", "Check mix levels", "Verify temperatures"],
                    "weekly": ["Deep clean", "Sanitize", "Check belts"],
                    "monthly": ["Lubricate", "Check filters", "Calibrate"]
                }
            },
            "vulcan_fryer": {
                "models": ["PowerFry", "GR Series", "CEF Series"],
                "common_issues": [
                    "Temperature inconsistency",
                    "Oil filtration problems",
                    "Heating element failure",
                    "Safety system alarms"
                ],
                "maintenance_schedule": {
                    "daily": ["Oil level check", "Temperature verification", "Clean filters"],
                    "weekly": ["Deep clean", "Filter replacement", "Safety check"],
                    "monthly": ["Full service", "Calibration", "Parts inspection"]
                }
            },
            "hobart_mixer": {
                "models": ["HL120", "HL200", "HL300", "HL400"],
                "common_issues": [
                    "Motor overheating",
                    "Bowl attachment problems",
                    "Speed control issues",
                    "Safety interlock problems"
                ],
                "maintenance_schedule": {
                    "daily": ["Clean bowl", "Check attachments", "Lubricate"],
                    "weekly": ["Deep clean", "Motor check", "Safety inspection"],
                    "monthly": ["Full service", "Belt inspection", "Calibration"]
                }
            },
            "traulsen_refrigeration": {
                "models": ["G Series", "A Series", "R Series"],
                "common_issues": [
                    "Temperature fluctuations",
                    "Compressor problems",
                    "Door seal issues",
                    "Defrost system failures"
                ],
                "maintenance_schedule": {
                    "daily": ["Temperature check", "Door seal inspection"],
                    "weekly": ["Coil cleaning", "Drain check", "Calibration"],
                    "monthly": ["Full service", "Refrigerant check", "Seal replacement"]
                }
            }
        }
    
    async def initialize(self) -> None:
        """Initialize the equipment agent with enhanced services"""
        if self._initialized:
            return
        
        try:
            # Initialize enhanced Ragie service
            self._ragie_service = await create_enhanced_ragie_service()
            self._initialized = True
            
        except Exception as e:
            print(f"Warning: Failed to initialize enhanced services: {e}")
            # Continue without enhanced services
            self._initialized = True
    
    async def handle_equipment_query(
        self,
        query: str,
        context: Dict[str, Any],
        message_history: List[ModelMessage] = None
    ) -> EquipmentResponse:
        """
        Handle equipment query with enhanced Ragie integration.
        
        This is the main method called by the orchestrator for equipment-related queries.
        """
        if not self._initialized:
            await self.initialize()
        
        # Convert context dict to EquipmentContext
        equipment_context = self._create_equipment_context_from_dict(context)
        
        # Search for relevant documents using enhanced Ragie
        ragie_results = None
        if self._ragie_service:
            try:
                from .types import AgentType
                ragie_results = await self._ragie_service.search_for_agent(
                    query=query,
                    agent_type=AgentType.EQUIPMENT,
                    context=context
                )
            except Exception as e:
                print(f"Ragie search failed: {e}")
        
        # Enhance query with Ragie results
        enhanced_query = self._enhance_query_with_ragie(query, equipment_context, ragie_results)
        
        # Use the existing diagnose_equipment method
        return await self.diagnose_equipment(enhanced_query, equipment_context, message_history)
    
    async def handle_equipment_query_stream(
        self,
        query: str,
        context: Dict[str, Any],
        message_history: List[ModelMessage] = None
    ):
        """
        Handle streaming equipment query with enhanced Ragie integration.
        """
        if not self._initialized:
            await self.initialize()
        
        # Convert context dict to EquipmentContext  
        equipment_context = self._create_equipment_context_from_dict(context)
        
        # Search for relevant documents using enhanced Ragie
        ragie_results = None
        if self._ragie_service:
            try:
                from .types import AgentType
                ragie_results = await self._ragie_service.search_for_agent(
                    query=query,
                    agent_type=AgentType.EQUIPMENT,
                    context=context
                )
            except Exception as e:
                print(f"Ragie search failed: {e}")
        
        # Enhance query with Ragie results
        enhanced_query = self._enhance_query_with_ragie(query, equipment_context, ragie_results)
        
        # Stream response using PydanticAI
        try:
            async with self.agent.run_stream(enhanced_query, message_history=message_history or []) as result:
                async for text_chunk in result.stream(debounce_by=0.01):
                    yield {
                        "chunk": text_chunk,
                        "timestamp": datetime.now().isoformat(),
                        "done": False
                    }
                
                # Send final chunk with metadata
                final_response = await self.diagnose_equipment(enhanced_query, equipment_context, message_history)
                yield {
                    "chunk": "",
                    "done": True,
                    "metadata": {
                        "equipment_type": final_response.equipment_type.value,
                        "diagnostic_level": final_response.diagnostic_level.value,
                        "confidence": final_response.confidence,
                        "service_required": final_response.service_call_recommended,
                        "ragie_results_used": ragie_results.total_results if ragie_results else 0
                    }
                }
        except Exception as e:
            yield {
                "chunk": f"Error in equipment diagnosis: {str(e)}",
                "done": True,
                "error": True
            }
    
    def _create_equipment_context_from_dict(self, context_dict: Dict[str, Any]) -> EquipmentContext:
        """Convert dict context to EquipmentContext object"""
        
        # Extract equipment type
        equipment_type_str = context_dict.get("equipment_type", "other")
        try:
            equipment_type = EquipmentType(equipment_type_str)
        except ValueError:
            equipment_type = EquipmentType.GENERAL_EQUIPMENT
        
        return EquipmentContext(
            equipment_type=equipment_type,
            model_number=context_dict.get("model_number"),
            error_codes=context_dict.get("error_codes", []),
            symptoms=context_dict.get("symptoms", []),
            last_maintenance=datetime.fromisoformat(context_dict["last_maintenance"]) if context_dict.get("last_maintenance") else None,
            location=context_dict.get("location"),
            urgency_level=context_dict.get("urgency_level", "normal")
        )
    
    def _enhance_query_with_ragie(
        self, 
        query: str, 
        context: EquipmentContext, 
        ragie_results
    ) -> str:
        """Enhance query with Ragie search results"""
        
        enhanced_parts = [query]
        
        # Add equipment context
        enhanced_parts.append(f"\nEquipment Type: {context.equipment_type.value}")
        
        if context.model_number:
            enhanced_parts.append(f"Model: {context.model_number}")
        
        if context.error_codes:
            enhanced_parts.append(f"Error Codes: {', '.join(context.error_codes)}")
        
        if context.symptoms:
            enhanced_parts.append(f"Symptoms: {', '.join(context.symptoms)}")
        
        # Add Ragie search results
        if ragie_results and ragie_results.results:
            enhanced_parts.append("\nRelevant Equipment Documentation:")
            for i, result in enumerate(ragie_results.results[:3], 1):  # Top 3 results
                enhanced_parts.append(f"{i}. [{result.source}] {result.content[:200]}...")
        
        return "\n".join(enhanced_parts)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status including enhanced services"""
        
        base_health = await self.health_check()
        
        # Add Ragie service health
        ragie_health = None
        if self._ragie_service:
            try:
                ragie_health = await self._ragie_service.get_health_status()
            except Exception as e:
                ragie_health = {"status": "error", "error": str(e)}
        
        base_health["ragie_service"] = ragie_health
        base_health["enhanced_services_initialized"] = self._initialized
        
        return base_health
    
    @classmethod
    async def create(cls, **kwargs) -> 'EquipmentSpecialistAgent':
        """Factory method to create and initialize equipment agent"""
        agent = cls(**kwargs)
        await agent.initialize()
        return agent
    
    async def diagnose_equipment(
        self, 
        query: str, 
        context: EquipmentContext,
        message_history: List[ModelMessage] = None
    ) -> EquipmentResponse:
        """
        Diagnose equipment issues using specialized knowledge.
        
        Args:
            query: User query about equipment
            context: Equipment context information
            message_history: Previous conversation messages
            
        Returns:
            EquipmentResponse with diagnostic information
        """
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Enhance query with equipment context
            enhanced_query = self._enhance_query_with_equipment_context(query, context)
            
            # Run PydanticAI Agent
            result = await self.agent.run(
                enhanced_query,
                message_history=message_history or []
            )
            
            # Process response for equipment-specific information
            response_data = self._process_equipment_response(result.data, query, context)
            
            # Update performance metrics
            self.query_count += 1
            self.diagnostic_count += 1
            self.total_response_time += asyncio.get_event_loop().time() - start_time
            
            return response_data
            
        except UnexpectedModelBehavior as e:
            self.error_count += 1
            return EquipmentResponse(
                response=f"I encountered an unexpected issue diagnosing this equipment problem. Please provide more specific details about the symptoms.",
                equipment_type=context.equipment_type,
                diagnostic_level=DiagnosticLevel.SERVICE_REQUIRED,
                confidence=0.0,
                service_call_recommended=True,
                service_urgency="urgent"
            )
            
        except ModelRetry as e:
            self.error_count += 1
            return EquipmentResponse(
                response=f"I'm having trouble accessing equipment diagnostics right now. Please try again in a moment.",
                equipment_type=context.equipment_type,
                diagnostic_level=DiagnosticLevel.BASIC,
                confidence=0.0
            )
            
        except Exception as e:
            self.error_count += 1
            return EquipmentResponse(
                response=f"I'm experiencing technical difficulties with equipment diagnostics. Please contact technical support.",
                equipment_type=context.equipment_type,
                diagnostic_level=DiagnosticLevel.SERVICE_REQUIRED,
                confidence=0.0,
                service_call_recommended=True,
                service_urgency="urgent"
            )
    
    async def get_maintenance_schedule(self, equipment_type: EquipmentType, model: str = None) -> Dict[str, Any]:
        """Get maintenance schedule for specific equipment"""
        
        equipment_key = equipment_type.value
        equipment_data = self.equipment_database.get(equipment_key, {})
        
        if not equipment_data:
            return {
                "equipment_type": equipment_type.value,
                "error": "Equipment type not found in database"
            }
        
        schedule = equipment_data.get("maintenance_schedule", {})
        
        return {
            "equipment_type": equipment_type.value,
            "model": model,
            "maintenance_schedule": schedule,
            "generated_at": datetime.now().isoformat()
        }
    
    def _enhance_query_with_equipment_context(self, query: str, context: EquipmentContext) -> str:
        """Enhance query with equipment-specific context"""
        
        enhanced_parts = [query]
        
        # Add equipment type context
        enhanced_parts.append(f"\nEquipment Type: {context.equipment_type.value}")
        
        # Add model information
        if context.model_number:
            enhanced_parts.append(f"Model: {context.model_number}")
        
        # Add error codes
        if context.error_codes:
            enhanced_parts.append(f"Error Codes: {', '.join(context.error_codes)}")
        
        # Add symptoms
        if context.symptoms:
            enhanced_parts.append(f"Symptoms: {', '.join(context.symptoms)}")
        
        # Add maintenance history
        if context.last_maintenance:
            enhanced_parts.append(f"Last Maintenance: {context.last_maintenance.strftime('%Y-%m-%d')}")
        
        # Add urgency
        if context.urgency_level != "normal":
            enhanced_parts.append(f"Urgency Level: {context.urgency_level}")
        
        # Add location
        if context.location:
            enhanced_parts.append(f"Location: {context.location}")
        
        # Add equipment database context
        equipment_key = context.equipment_type.value
        if equipment_key in self.equipment_database:
            equipment_data = self.equipment_database[equipment_key]
            enhanced_parts.append(f"\nEquipment Database Info: {equipment_data}")
        
        return "\n".join(enhanced_parts)
    
    def _process_equipment_response(self, response_text: str, original_query: str, context: EquipmentContext) -> EquipmentResponse:
        """Process raw response into structured EquipmentResponse"""
        
        # Extract equipment-specific information
        error_codes = self._extract_error_codes(response_text, context)
        manual_references = self._extract_manual_references(response_text)
        safety_warnings = self._extract_safety_warnings(response_text)
        maintenance_recommendations = self._extract_maintenance_recommendations(response_text)
        diagnostic_steps = self._extract_diagnostic_steps(response_text)
        tools_required = self._extract_tools_required(response_text)
        
        # Determine diagnostic level
        diagnostic_level = self._determine_diagnostic_level(response_text, context)
        
        # Determine service requirements
        service_call_recommended = self._requires_service_call(response_text, diagnostic_level)
        service_urgency = self._determine_service_urgency(response_text, context)
        
        # Extract replacement parts
        replacement_parts = self._extract_replacement_parts(response_text)
        
        # Determine follow-up requirements
        follow_up_required = self._requires_follow_up(response_text, diagnostic_level)
        follow_up_timeframe = self._determine_follow_up_timeframe(response_text, context)
        
        # Calculate confidence score
        confidence = self._calculate_equipment_confidence(response_text, context)
        
        return EquipmentResponse(
            response=response_text,
            equipment_type=context.equipment_type,
            diagnostic_level=diagnostic_level,
            confidence=confidence,
            error_codes_addressed=error_codes,
            manual_references=manual_references,
            safety_warnings=safety_warnings,
            maintenance_recommendations=maintenance_recommendations,
            diagnostic_steps=diagnostic_steps,
            tools_required=tools_required,
            service_call_recommended=service_call_recommended,
            service_urgency=service_urgency,
            replacement_parts=replacement_parts,
            follow_up_required=follow_up_required,
            follow_up_timeframe=follow_up_timeframe
        )
    
    def _extract_error_codes(self, response: str, context: EquipmentContext) -> List[str]:
        """Extract error codes from response"""
        
        error_codes = []
        
        # Check for mentioned error codes
        for error_code in context.error_codes:
            if error_code in response:
                error_codes.append(error_code)
        
        # Look for additional error codes in response
        import re
        error_pattern = r'E\d{2}'
        found_errors = re.findall(error_pattern, response)
        error_codes.extend(found_errors)
        
        return list(set(error_codes))  # Remove duplicates
    
    def _extract_manual_references(self, response: str) -> List[str]:
        """Extract manual references from response"""
        
        references = []
        
        # Look for manual reference patterns
        import re
        reference_patterns = [
            r'\[([^]]*Manual[^]]*)\]',
            r'\[([^]]*Guide[^]]*)\]',
            r'\[([^]]*Page \d+[^]]*)\]',
            r'\[([^]]*Section [^]]*)\]'
        ]
        
        for pattern in reference_patterns:
            matches = re.findall(pattern, response)
            references.extend(matches)
        
        return references
    
    def _extract_safety_warnings(self, response: str) -> List[str]:
        """Extract safety warnings from response"""
        
        warnings = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["warning", "danger", "caution", "safety", "hazard"]):
                warnings.append(line.strip())
        
        return warnings
    
    def _extract_maintenance_recommendations(self, response: str) -> List[str]:
        """Extract maintenance recommendations from response"""
        
        recommendations = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["maintenance", "schedule", "service", "replace", "clean"]):
                if any(action in line_lower for action in ["should", "must", "recommend", "suggest"]):
                    recommendations.append(line.strip())
        
        return recommendations
    
    def _extract_diagnostic_steps(self, response: str) -> List[str]:
        """Extract diagnostic steps from response"""
        
        steps = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered steps or bullet points
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                line.startswith(('•', '-', '*')) or
                line.startswith(('Step', 'First', 'Then', 'Next', 'Finally'))):
                steps.append(line)
        
        return steps
    
    def _extract_tools_required(self, response: str) -> List[str]:
        """Extract required tools from response"""
        
        tools = []
        response_lower = response.lower()
        
        # Common tools
        common_tools = [
            "multimeter", "thermometer", "screwdriver", "wrench", "pliers",
            "voltmeter", "pressure gauge", "level", "torque wrench", "flashlight"
        ]
        
        for tool in common_tools:
            if tool in response_lower:
                tools.append(tool.title())
        
        return tools
    
    def _extract_replacement_parts(self, response: str) -> List[str]:
        """Extract replacement parts from response"""
        
        parts = []
        response_lower = response.lower()
        
        # Look for part-related keywords
        part_keywords = ["replace", "part", "component", "filter", "belt", "motor", "sensor"]
        
        lines = response.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in part_keywords):
                if "part" in line_lower or "component" in line_lower:
                    parts.append(line.strip())
        
        return parts
    
    def _determine_diagnostic_level(self, response: str, context: EquipmentContext) -> DiagnosticLevel:
        """Determine diagnostic complexity level"""
        
        response_lower = response.lower()
        
        # Check for service-required indicators
        if any(keyword in response_lower for keyword in ["service", "technician", "call", "professional"]):
            return DiagnosticLevel.SERVICE_REQUIRED
        
        # Check for advanced indicators
        if any(keyword in response_lower for keyword in ["advanced", "complex", "calibration", "electrical"]):
            return DiagnosticLevel.ADVANCED
        
        # Check for intermediate indicators
        if any(keyword in response_lower for keyword in ["diagnostic", "troubleshoot", "disassemble", "test"]):
            return DiagnosticLevel.INTERMEDIATE
        
        return DiagnosticLevel.BASIC
    
    def _requires_service_call(self, response: str, diagnostic_level: DiagnosticLevel) -> bool:
        """Determine if service call is recommended"""
        
        if diagnostic_level == DiagnosticLevel.SERVICE_REQUIRED:
            return True
        
        response_lower = response.lower()
        service_keywords = ["service", "technician", "call", "professional", "repair"]
        
        return any(keyword in response_lower for keyword in service_keywords)
    
    def _determine_service_urgency(self, response: str, context: EquipmentContext) -> str:
        """Determine service urgency level"""
        
        if context.urgency_level == "emergency":
            return "emergency"
        
        response_lower = response.lower()
        
        if any(keyword in response_lower for keyword in ["emergency", "immediate", "urgent", "critical"]):
            return "urgent"
        
        return "normal"
    
    def _requires_follow_up(self, response: str, diagnostic_level: DiagnosticLevel) -> bool:
        """Determine if follow-up is required"""
        
        if diagnostic_level in [DiagnosticLevel.ADVANCED, DiagnosticLevel.SERVICE_REQUIRED]:
            return True
        
        response_lower = response.lower()
        follow_up_keywords = ["follow", "check", "monitor", "verify", "test"]
        
        return any(keyword in response_lower for keyword in follow_up_keywords)
    
    def _determine_follow_up_timeframe(self, response: str, context: EquipmentContext) -> Optional[str]:
        """Determine follow-up timeframe"""
        
        if context.urgency_level == "emergency":
            return "immediately"
        elif context.urgency_level == "urgent":
            return "within 24 hours"
        
        response_lower = response.lower()
        
        if any(keyword in response_lower for keyword in ["daily", "day"]):
            return "daily"
        elif any(keyword in response_lower for keyword in ["weekly", "week"]):
            return "weekly"
        elif any(keyword in response_lower for keyword in ["monthly", "month"]):
            return "monthly"
        
        return "as needed"
    
    def _calculate_equipment_confidence(self, response: str, context: EquipmentContext) -> float:
        """Calculate confidence score for equipment response"""
        
        confidence = 0.7  # Base confidence
        
        # Increase confidence for specific equipment matches
        if context.equipment_type.value in response.lower():
            confidence += 0.1
        
        # Increase confidence for error code matches
        if context.error_codes:
            for error_code in context.error_codes:
                if error_code in response:
                    confidence += 0.05
        
        # Increase confidence for manual references
        if "[" in response and "]" in response:
            confidence += 0.1
        
        # Increase confidence for structured responses
        if any(marker in response for marker in ["1.", "2.", "3.", "•", "-"]):
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get equipment agent performance metrics"""
        
        avg_response_time = self.total_response_time / self.query_count if self.query_count > 0 else 0
        
        return {
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "version": self.version,
            "query_count": self.query_count,
            "diagnostic_count": self.diagnostic_count,
            "maintenance_count": self.maintenance_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.query_count if self.query_count > 0 else 0,
            "average_response_time": avg_response_time,
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "model": str(self.agent.model)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the equipment agent"""
        
        try:
            # Test basic functionality
            test_context = EquipmentContext(
                equipment_type=EquipmentType.TAYLOR_ICE_CREAM,
                error_codes=["E01"],
                symptoms=["Mix low alarm"]
            )
            
            test_result = await self.diagnose_equipment("Test diagnostic query", test_context)
            
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "specialization": self.specialization,
                "model": str(self.agent.model),
                "test_successful": True,
                "performance_metrics": self.get_performance_metrics(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_id": self.agent_id,
                "specialization": self.specialization,
                "model": str(self.agent.model),
                "test_successful": False,
                "error": str(e),
                "performance_metrics": self.get_performance_metrics(),
                "timestamp": datetime.now().isoformat()
            }

# Global equipment agent instance
equipment_agent = EquipmentSpecialistAgent()

# Factory function
def create_equipment_agent(model: str = None) -> EquipmentSpecialistAgent:
    """Factory function to create equipment agents"""
    return EquipmentSpecialistAgent(model=model)

# Async factory function
async def create_equipment_agent_async(model: str = None) -> EquipmentSpecialistAgent:
    """Async factory function to create equipment agents"""
    agent = EquipmentSpecialistAgent(model=model)
    
    # Perform health check
    health_status = await agent.health_check()
    
    if health_status["status"] != "healthy":
        raise Exception(f"Equipment agent health check failed: {health_status.get('error', 'Unknown error')}")
    
    return agent

if __name__ == "__main__":
    # Test the equipment agent
    async def test_equipment_agent():
        agent = await create_equipment_agent_async()
        
        # Test Taylor machine diagnostic
        context = EquipmentContext(
            equipment_type=EquipmentType.TAYLOR_ICE_CREAM,
            model_number="C712",
            error_codes=["E01"],
            symptoms=["Mix low alarm", "Machine beeping"],
            urgency_level="urgent"
        )
        
        response = await agent.diagnose_equipment(
            "The Taylor ice cream machine is showing error E01 and beeping continuously. What should I do?",
            context
        )
        
        print("Equipment Diagnostic Response:")
        print(f"Response: {response.response}")
        print(f"Equipment Type: {response.equipment_type.value}")
        print(f"Diagnostic Level: {response.diagnostic_level.value}")
        print(f"Confidence: {response.confidence}")
        print(f"Error Codes: {response.error_codes_addressed}")
        print(f"Safety Warnings: {response.safety_warnings}")
        print(f"Service Required: {response.service_call_recommended}")
        print(f"Diagnostic Steps: {response.diagnostic_steps}")
        print()
        
        # Test maintenance schedule
        schedule = await agent.get_maintenance_schedule(EquipmentType.TAYLOR_ICE_CREAM, "C712")
        print("Maintenance Schedule:")
        print(schedule)
        print()
        
        # Performance metrics
        print("Performance Metrics:")
        print(agent.get_performance_metrics())
    
    asyncio.run(test_equipment_agent())