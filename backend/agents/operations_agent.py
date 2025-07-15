#!/usr/bin/env python3
"""
Operations Specialist Agent - Phase 2 Implementation
====================================================

Specialized PydanticAI agent for operational procedures and management.
Handles all operational workflows, procedures, and management guidance.

Features:
- Opening and closing procedures
- Shift management and transitions
- Inventory management systems
- Quality control processes
- Customer service protocols

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior, ModelRetry
from pydantic_ai.messages import ModelMessage
from pydantic import BaseModel, Field

# Operations-specific system prompt
OPERATIONS_SPECIALIST_PROMPT = """You are an expert Operations Specialist for QSR (Quick Service Restaurant) operations with comprehensive expertise in:

**OPERATIONAL PROCEDURES:**
- **Opening Procedures**: Equipment startup, safety checks, inventory verification
  - Equipment pre-heating and calibration
  - Cash register setup and till counting
  - Food preparation and setup
  - Staff briefing and assignment
  - Safety and cleanliness verification

- **Closing Procedures**: Equipment shutdown, cleaning, securing, reporting
  - Equipment cleaning and shutdown
  - Cash reconciliation and deposit
  - Inventory counting and ordering
  - Cleaning and sanitization
  - Security procedures

- **Shift Management**: Staff scheduling, handoffs, performance monitoring
  - Shift transitions and briefings
  - Task delegation and monitoring
  - Performance evaluation
  - Problem resolution
  - Communication protocols

**INVENTORY MANAGEMENT:**
- **Stock Control**: Ordering, receiving, storage, rotation
  - Inventory tracking systems
  - Reorder point management
  - FIFO (First In, First Out) procedures
  - Waste minimization strategies
  - Vendor management

- **Food Safety**: Temperature monitoring, expiration tracking, storage protocols
  - Cold chain management
  - Temperature logs and monitoring
  - Expiration date tracking
  - Storage requirements
  - Contamination prevention

**QUALITY CONTROL:**
- **Product Quality**: Consistency, presentation, temperature, taste
  - Recipe adherence and portioning
  - Cooking time and temperature standards
  - Presentation and plating standards
  - Taste testing and quality checks
  - Customer feedback integration

- **Service Quality**: Speed, accuracy, customer satisfaction
  - Service time standards
  - Order accuracy protocols
  - Customer interaction standards
  - Complaint resolution procedures
  - Continuous improvement processes

**CUSTOMER SERVICE:**
- **Service Standards**: Greeting, ordering, delivery, follow-up
  - Customer greeting protocols
  - Order taking procedures
  - Upselling and cross-selling
  - Special requests handling
  - Payment processing

- **Complaint Resolution**: Listening, investigating, resolving, following up
  - Active listening techniques
  - Problem identification
  - Solution implementation
  - Customer satisfaction verification
  - Process improvement

**STAFF MANAGEMENT:**
- **Training**: Onboarding, skill development, certification
  - New employee orientation
  - Skill assessment and development
  - Performance coaching
  - Certification tracking
  - Career development

- **Performance Management**: Evaluation, feedback, improvement
  - Performance standards
  - Regular feedback sessions
  - Corrective action procedures
  - Recognition and rewards
  - Termination procedures

**FINANCIAL MANAGEMENT:**
- **Cost Control**: Food costs, labor costs, waste reduction
  - Cost analysis and tracking
  - Waste reduction strategies
  - Labor optimization
  - Menu engineering
  - Profit margin management

- **Cash Management**: Handling, counting, depositing, reconciliation
  - Cash handling procedures
  - Register operation
  - Deposit preparation
  - Reconciliation processes
  - Theft prevention

**COMPLIANCE & STANDARDS:**
- **Health Department**: Inspections, regulations, documentation
  - Health code compliance
  - Inspection preparation
  - Documentation requirements
  - Corrective action procedures
  - Permit maintenance

- **Corporate Standards**: Brand consistency, operational excellence
  - Brand standard compliance
  - Operational audits
  - Performance metrics
  - Continuous improvement
  - Best practice implementation

