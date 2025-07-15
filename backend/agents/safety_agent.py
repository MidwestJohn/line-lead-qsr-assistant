#!/usr/bin/env python3
"""
Safety Specialist Agent - Phase 2 Implementation
================================================

Specialized PydanticAI agent for safety-related queries and emergency response.
Handles all safety protocols, emergency procedures, and compliance guidance.

Features:
- Emergency response protocols
- Food safety and HACCP compliance
- Workplace safety procedures
- Incident reporting and documentation
- Training and certification guidance

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

# Safety-specific system prompt
SAFETY_SPECIALIST_PROMPT = """You are an expert Safety Specialist for QSR (Quick Service Restaurant) operations with comprehensive expertise in:

**EMERGENCY RESPONSE:**
- **Medical Emergencies**: Burns, cuts, choking, allergic reactions, cardiac events
  - Immediate first aid procedures
  - When to call 911 vs. handling internally
  - Documentation requirements
  - Staff notification protocols

- **Fire Safety**: Grease fires, electrical fires, general fire emergencies
  - Fire suppression procedures
  - Evacuation protocols
  - Equipment shutdown procedures
  - Emergency contact procedures

- **Chemical Safety**: Cleaning chemical spills, mixing accidents, exposure incidents
  - Immediate response procedures
  - Personal protective equipment
  - Ventilation requirements
  - Material Safety Data Sheet (MSDS) guidance

**FOOD SAFETY & HACCP:**
- **Temperature Control**: Safe holding temperatures, cooking temperatures, cooling procedures
- **Cross-Contamination Prevention**: Separate preparation areas, utensil protocols
- **Personal Hygiene**: Handwashing, glove use, uniform requirements
- **Allergen Management**: Identification, prevention, response protocols
- **Sanitation**: Cleaning schedules, approved sanitizers, documentation

**WORKPLACE SAFETY:**
- **Slip/Fall Prevention**: Floor maintenance, signage, proper footwear
- **Equipment Safety**: Lockout/tagout procedures, safety guards, proper operation
- **Ergonomics**: Lifting techniques, repetitive motion prevention
- **Chemical Handling**: Storage, mixing, application, disposal
- **Personal Protective Equipment**: Selection, use, maintenance

**INCIDENT MANAGEMENT:**
- **Incident Reporting**: Documentation requirements, timing, authorities
- **Investigation Procedures**: Root cause analysis, corrective actions
- **Workers' Compensation**: Claim procedures, documentation
- **Regulatory Compliance**: OSHA, health department, insurance requirements

**TRAINING & COMPLIANCE:**
- **Safety Training Programs**: New employee orientation, ongoing training
- **Certification Requirements**: Food handler permits, safety training
- **Documentation**: Training records, incident logs, inspection reports
- **Compliance Audits**: Self-assessment, third-party audits

**CRISIS MANAGEMENT:**
- **Emergency Communication**: Staff notification, customer communication
- **Business Continuity**: Temporary closure procedures, reopening protocols
- **Media Relations**: Public relations, social media management
- **Legal Compliance**: Regulatory reporting, legal notifications

**RESPONSE PRIORITY:**
1. **LIFE SAFETY FIRST**: Always prioritize human life and safety
2. **IMMEDIATE ACTION**: Provide immediate response steps
3. **PROFESSIONAL HELP**: When to call emergency services
4. **DOCUMENTATION**: Required reporting and documentation
5. **FOLLOW-UP**: Post-incident procedures and prevention

**EMERGENCY PROTOCOLS:**
- Always start with immediate safety measures
- Provide clear, step-by-step instructions
- Emphasize when to call 911 or emergency services
- Include specific timeframes for actions
- Reference relevant regulations and standards

**COMPLIANCE STANDARDS:**
- OSHA workplace safety standards
- FDA food safety regulations
- Local health department requirements
- Industry-specific safety standards
- Workers' compensation requirements

You have access to comprehensive safety documentation, emergency procedures, and regulatory requirements. Always provide accurate, actionable guidance that prioritizes safety and compliance.
"""

class SafetyIncidentType(Enum):
    """Types of safety incidents"""
    BURN = "burn"
    CUT = "cut"
    SLIP_FALL = "slip_fall"
    CHOKING = "choking"
    ALLERGIC_REACTION = "allergic_reaction"
    FIRE = "fire"
    CHEMICAL_EXPOSURE = "chemical_exposure"
    EQUIPMENT_INJURY = "equipment_injury"
    FOOD_CONTAMINATION = "food_contamination"
    WORKPLACE_VIOLENCE = "workplace_violence"
    GENERAL_EMERGENCY = "general_emergency"

class SafetySeverity(Enum):
    """Safety incident severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ResponseUrgency(Enum):
    """Response urgency levels"""
    IMMEDIATE = "immediate"
    URGENT = "urgent"
    NORMAL = "normal"
    PREVENTIVE = "preventive"

@dataclass
class SafetyContext:
    """Context for safety-related operations"""
    incident_type: SafetyIncidentType
    severity: SafetySeverity
    location: str
    injured_persons: int = 0
    immediate_danger: bool = False
    equipment_involved: Optional[str] = None
    witnesses: int = 0
    emergency_services_called: bool = False
    time_of_incident: Optional[datetime] = None
    
class SafetyResponse(BaseModel):
    """Specialized response for safety queries"""
    response: str
    incident_type: SafetyIncidentType
    severity: SafetySeverity
    urgency: ResponseUrgency
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    
    # Emergency response
    immediate_actions: List[str] = Field(default_factory=list)
    call_911: bool = False
    call_emergency_services: bool = False
    evacuation_required: bool = False
    
    # Safety protocols
    safety_procedures: List[str] = Field(default_factory=list)
    ppe_required: List[str] = Field(default_factory=list)
    equipment_shutdown: List[str] = Field(default_factory=list)
    
    # Documentation
    incident_reporting_required: bool = True
    documentation_timeline: Optional[str] = None
    regulatory_notifications: List[str] = Field(default_factory=list)
    
    # Follow-up
    medical_attention_required: bool = False
    investigation_required: bool = False
    training_required: bool = False
    
    # Prevention
    prevention_measures: List[str] = Field(default_factory=list)
    policy_updates: List[str] = Field(default_factory=list)
    
    # Compliance
    regulations_cited: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    
    class Config:
        exclude_none = False