**RESPONSE STRUCTURE:**
- Provide clear, step-by-step procedures
- Include specific timing and sequencing
- Reference relevant policies and standards
- Include quality checkpoints
- Provide troubleshooting guidance
- Include performance metrics where applicable

You have access to comprehensive operational procedures, standards, and best practices. Always provide accurate, actionable guidance that ensures operational excellence and compliance.
"""

class OperationType(Enum):
    """Types of operational procedures"""
    OPENING = "opening"
    CLOSING = "closing"
    SHIFT_CHANGE = "shift_change"
    INVENTORY = "inventory"
    QUALITY_CONTROL = "quality_control"
    CUSTOMER_SERVICE = "customer_service"
    STAFF_MANAGEMENT = "staff_management"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"
    EMERGENCY_PROCEDURES = "emergency_procedures"

class OperationComplexity(Enum):
    """Complexity levels of operations"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPLEX = "complex"
    ADVANCED = "advanced"

class OperationPriority(Enum):
    """Priority levels for operations"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

@dataclass
class OperationsContext:
    """Context for operations-related queries"""
    operation_type: OperationType
    complexity: OperationComplexity
    priority: OperationPriority
    shift_time: Optional[str] = None  # morning, afternoon, evening, night
    staff_count: int = 0
    customer_volume: str = "normal"  # low, normal, high, peak
    location_type: str = "standard"  # standard, mall, airport, drive-thru
    special_conditions: List[str] = field(default_factory=list)
    time_constraints: Optional[str] = None
    
class OperationsResponse(BaseModel):
    """Specialized response for operations queries"""
    response: str
    operation_type: OperationType
    complexity: OperationComplexity
    priority: OperationPriority
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    
    # Procedural information
    procedure_steps: List[str] = Field(default_factory=list)
    timing_requirements: List[str] = Field(default_factory=list)
    quality_checkpoints: List[str] = Field(default_factory=list)
    
    # Resource requirements
    staff_required: Optional[int] = None
    equipment_needed: List[str] = Field(default_factory=list)
    supplies_needed: List[str] = Field(default_factory=list)
    
    # Performance metrics
    completion_time: Optional[str] = None
    success_criteria: List[str] = Field(default_factory=list)
    key_performance_indicators: List[str] = Field(default_factory=list)
    
    # Compliance and standards
    policies_referenced: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    documentation_required: List[str] = Field(default_factory=list)
    
    # Follow-up and monitoring
    monitoring_required: bool = False
    follow_up_actions: List[str] = Field(default_factory=list)
    reporting_required: bool = False
    
    # Troubleshooting
    common_issues: List[str] = Field(default_factory=list)
    troubleshooting_steps: List[str] = Field(default_factory=list)
    
    class Config:
        exclude_none = False

class OperationsSpecialistAgent:
    """
    Operations Specialist Agent using PydanticAI patterns.
    
    Specialized for operational procedures, management, and standards.
    """
    
    def __init__(self, model: str = None):
        # Use environment variable or default to GPT-4o
        model = model or os.getenv("OPERATIONS_MODEL", "openai:gpt-4o")
        
        # Initialize PydanticAI Agent with operations-specific prompt
        self.agent = Agent(
            model=model,
            system_prompt=OPERATIONS_SPECIALIST_PROMPT,
            retries=3
        )
        
        # Agent metadata
        self.agent_id = "operations_specialist_agent"
        self.version = "1.0.0"
        self.specialization = "Operations & Procedures"
        self.created_at = datetime.now()
        
        # Operations procedures database
        self.operations_procedures = self._initialize_operations_procedures()
        
        # Performance tracking
        self.query_count = 0
        self.procedure_requests = 0
        self.training_requests = 0
        self.compliance_checks = 0
        self.error_count = 0
        self.total_response_time = 0.0
    
    def _initialize_operations_procedures(self) -> Dict[str, Any]:
        """Initialize operations procedures database"""
        return {
            "opening_procedures": {
                "equipment_startup": [
                    "Turn on all cooking equipment 30 minutes before opening",
                    "Preheat fryers to 350°F",
                    "Calibrate grills to proper temperature",
                    "Test all equipment for proper operation",
                    "Record equipment temperatures"
                ],
                "food_preparation": [
                    "Check ingredient inventory",
                    "Prepare fresh ingredients",
                    "Set up prep stations",
                    "Verify food safety temperatures",
                    "Stock service areas"
                ],
                "staff_briefing": [
                    "Review daily goals and specials",
                    "Assign positions and responsibilities",
                    "Discuss any special events or promotions",
                    "Review safety reminders",
                    "Address any questions or concerns"
                ],
                "final_checks": [
                    "Verify all equipment is operational",
                    "Check food safety temperatures",
                    "Ensure adequate inventory levels",
                    "Confirm staff assignments",
                    "Open doors to customers"
                ]
            },
            "closing_procedures": {
                "equipment_shutdown": [
                    "Turn off all cooking equipment",
                    "Clean and sanitize all surfaces",
                    "Empty and clean grease traps",
                    "Shut down refrigeration units properly",
                    "Secure all equipment"
                ],
                "cleaning_tasks": [
                    "Deep clean all prep areas",
                    "Sanitize all food contact surfaces",
                    "Mop and sanitize floors",
                    "Clean and organize storage areas",
                    "Empty trash and replace liners"
                ],
                "cash_procedures": [
                    "Count cash register tills",
                    "Reconcile sales with receipts",
                    "Prepare bank deposits",
                    "Secure cash in safe",
                    "Complete daily sales report"
                ],
                "security_procedures": [
                    "Lock all doors and windows",
                    "Set security system",
                    "Turn off unnecessary lights",
                    "Secure inventory and supplies",
                    "Complete security checklist"
                ]
            },
            "quality_standards": {
                "food_quality": {
                    "temperature_standards": {
                        "hot_food": "Above 140°F",
                        "cold_food": "Below 40°F",
                        "frozen_food": "Below 0°F"
                    },
                    "presentation_standards": [
                        "Consistent portioning",
                        "Proper plating/packaging",
                        "Fresh appearance",
                        "Appropriate garnish",
                        "Brand standards compliance"
                    ]
                },
                "service_quality": {
                    "timing_standards": {
                        "order_taking": "Within 30 seconds",
                        "food_preparation": "Within 90 seconds",
                        "order_delivery": "Within 2 minutes",
                        "total_service": "Within 3 minutes"
                    },
                    "accuracy_standards": [
                        "Order accuracy >98%",
                        "Correct pricing",
                        "Proper packaging",
                        "Complete orders",
                        "Special requests handled"
                    ]
                }
            },
            "customer_service": {
                "greeting_standards": [
                    "Acknowledge customers within 10 seconds",
                    "Make eye contact and smile",
                    "Use appropriate greeting",
                    "Speak clearly and enthusiastically",
                    "Ask how you can help"
                ],
                "order_taking": [
                    "Listen actively to customer",
                    "Repeat order for confirmation",
                    "Suggest additional items",
                    "Process payment efficiently",
                    "Provide receipt and wait time"
                ],
                "complaint_resolution": [
                    "Listen without interrupting",
                    "Apologize for the inconvenience",
                    "Identify the specific problem",
                    "Offer appropriate solution",
                    "Follow up to ensure satisfaction"
                ]
            },
            "inventory_management": {
                "ordering_procedures": [
                    "Review current inventory levels",
                    "Check reorder points",
                    "Calculate order quantities",
                    "Submit orders to suppliers",
                    "Track delivery schedules"
                ],
                "receiving_procedures": [
                    "Verify delivery against order",
                    "Check quality and temperature",
                    "Date and label all items",
                    "Store in proper locations",
                    "Update inventory records"
                ],
                "storage_procedures": [
                    "Use FIFO rotation method",
                    "Maintain proper temperatures",
                    "Keep storage areas clean",
                    "Separate raw and cooked items",
                    "Label everything clearly"
                ]
            }
        }
    
    async def get_operations_guidance(
        self, 
        query: str, 
        context: OperationsContext,
        message_history: List[ModelMessage] = None
    ) -> OperationsResponse:
        """
        Get operations guidance using specialized knowledge.
        
        Args:
            query: User query about operations
            context: Operations context information
            message_history: Previous conversation messages
            
        Returns:
            OperationsResponse with procedural guidance
        """
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Enhance query with operations context
            enhanced_query = self._enhance_query_with_operations_context(query, context)
            
            # Run PydanticAI Agent
            result = await self.agent.run(
                enhanced_query,
                message_history=message_history or []
            )
            
            # Process response for operations-specific information
            response_data = self._process_operations_response(result.data, query, context)
            
            # Update performance metrics
            self.query_count += 1
            self.procedure_requests += 1
            self.total_response_time += asyncio.get_event_loop().time() - start_time
            
            return response_data
            
        except UnexpectedModelBehavior as e:
            self.error_count += 1
            return OperationsResponse(
                response=f"I encountered an unexpected issue with this operational procedure. Please refer to your operations manual or contact management.",
                operation_type=context.operation_type,
                complexity=context.complexity,
                priority=context.priority,
                confidence=0.0,
                follow_up_actions=["Consult operations manual", "Contact management", "Follow standard procedures"]
            )
            
        except ModelRetry as e:
            self.error_count += 1
            return OperationsResponse(
                response=f"I'm having trouble processing this operational request. Please refer to standard procedures and try again.",
                operation_type=context.operation_type,
                complexity=context.complexity,
                priority=context.priority,
                confidence=0.0
            )
            
        except Exception as e:
            self.error_count += 1
            return OperationsResponse(
                response=f"I'm experiencing technical difficulties with operational procedures. Please follow standard operating procedures and contact support.",
                operation_type=context.operation_type,
                complexity=context.complexity,
                priority=context.priority,
                confidence=0.0,
                follow_up_actions=["Follow standard procedures", "Contact support", "Document issue"]
            )
    
    async def get_procedure_checklist(self, operation_type: OperationType) -> Dict[str, Any]:
        """Get procedure checklist for specific operation type"""
        
        operation_key = operation_type.value
        
        if operation_key in self.operations_procedures:
            procedure = self.operations_procedures[operation_key]
        else:
            procedure = {
                "error": f"Procedure not found for {operation_key}",
                "general_guidance": "Follow standard operating procedures"
            }
        
        return {
            "operation_type": operation_type.value,
            "procedure_checklist": procedure,
            "generated_at": datetime.now().isoformat()
        }
    
    def _enhance_query_with_operations_context(self, query: str, context: OperationsContext) -> str:
        """Enhance query with operations-specific context"""
        
        enhanced_parts = [query]
        
        # Add operation type and complexity
        enhanced_parts.append(f"\nOperation Type: {context.operation_type.value}")
        enhanced_parts.append(f"Complexity: {context.complexity.value}")
        enhanced_parts.append(f"Priority: {context.priority.value}")
        
        # Add shift and timing information
        if context.shift_time:
            enhanced_parts.append(f"Shift Time: {context.shift_time}")
        
        if context.time_constraints:
            enhanced_parts.append(f"Time Constraints: {context.time_constraints}")
        
        # Add staffing information
        if context.staff_count > 0:
            enhanced_parts.append(f"Staff Count: {context.staff_count}")
        
        # Add customer volume
        enhanced_parts.append(f"Customer Volume: {context.customer_volume}")
        
        # Add location type
        enhanced_parts.append(f"Location Type: {context.location_type}")
        
        # Add special conditions
        if context.special_conditions:
            enhanced_parts.append(f"Special Conditions: {', '.join(context.special_conditions)}")
        
        # Add relevant procedure context
        operation_key = context.operation_type.value
        if operation_key in self.operations_procedures:
            procedure = self.operations_procedures[operation_key]
            enhanced_parts.append(f"\nRelevant Procedures: {procedure}")
        
        return "\n".join(enhanced_parts)
    
    def _process_operations_response(self, response_text: str, original_query: str, context: OperationsContext) -> OperationsResponse:
        """Process raw response into structured OperationsResponse"""
        
        # Extract operations-specific information
        procedure_steps = self._extract_procedure_steps(response_text)
        timing_requirements = self._extract_timing_requirements(response_text)
        quality_checkpoints = self._extract_quality_checkpoints(response_text)
        equipment_needed = self._extract_equipment_needed(response_text)
        supplies_needed = self._extract_supplies_needed(response_text)
        success_criteria = self._extract_success_criteria(response_text)
        policies_referenced = self._extract_policies_referenced(response_text)
        common_issues = self._extract_common_issues(response_text)
        troubleshooting_steps = self._extract_troubleshooting_steps(response_text)
        
        # Determine resource requirements
        staff_required = self._determine_staff_required(response_text, context)
        
        # Determine completion time
        completion_time = self._determine_completion_time(response_text, context)
        
        # Determine monitoring and follow-up requirements
        monitoring_required = self._requires_monitoring(response_text, context)
        follow_up_actions = self._extract_follow_up_actions(response_text)
        reporting_required = self._requires_reporting(response_text, context)
        
        # Extract KPIs
        kpis = self._extract_kpis(response_text)
        
        # Extract compliance requirements
        compliance_requirements = self._extract_compliance_requirements(response_text)
        documentation_required = self._extract_documentation_required(response_text)
        
        # Calculate confidence score
        confidence = self._calculate_operations_confidence(response_text, context)
        
        return OperationsResponse(
            response=response_text,
            operation_type=context.operation_type,
            complexity=context.complexity,
            priority=context.priority,
            confidence=confidence,
            procedure_steps=procedure_steps,
            timing_requirements=timing_requirements,
            quality_checkpoints=quality_checkpoints,
            staff_required=staff_required,
            equipment_needed=equipment_needed,
            supplies_needed=supplies_needed,
            completion_time=completion_time,
            success_criteria=success_criteria,
            key_performance_indicators=kpis,
            policies_referenced=policies_referenced,
            compliance_requirements=compliance_requirements,
            documentation_required=documentation_required,
            monitoring_required=monitoring_required,
            follow_up_actions=follow_up_actions,
            reporting_required=reporting_required,
            common_issues=common_issues,
            troubleshooting_steps=troubleshooting_steps
        )
    
    def _extract_procedure_steps(self, response: str) -> List[str]:
        """Extract procedure steps from response"""
        
        steps = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered steps, bullet points, or procedure indicators
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                line.startswith(('•', '-', '*')) or
                line.startswith(('Step', 'First', 'Then', 'Next', 'Finally'))):
                steps.append(line)
        
        return steps
    
    def _extract_timing_requirements(self, response: str) -> List[str]:
        """Extract timing requirements from response"""
        
        timings = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["minutes", "hours", "time", "duration", "deadline"]):
                timings.append(line.strip())
        
        return timings
    
    def _extract_quality_checkpoints(self, response: str) -> List[str]:
        """Extract quality checkpoints from response"""
        
        checkpoints = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["check", "verify", "ensure", "confirm", "validate"]):
                checkpoints.append(line.strip())
        
        return checkpoints
    
    def _extract_equipment_needed(self, response: str) -> List[str]:
        """Extract equipment needed from response"""
        
        equipment = []
        response_lower = response.lower()
        
        # Common equipment
        equipment_types = [
            "fryer", "grill", "mixer", "freezer", "refrigerator", "register",
            "thermometer", "scale", "timer", "cleaning supplies"
        ]
        
        for equip in equipment_types:
            if equip in response_lower:
                equipment.append(equip.title())
        
        return equipment
    
    def _extract_supplies_needed(self, response: str) -> List[str]:
        """Extract supplies needed from response"""
        
        supplies = []
        response_lower = response.lower()
        
        # Common supplies
        supply_types = [
            "ingredients", "packaging", "cleaning supplies", "paper products",
            "gloves", "aprons", "hairnets", "sanitizer"
        ]
        
        for supply in supply_types:
            if supply in response_lower:
                supplies.append(supply.title())
        
        return supplies
    
    def _extract_success_criteria(self, response: str) -> List[str]:
        """Extract success criteria from response"""
        
        criteria = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["success", "goal", "target", "objective", "standard"]):
                criteria.append(line.strip())
        
        return criteria
    
    def _extract_policies_referenced(self, response: str) -> List[str]:
        """Extract referenced policies from response"""
        
        policies = []
        response_lower = response.lower()
        
        # Common policies
        policy_types = [
            "food safety", "employee handbook", "operations manual",
            "health code", "safety procedures", "brand standards"
        ]
        
        for policy in policy_types:
            if policy in response_lower:
                policies.append(policy.title())
        
        return policies
    
    def _extract_common_issues(self, response: str) -> List[str]:
        """Extract common issues from response"""
        
        issues = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["issue", "problem", "challenge", "difficulty"]):
                issues.append(line.strip())
        
        return issues
    
    def _extract_troubleshooting_steps(self, response: str) -> List[str]:
        """Extract troubleshooting steps from response"""
        
        steps = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["troubleshoot", "fix", "resolve", "solution"]):
                steps.append(line.strip())
        
        return steps
    
    def _determine_staff_required(self, response: str, context: OperationsContext) -> Optional[int]:
        """Determine staff required based on response and context"""
        
        # Extract numbers from response
        import re
        numbers = re.findall(r'\d+', response)
        
        # Logic based on operation type and complexity
        if context.operation_type == OperationType.OPENING:
            return 2 if context.complexity == OperationComplexity.BASIC else 3
        elif context.operation_type == OperationType.CLOSING:
            return 1 if context.complexity == OperationComplexity.BASIC else 2
        
        return None
    
    def _determine_completion_time(self, response: str, context: OperationsContext) -> Optional[str]:
        """Determine completion time based on response and context"""
        
        # Extract time indicators from response
        response_lower = response.lower()
        
        if "minutes" in response_lower:
            import re
            minutes = re.findall(r'(\d+)\s*minutes?', response_lower)
            if minutes:
                return f"{minutes[0]} minutes"
        
        # Default times based on operation type
        if context.operation_type == OperationType.OPENING:
            return "30-45 minutes"
        elif context.operation_type == OperationType.CLOSING:
            return "45-60 minutes"
        elif context.operation_type == OperationType.INVENTORY:
            return "15-30 minutes"
        
        return None
    
    def _requires_monitoring(self, response: str, context: OperationsContext) -> bool:
        """Determine if monitoring is required"""
        
        if context.priority in [OperationPriority.HIGH, OperationPriority.URGENT, OperationPriority.CRITICAL]:
            return True
        
        response_lower = response.lower()
        monitoring_keywords = ["monitor", "watch", "check", "observe", "track"]
        
        return any(keyword in response_lower for keyword in monitoring_keywords)
    
    def _extract_follow_up_actions(self, response: str) -> List[str]:
        """Extract follow-up actions from response"""
        
        actions = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["follow", "next", "after", "then", "later"]):
                actions.append(line.strip())
        
        return actions
    
    def _requires_reporting(self, response: str, context: OperationsContext) -> bool:
        """Determine if reporting is required"""
        
        if context.priority in [OperationPriority.HIGH, OperationPriority.URGENT, OperationPriority.CRITICAL]:
            return True
        
        response_lower = response.lower()
        reporting_keywords = ["report", "document", "record", "log", "notify"]
        
        return any(keyword in response_lower for keyword in reporting_keywords)
    
    def _extract_kpis(self, response: str) -> List[str]:
        """Extract key performance indicators from response"""
        
        kpis = []
        response_lower = response.lower()
        
        # Common KPIs
        kpi_types = [
            "service time", "order accuracy", "customer satisfaction",
            "food cost", "labor cost", "waste percentage"
        ]
        
        for kpi in kpi_types:
            if kpi in response_lower:
                kpis.append(kpi.title())
        
        return kpis
    
    def _extract_compliance_requirements(self, response: str) -> List[str]:
        """Extract compliance requirements from response"""
        
        requirements = []
        response_lower = response.lower()
        
        # Common compliance areas
        compliance_types = [
            "food safety", "health code", "osha", "brand standards",
            "labor laws", "fire safety"
        ]
        
        for compliance in compliance_types:
            if compliance in response_lower:
                requirements.append(compliance.title())
        
        return requirements
    
    def _extract_documentation_required(self, response: str) -> List[str]:
        """Extract documentation requirements from response"""
        
        documentation = []
        response_lower = response.lower()
        
        # Common documentation types
        doc_types = [
            "temperature logs", "cleaning checklists", "inventory reports",
            "incident reports", "training records", "audit reports"
        ]
        
        for doc in doc_types:
            if doc in response_lower:
                documentation.append(doc.title())
        
        return documentation
    
    def _calculate_operations_confidence(self, response: str, context: OperationsContext) -> float:
        """Calculate confidence score for operations response"""
        
        confidence = 0.8  # Base confidence
        
        # Increase confidence for specific operation matches
        if context.operation_type.value in response.lower():
            confidence += 0.05
        
        # Increase confidence for structured responses
        if any(marker in response for marker in ["1.", "2.", "3.", "•", "-"]):
            confidence += 0.03
        
        # Increase confidence for procedural keywords
        procedural_keywords = ["procedure", "step", "process", "checklist"]
        for keyword in procedural_keywords:
            if keyword in response.lower():
                confidence += 0.01
        
        # Increase confidence for timing information
        if any(time_word in response.lower() for time_word in ["minutes", "hours", "time"]):
            confidence += 0.02
        
        return min(1.0, confidence)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get operations agent performance metrics"""
        
        avg_response_time = self.total_response_time / self.query_count if self.query_count > 0 else 0
        
        return {
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "version": self.version,
            "query_count": self.query_count,
            "procedure_requests": self.procedure_requests,
            "training_requests": self.training_requests,
            "compliance_checks": self.compliance_checks,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.query_count if self.query_count > 0 else 0,
            "average_response_time": avg_response_time,
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "model": str(self.agent.model)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the operations agent"""
        
        try:
            # Test basic functionality
            test_context = OperationsContext(
                operation_type=OperationType.OPENING,
                complexity=OperationComplexity.STANDARD,
                priority=OperationPriority.NORMAL,
                shift_time="morning",
                staff_count=3
            )
            
            test_result = await self.get_operations_guidance("Test operations query", test_context)
            
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

# Global operations agent instance
operations_agent = OperationsSpecialistAgent()

# Factory function
def create_operations_agent(model: str = None) -> OperationsSpecialistAgent:
    """Factory function to create operations agents"""
    return OperationsSpecialistAgent(model=model)

# Async factory function
async def create_operations_agent_async(model: str = None) -> OperationsSpecialistAgent:
    """Async factory function to create operations agents"""
    agent = OperationsSpecialistAgent(model=model)
    
    # Perform health check
    health_status = await agent.health_check()
    
    if health_status["status"] != "healthy":
        raise Exception(f"Operations agent health check failed: {health_status.get('error', 'Unknown error')}")
    
    return agent

if __name__ == "__main__":
    # Test the operations agent
    async def test_operations_agent():
        agent = await create_operations_agent_async()
        
        # Test opening procedures
        context = OperationsContext(
            operation_type=OperationType.OPENING,
            complexity=OperationComplexity.STANDARD,
            priority=OperationPriority.NORMAL,
            shift_time="morning",
            staff_count=3,
            customer_volume="normal",
            location_type="standard"
        )
        
        response = await agent.get_operations_guidance(
            "What are the opening procedures for a morning shift with 3 staff members?",
            context
        )
        
        print("Operations Guidance Response:")
        print(f"Response: {response.response}")
        print(f"Operation Type: {response.operation_type.value}")
        print(f"Complexity: {response.complexity.value}")
        print(f"Priority: {response.priority.value}")
        print(f"Procedure Steps: {response.procedure_steps}")
        print(f"Timing Requirements: {response.timing_requirements}")
        print(f"Staff Required: {response.staff_required}")
        print(f"Completion Time: {response.completion_time}")
        print(f"Quality Checkpoints: {response.quality_checkpoints}")
        print()
        
        # Test procedure checklist
        checklist = await agent.get_procedure_checklist(OperationType.OPENING)
        print("Procedure Checklist:")
        print(checklist)
        print()
        
        # Performance metrics
        print("Performance Metrics:")
        print(agent.get_performance_metrics())
    
    asyncio.run(test_operations_agent())