class SafetySpecialistAgent:
    """
    Safety Specialist Agent using PydanticAI patterns.
    
    Specialized for safety protocols, emergency response, and compliance.
    """
    
    def __init__(self, model: str = None):
        # Use environment variable or default to GPT-4o
        model = model or os.getenv("SAFETY_MODEL", "openai:gpt-4o")
        
        # Initialize PydanticAI Agent with safety-specific prompt
        self.agent = Agent(
            model=model,
            system_prompt=SAFETY_SPECIALIST_PROMPT,
            retries=3
        )
        
        # Agent metadata
        self.agent_id = "safety_specialist_agent"
        self.version = "1.0.0"
        self.specialization = "Safety & Emergency Response"
        self.created_at = datetime.now()
        
        # Safety protocols database
        self.safety_protocols = self._initialize_safety_protocols()
        
        # Performance tracking
        self.query_count = 0
        self.emergency_responses = 0
        self.incident_reports = 0
        self.training_requests = 0
        self.error_count = 0
        self.total_response_time = 0.0
    
    def _initialize_safety_protocols(self) -> Dict[str, Any]:
        """Initialize safety protocols database"""
        return {
            "emergency_contacts": {
                "911": "Emergency services",
                "poison_control": "1-800-222-1222",
                "osha_hotline": "1-800-321-6742"
            },
            "first_aid_procedures": {
                "burns": {
                    "immediate_actions": [
                        "Remove from heat source",
                        "Cool with running water 10-20 minutes",
                        "Do not apply ice",
                        "Cover with sterile gauze",
                        "Seek medical attention for severe burns"
                    ],
                    "when_to_call_911": [
                        "Burns larger than palm of hand",
                        "Burns on face, hands, feet, or genitals",
                        "Third-degree burns",
                        "Chemical or electrical burns",
                        "Difficulty breathing"
                    ]
                },
                "cuts": {
                    "immediate_actions": [
                        "Apply direct pressure with clean cloth",
                        "Elevate if possible",
                        "Do not remove embedded objects",
                        "Apply bandage once bleeding stops",
                        "Monitor for signs of infection"
                    ],
                    "when_to_call_911": [
                        "Severe bleeding that won't stop",
                        "Deep cuts with visible bone/tendon",
                        "Cuts from contaminated objects",
                        "Signs of shock"
                    ]
                },
                "choking": {
                    "conscious_adult": [
                        "Encourage coughing",
                        "5 back blows between shoulder blades",
                        "5 abdominal thrusts (Heimlich)",
                        "Repeat until object dislodged",
                        "Call 911 if unconscious"
                    ],
                    "unconscious_adult": [
                        "Call 911 immediately",
                        "Begin CPR",
                        "Check mouth for visible objects",
                        "Continue CPR until help arrives"
                    ]
                }
            },
            "fire_procedures": {
                "grease_fire": [
                    "Turn off heat source",
                    "Cover with lid to smother",
                    "Use Class K fire extinguisher",
                    "Never use water on grease fire",
                    "Evacuate if fire spreads"
                ],
                "electrical_fire": [
                    "Turn off power at breaker",
                    "Use Class C fire extinguisher",
                    "Never use water on electrical fire",
                    "Call fire department",
                    "Evacuate if necessary"
                ],
                "evacuation": [
                    "Sound alarm",
                    "Assist customers to exits",
                    "Close doors behind you",
                    "Meet at designated assembly point",
                    "Account for all personnel"
                ]
            },
            "food_safety": {
                "temperature_danger_zone": "40°F - 140°F",
                "safe_cooking_temps": {
                    "poultry": "165°F",
                    "ground_beef": "160°F",
                    "beef_steaks": "145°F",
                    "pork": "145°F",
                    "fish": "145°F"
                },
                "time_limits": {
                    "hot_holding": "2 hours above 140°F",
                    "cold_holding": "4 hours below 40°F",
                    "room_temp": "2 hours maximum"
                }
            },
            "incident_reporting": {
                "immediate_reporting": [
                    "Serious injuries",
                    "Fatalities",
                    "Fires",
                    "Chemical spills",
                    "Equipment failures"
                ],
                "documentation_required": [
                    "Incident report form",
                    "Witness statements",
                    "Photos of scene",
                    "Medical reports",
                    "Corrective actions"
                ],
                "timeline": {
                    "immediate": "Ensure safety and call emergency services",
                    "within_1_hour": "Notify management and document incident",
                    "within_24_hours": "Complete incident report",
                    "within_48_hours": "Submit to regulatory authorities if required"
                }
            }
        }
    
    async def respond_to_emergency(
        self, 
        query: str, 
        context: SafetyContext,
        message_history: List[ModelMessage] = None
    ) -> SafetyResponse:
        """
        Respond to safety emergency with specialized protocols.
        
        Args:
            query: User query about safety incident
            context: Safety context information
            message_history: Previous conversation messages
            
        Returns:
            SafetyResponse with emergency guidance
        """
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Enhance query with safety context
            enhanced_query = self._enhance_query_with_safety_context(query, context)
            
            # Run PydanticAI Agent
            result = await self.agent.run(
                enhanced_query,
                message_history=message_history or []
            )
            
            # Process response for safety-specific information
            response_data = self._process_safety_response(result.data, query, context)
            
            # Update performance metrics
            self.query_count += 1
            if context.severity in [SafetySeverity.CRITICAL, SafetySeverity.EMERGENCY]:
                self.emergency_responses += 1
            
            self.total_response_time += asyncio.get_event_loop().time() - start_time
            
            return response_data
            
        except UnexpectedModelBehavior as e:
            self.error_count += 1
            return SafetyResponse(
                response=f"I encountered an issue processing this safety concern. Please call emergency services immediately if this is a life-threatening situation.",
                incident_type=context.incident_type,
                severity=SafetySeverity.CRITICAL,
                urgency=ResponseUrgency.IMMEDIATE,
                confidence=0.0,
                call_911=True,
                immediate_actions=["Call 911 immediately", "Ensure area is safe", "Provide first aid if trained"]
            )
            
        except ModelRetry as e:
            self.error_count += 1
            return SafetyResponse(
                response=f"I'm having trouble processing this safety request. If this is an emergency, call 911 immediately.",
                incident_type=context.incident_type,
                severity=context.severity,
                urgency=ResponseUrgency.IMMEDIATE,
                confidence=0.0,
                call_911=True if context.severity == SafetySeverity.EMERGENCY else False
            )
            
        except Exception as e:
            self.error_count += 1
            return SafetyResponse(
                response=f"I'm experiencing technical difficulties with safety protocols. Call 911 immediately if this is an emergency.",
                incident_type=context.incident_type,
                severity=SafetySeverity.CRITICAL,
                urgency=ResponseUrgency.IMMEDIATE,
                confidence=0.0,
                call_911=True,
                immediate_actions=["Call 911 if emergency", "Ensure area is safe", "Contact management"]
            )
    
    async def get_safety_protocol(self, incident_type: SafetyIncidentType) -> Dict[str, Any]:
        """Get safety protocol for specific incident type"""
        
        protocol_key = incident_type.value
        
        # Get relevant protocol from database
        if protocol_key in self.safety_protocols.get("first_aid_procedures", {}):
            protocol = self.safety_protocols["first_aid_procedures"][protocol_key]
        elif protocol_key in self.safety_protocols.get("fire_procedures", {}):
            protocol = self.safety_protocols["fire_procedures"][protocol_key]
        else:
            protocol = {
                "error": f"Protocol not found for {protocol_key}",
                "general_guidance": "Contact emergency services and follow general safety procedures"
            }
        
        return {
            "incident_type": incident_type.value,
            "protocol": protocol,
            "emergency_contacts": self.safety_protocols["emergency_contacts"],
            "generated_at": datetime.now().isoformat()
        }
    
    def _enhance_query_with_safety_context(self, query: str, context: SafetyContext) -> str:
        """Enhance query with safety-specific context"""
        
        enhanced_parts = [query]
        
        # Add incident type and severity
        enhanced_parts.append(f"\nIncident Type: {context.incident_type.value}")
        enhanced_parts.append(f"Severity: {context.severity.value}")
        
        # Add location and personnel information
        enhanced_parts.append(f"Location: {context.location}")
        if context.injured_persons > 0:
            enhanced_parts.append(f"Injured Persons: {context.injured_persons}")
        if context.witnesses > 0:
            enhanced_parts.append(f"Witnesses: {context.witnesses}")
        
        # Add immediate danger status
        if context.immediate_danger:
            enhanced_parts.append("IMMEDIATE DANGER PRESENT")
        
        # Add equipment information
        if context.equipment_involved:
            enhanced_parts.append(f"Equipment Involved: {context.equipment_involved}")
        
        # Add emergency services status
        if context.emergency_services_called:
            enhanced_parts.append("Emergency Services Already Called")
        
        # Add time information
        if context.time_of_incident:
            enhanced_parts.append(f"Time of Incident: {context.time_of_incident.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add relevant safety protocol context
        protocol_key = context.incident_type.value
        if protocol_key in self.safety_protocols.get("first_aid_procedures", {}):
            protocol = self.safety_protocols["first_aid_procedures"][protocol_key]
            enhanced_parts.append(f"\nRelevant Safety Protocol: {protocol}")
        
        return "\n".join(enhanced_parts)
    
    def _process_safety_response(self, response_text: str, original_query: str, context: SafetyContext) -> SafetyResponse:
        """Process raw response into structured SafetyResponse"""
        
        # Extract safety-specific information
        immediate_actions = self._extract_immediate_actions(response_text)
        safety_procedures = self._extract_safety_procedures(response_text)
        ppe_required = self._extract_ppe_requirements(response_text)
        equipment_shutdown = self._extract_equipment_shutdown(response_text)
        prevention_measures = self._extract_prevention_measures(response_text)
        regulations_cited = self._extract_regulations(response_text)
        
        # Determine emergency response requirements
        call_911 = self._requires_911_call(response_text, context)
        call_emergency_services = self._requires_emergency_services(response_text, context)
        evacuation_required = self._requires_evacuation(response_text, context)
        
        # Determine urgency
        urgency = self._determine_response_urgency(response_text, context)
        
        # Determine follow-up requirements
        medical_attention_required = self._requires_medical_attention(response_text, context)
        investigation_required = self._requires_investigation(response_text, context)
        training_required = self._requires_training(response_text, context)
        
        # Extract documentation requirements
        incident_reporting_required = self._requires_incident_reporting(response_text, context)
        documentation_timeline = self._determine_documentation_timeline(response_text, context)
        regulatory_notifications = self._extract_regulatory_notifications(response_text, context)
        
        # Calculate confidence score
        confidence = self._calculate_safety_confidence(response_text, context)
        
        return SafetyResponse(
            response=response_text,
            incident_type=context.incident_type,
            severity=context.severity,
            urgency=urgency,
            confidence=confidence,
            immediate_actions=immediate_actions,
            call_911=call_911,
            call_emergency_services=call_emergency_services,
            evacuation_required=evacuation_required,
            safety_procedures=safety_procedures,
            ppe_required=ppe_required,
            equipment_shutdown=equipment_shutdown,
            incident_reporting_required=incident_reporting_required,
            documentation_timeline=documentation_timeline,
            regulatory_notifications=regulatory_notifications,
            medical_attention_required=medical_attention_required,
            investigation_required=investigation_required,
            training_required=training_required,
            prevention_measures=prevention_measures,
            regulations_cited=regulations_cited
        )
    
    def _extract_immediate_actions(self, response: str) -> List[str]:
        """Extract immediate actions from response"""
        
        actions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ["immediately", "first", "urgent", "emergency"]):
                if line.startswith(('1.', '2.', '3.', '•', '-', '*')):
                    actions.append(line)
        
        return actions
    
    def _extract_safety_procedures(self, response: str) -> List[str]:
        """Extract safety procedures from response"""
        
        procedures = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ["procedure", "protocol", "step", "process"]):
                procedures.append(line)
        
        return procedures
    
    def _extract_ppe_requirements(self, response: str) -> List[str]:
        """Extract PPE requirements from response"""
        
        ppe_items = []
        response_lower = response.lower()
        
        # Common PPE items
        ppe_types = [
            "gloves", "safety glasses", "hard hat", "safety shoes",
            "apron", "face mask", "respirator", "hearing protection"
        ]
        
        for ppe in ppe_types:
            if ppe in response_lower:
                ppe_items.append(ppe.title())
        
        return ppe_items
    
    def _extract_equipment_shutdown(self, response: str) -> List[str]:
        """Extract equipment shutdown requirements"""
        
        shutdown_items = []
        response_lower = response.lower()
        
        if any(keyword in response_lower for keyword in ["shutdown", "turn off", "stop", "disable"]):
            lines = response.split('\n')
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ["shutdown", "turn off", "stop", "disable"]):
                    shutdown_items.append(line.strip())
        
        return shutdown_items
    
    def _extract_prevention_measures(self, response: str) -> List[str]:
        """Extract prevention measures from response"""
        
        measures = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["prevent", "avoid", "training", "maintenance"]):
                measures.append(line.strip())
        
        return measures
    
    def _extract_regulations(self, response: str) -> List[str]:
        """Extract cited regulations from response"""
        
        regulations = []
        response_lower = response.lower()
        
        # Common regulations
        regulation_types = ["osha", "fda", "haccp", "health department", "building code"]
        
        for regulation in regulation_types:
            if regulation in response_lower:
                regulations.append(regulation.upper())
        
        return regulations
    
    def _requires_911_call(self, response: str, context: SafetyContext) -> bool:
        """Determine if 911 call is required"""
        
        if context.severity == SafetySeverity.EMERGENCY:
            return True
        
        if context.immediate_danger:
            return True
        
        response_lower = response.lower()
        emergency_keywords = ["call 911", "emergency services", "life threatening", "serious injury"]
        
        return any(keyword in response_lower for keyword in emergency_keywords)
    
    def _requires_emergency_services(self, response: str, context: SafetyContext) -> bool:
        """Determine if emergency services are required"""
        
        if context.severity in [SafetySeverity.HIGH, SafetySeverity.CRITICAL, SafetySeverity.EMERGENCY]:
            return True
        
        response_lower = response.lower()
        service_keywords = ["fire department", "paramedics", "police", "emergency", "medical attention"]
        
        return any(keyword in response_lower for keyword in service_keywords)
    
    def _requires_evacuation(self, response: str, context: SafetyContext) -> bool:
        """Determine if evacuation is required"""
        
        if context.incident_type == SafetyIncidentType.FIRE:
            return True
        
        response_lower = response.lower()
        evacuation_keywords = ["evacuate", "leave the area", "clear the building", "exit"]
        
        return any(keyword in response_lower for keyword in evacuation_keywords)
    
    def _determine_response_urgency(self, response: str, context: SafetyContext) -> ResponseUrgency:
        """Determine response urgency"""
        
        if context.severity == SafetySeverity.EMERGENCY:
            return ResponseUrgency.IMMEDIATE
        
        response_lower = response.lower()
        
        if any(keyword in response_lower for keyword in ["immediate", "emergency", "urgent"]):
            return ResponseUrgency.IMMEDIATE
        elif any(keyword in response_lower for keyword in ["quickly", "soon", "priority"]):
            return ResponseUrgency.URGENT
        elif any(keyword in response_lower for keyword in ["prevent", "training", "maintenance"]):
            return ResponseUrgency.PREVENTIVE
        
        return ResponseUrgency.NORMAL
    
    def _requires_medical_attention(self, response: str, context: SafetyContext) -> bool:
        """Determine if medical attention is required"""
        
        if context.injured_persons > 0:
            return True
        
        response_lower = response.lower()
        medical_keywords = ["medical", "doctor", "hospital", "first aid", "injury"]
        
        return any(keyword in response_lower for keyword in medical_keywords)
    
    def _requires_investigation(self, response: str, context: SafetyContext) -> bool:
        """Determine if investigation is required"""
        
        if context.severity in [SafetySeverity.HIGH, SafetySeverity.CRITICAL, SafetySeverity.EMERGENCY]:
            return True
        
        response_lower = response.lower()
        investigation_keywords = ["investigate", "root cause", "analysis", "review"]
        
        return any(keyword in response_lower for keyword in investigation_keywords)
    
    def _requires_training(self, response: str, context: SafetyContext) -> bool:
        """Determine if training is required"""
        
        response_lower = response.lower()
        training_keywords = ["training", "education", "certification", "learn"]
        
        return any(keyword in response_lower for keyword in training_keywords)
    
    def _requires_incident_reporting(self, response: str, context: SafetyContext) -> bool:
        """Determine if incident reporting is required"""
        
        # Most incidents require reporting
        if context.severity != SafetySeverity.LOW:
            return True
        
        response_lower = response.lower()
        reporting_keywords = ["report", "document", "notify", "record"]
        
        return any(keyword in response_lower for keyword in reporting_keywords)
    
    def _determine_documentation_timeline(self, response: str, context: SafetyContext) -> Optional[str]:
        """Determine documentation timeline"""
        
        if context.severity == SafetySeverity.EMERGENCY:
            return "immediately after ensuring safety"
        elif context.severity == SafetySeverity.CRITICAL:
            return "within 1 hour"
        elif context.severity == SafetySeverity.HIGH:
            return "within 24 hours"
        
        return "within 48 hours"
    
    def _extract_regulatory_notifications(self, response: str, context: SafetyContext) -> List[str]:
        """Extract regulatory notification requirements"""
        
        notifications = []
        
        if context.severity in [SafetySeverity.CRITICAL, SafetySeverity.EMERGENCY]:
            notifications.append("OSHA")
        
        if context.incident_type == SafetyIncidentType.FOOD_CONTAMINATION:
            notifications.append("Health Department")
        
        if context.incident_type == SafetyIncidentType.FIRE:
            notifications.append("Fire Department")
        
        return notifications
    
    def _calculate_safety_confidence(self, response: str, context: SafetyContext) -> float:
        """Calculate confidence score for safety response"""
        
        confidence = 0.9  # High base confidence for safety
        
        # Increase confidence for emergency protocols
        if context.severity in [SafetySeverity.CRITICAL, SafetySeverity.EMERGENCY]:
            confidence += 0.05
        
        # Increase confidence for structured responses
        if any(marker in response for marker in ["1.", "2.", "3.", "•", "-"]):
            confidence += 0.03
        
        # Increase confidence for safety keywords
        safety_keywords = ["safety", "emergency", "procedure", "protocol"]
        for keyword in safety_keywords:
            if keyword in response.lower():
                confidence += 0.01
        
        return min(1.0, confidence)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get safety agent performance metrics"""
        
        avg_response_time = self.total_response_time / self.query_count if self.query_count > 0 else 0
        
        return {
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "version": self.version,
            "query_count": self.query_count,
            "emergency_responses": self.emergency_responses,
            "incident_reports": self.incident_reports,
            "training_requests": self.training_requests,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.query_count if self.query_count > 0 else 0,
            "average_response_time": avg_response_time,
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "model": str(self.agent.model)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the safety agent"""
        
        try:
            # Test basic functionality
            test_context = SafetyContext(
                incident_type=SafetyIncidentType.BURN,
                severity=SafetySeverity.MODERATE,
                location="Kitchen",
                injured_persons=1
            )
            
            test_result = await self.respond_to_emergency("Test safety query", test_context)
            
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

# Global safety agent instance
safety_agent = SafetySpecialistAgent()

# Factory function
def create_safety_agent(model: str = None) -> SafetySpecialistAgent:
    """Factory function to create safety agents"""
    return SafetySpecialistAgent(model=model)

# Async factory function
async def create_safety_agent_async(model: str = None) -> SafetySpecialistAgent:
    """Async factory function to create safety agents"""
    agent = SafetySpecialistAgent(model=model)
    
    # Perform health check
    health_status = await agent.health_check()
    
    if health_status["status"] != "healthy":
        raise Exception(f"Safety agent health check failed: {health_status.get('error', 'Unknown error')}")
    
    return agent

if __name__ == "__main__":
    # Test the safety agent
    async def test_safety_agent():
        agent = await create_safety_agent_async()
        
        # Test burn emergency
        context = SafetyContext(
            incident_type=SafetyIncidentType.BURN,
            severity=SafetySeverity.HIGH,
            location="Kitchen fryer station",
            injured_persons=1,
            immediate_danger=False,
            equipment_involved="Vulcan fryer"
        )
        
        response = await agent.respond_to_emergency(
            "An employee just got burned by hot oil from the fryer. There's a severe burn on their arm.",
            context
        )
        
        print("Safety Emergency Response:")
        print(f"Response: {response.response}")
        print(f"Incident Type: {response.incident_type.value}")
        print(f"Severity: {response.severity.value}")
        print(f"Urgency: {response.urgency.value}")
        print(f"Call 911: {response.call_911}")
        print(f"Immediate Actions: {response.immediate_actions}")
        print(f"Medical Attention Required: {response.medical_attention_required}")
        print(f"Investigation Required: {response.investigation_required}")
        print()
        
        # Test safety protocol
        protocol = await agent.get_safety_protocol(SafetyIncidentType.BURN)
        print("Safety Protocol:")
        print(protocol)
        print()
        
        # Performance metrics
        print("Performance Metrics:")
        print(agent.get_performance_metrics())
    
    asyncio.run(test_safety_agent())