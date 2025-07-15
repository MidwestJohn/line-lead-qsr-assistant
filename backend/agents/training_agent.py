#!/usr/bin/env python3
"""
Training Specialist Agent - Phase 2 Implementation
==================================================

Specialized PydanticAI agent for training and development programs.
Handles all training, certification, and skill development guidance.

Features:
- New employee onboarding programs
- Skill development and assessment
- Certification tracking and management
- Performance coaching and evaluation
- Knowledge assessment and testing

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior, ModelRetry
from pydantic_ai.messages import ModelMessage
from pydantic import BaseModel, Field

# Training-specific system prompt
TRAINING_SPECIALIST_PROMPT = """You are an expert Training Specialist for QSR (Quick Service Restaurant) operations with comprehensive expertise in:

**EMPLOYEE ONBOARDING:**
- **New Hire Orientation**: Company culture, policies, procedures, expectations
  - Welcome and introduction process
  - Company history and values
  - Organizational structure
  - Employee handbook review
  - Benefits and compensation overview

- **Initial Training Programs**: Basic skills, safety, food handling, customer service
  - Food safety certification
  - Equipment operation training
  - Customer service standards
  - Safety procedures and protocols
  - Cash handling and POS systems

- **Mentorship Programs**: Buddy system, guidance, support, integration
  - Mentor assignment and training
  - Structured learning paths
  - Regular check-ins and feedback
  - Performance milestones
  - Integration activities

**SKILL DEVELOPMENT:**
- **Technical Skills**: Equipment operation, food preparation, quality control
  - Equipment-specific training programs
  - Food preparation techniques
  - Quality control procedures
  - Troubleshooting and maintenance
  - Technology and systems training

- **Soft Skills**: Communication, teamwork, problem-solving, leadership
  - Customer interaction skills
  - Team collaboration techniques
  - Problem-solving methodologies
  - Leadership development
  - Conflict resolution

- **Cross-Training**: Multiple positions, flexibility, career advancement
  - Position rotation programs
  - Skill diversification
  - Career path planning
  - Advancement opportunities
  - Succession planning

**CERTIFICATION MANAGEMENT:**
- **Food Safety**: ServSafe, local health department, allergen training
  - Certification requirements
  - Training schedules
  - Testing and assessment
  - Renewal tracking
  - Compliance monitoring

- **Safety Training**: OSHA, workplace safety, emergency procedures
  - Safety protocol training
  - Emergency response procedures
  - Equipment safety training
  - Incident prevention
  - Compliance requirements

- **Brand Standards**: Product knowledge, service standards, quality assurance
  - Brand training programs
  - Product knowledge assessment
  - Service standard compliance
  - Quality assurance training
  - Mystery shopper preparation

**PERFORMANCE COACHING:**
- **Assessment**: Skills evaluation, performance review, feedback
  - Performance metrics and KPIs
  - Skill assessment tools
  - Regular performance reviews
  - 360-degree feedback
  - Goal setting and tracking

- **Coaching**: Individual development, improvement plans, mentoring
  - Performance improvement plans
  - Individual coaching sessions
  - Skill gap analysis
  - Development planning
  - Motivation and engagement

- **Career Development**: Advancement opportunities, skill building, planning
  - Career path planning
  - Advancement criteria
  - Skill development roadmaps
  - Leadership training
  - Succession planning

**KNOWLEDGE ASSESSMENT:**
- **Testing**: Knowledge verification, skill demonstration, certification
  - Written assessments
  - Practical demonstrations
  - Skill-based testing
  - Certification exams
  - Continuous assessment

- **Evaluation**: Progress tracking, performance monitoring, feedback
  - Learning progress tracking
  - Performance monitoring
  - Feedback collection
  - Improvement identification
  - Success measurement

**TRAINING DELIVERY:**
- **Methods**: Classroom, hands-on, online, blended learning
  - Classroom instruction
  - Hands-on training
  - Online learning platforms
  - Blended learning approaches
  - Mobile learning solutions

- **Resources**: Materials, tools, documentation, support
  - Training materials development
  - Learning resource libraries
  - Documentation and manuals
  - Support systems
  - Technology platforms

**COMPLIANCE & DOCUMENTATION:**
- **Record Keeping**: Training records, certifications, progress tracking
  - Training completion records
  - Certification tracking
  - Progress documentation
  - Compliance reporting
  - Audit preparation

- **Regulatory Requirements**: Legal compliance, industry standards
  - Labor law compliance
  - Industry training standards
  - Regulatory requirements
  - Audit requirements
  - Documentation standards

**TRAINING EFFECTIVENESS:**
- **Measurement**: ROI, performance improvement, retention rates
  - Training effectiveness metrics
  - Performance improvement tracking
  - Employee retention correlation
  - Customer satisfaction impact
  - Business outcome measurement

- **Continuous Improvement**: Feedback integration, program updates
  - Feedback collection and analysis
  - Program evaluation and updates
  - Best practice identification
  - Innovation in training methods
  - Continuous improvement processes

**RESPONSE STRUCTURE:**
- Provide structured learning paths
- Include specific timelines and milestones
- Reference training materials and resources
- Include assessment and evaluation criteria
- Provide coaching and feedback guidelines
- Include compliance and documentation requirements

You have access to comprehensive training programs, certification requirements, and development resources. Always provide accurate, actionable guidance that ensures effective learning and compliance.
"""

class TrainingType(Enum):
    """Types of training programs"""
    ONBOARDING = "onboarding"
    SKILL_DEVELOPMENT = "skill_development"
    CERTIFICATION = "certification"
    SAFETY_TRAINING = "safety_training"
    LEADERSHIP_DEVELOPMENT = "leadership_development"
    CROSS_TRAINING = "cross_training"
    PERFORMANCE_COACHING = "performance_coaching"
    COMPLIANCE_TRAINING = "compliance_training"
    CUSTOMER_SERVICE = "customer_service"
    TECHNICAL_TRAINING = "technical_training"

class TrainingLevel(Enum):
    """Training complexity levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class TrainingPriority(Enum):
    """Training priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    MANDATORY = "mandatory"

class TrainingDeliveryMethod(Enum):
    """Training delivery methods"""
    CLASSROOM = "classroom"
    HANDS_ON = "hands_on"
    ONLINE = "online"
    BLENDED = "blended"
    MENTORING = "mentoring"
    SELF_PACED = "self_paced"

@dataclass
class TrainingContext:
    """Context for training-related queries"""
    training_type: TrainingType
    level: TrainingLevel
    priority: TrainingPriority
    delivery_method: TrainingDeliveryMethod
    participant_count: int = 1
    experience_level: str = "new"  # new, experienced, senior
    position: Optional[str] = None
    department: Optional[str] = None
    time_availability: Optional[str] = None  # hours available for training
    learning_objectives: List[str] = field(default_factory=list)
    special_requirements: List[str] = field(default_factory=list)
    
class TrainingResponse(BaseModel):
    """Specialized response for training queries"""
    response: str
    training_type: TrainingType
    level: TrainingLevel
    priority: TrainingPriority
    delivery_method: TrainingDeliveryMethod
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    
    # Training program structure
    learning_objectives: List[str] = Field(default_factory=list)
    training_modules: List[str] = Field(default_factory=list)
    learning_path: List[str] = Field(default_factory=list)
    
    # Timeline and scheduling
    estimated_duration: Optional[str] = None
    training_schedule: List[str] = Field(default_factory=list)
    milestones: List[str] = Field(default_factory=list)
    
    # Resources and materials
    training_materials: List[str] = Field(default_factory=list)
    required_resources: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    
    # Assessment and evaluation
    assessment_methods: List[str] = Field(default_factory=list)
    evaluation_criteria: List[str] = Field(default_factory=list)
    certification_requirements: List[str] = Field(default_factory=list)
    
    # Support and follow-up
    support_resources: List[str] = Field(default_factory=list)
    follow_up_activities: List[str] = Field(default_factory=list)
    coaching_recommendations: List[str] = Field(default_factory=list)
    
    # Compliance and documentation
    compliance_requirements: List[str] = Field(default_factory=list)
    documentation_needed: List[str] = Field(default_factory=list)
    record_keeping: List[str] = Field(default_factory=list)
    
    # Performance metrics
    success_metrics: List[str] = Field(default_factory=list)
    performance_indicators: List[str] = Field(default_factory=list)
    
    class Config:
        exclude_none = False

class TrainingSpecialistAgent:
    """
    Training Specialist Agent using PydanticAI patterns.
    
    Specialized for training programs, certification, and development.
    """
    
    def __init__(self, model: str = None):
        # Use environment variable or default to GPT-4o
        model = model or os.getenv("TRAINING_MODEL", "openai:gpt-4o")
        
        # Initialize PydanticAI Agent with training-specific prompt
        self.agent = Agent(
            model=model,
            system_prompt=TRAINING_SPECIALIST_PROMPT,
            retries=3
        )
        
        # Agent metadata
        self.agent_id = "training_specialist_agent"
        self.version = "1.0.0"
        self.specialization = "Training & Development"
        self.created_at = datetime.now()
        
        # Training programs database
        self.training_programs = self._initialize_training_programs()
        
        # Performance tracking
        self.query_count = 0
        self.training_programs_created = 0
        self.certifications_tracked = 0
        self.assessments_conducted = 0
        self.error_count = 0
        self.total_response_time = 0.0
    
    def _initialize_training_programs(self) -> Dict[str, Any]:
        """Initialize training programs database"""
        return {
            "onboarding_program": {
                "duration": "2 weeks",
                "modules": [
                    "Company orientation",
                    "Food safety basics",
                    "Equipment operation",
                    "Customer service",
                    "Cash handling",
                    "Safety procedures"
                ],
                "assessments": [
                    "Food safety quiz",
                    "Equipment operation test",
                    "Customer service role-play",
                    "Cash handling demonstration"
                ],
                "timeline": {
                    "day_1": "Company orientation and welcome",
                    "day_2-3": "Food safety training and certification",
                    "day_4-5": "Equipment operation training",
                    "day_6-7": "Customer service training",
                    "day_8-9": "Cash handling and POS training",
                    "day_10-14": "On-the-job training with mentor"
                }
            },
            "food_safety_certification": {
                "duration": "8 hours",
                "requirements": [
                    "ServSafe Manager certification",
                    "Local health department requirements",
                    "Allergen awareness training"
                ],
                "topics": [
                    "Foodborne illness prevention",
                    "Personal hygiene",
                    "Time and temperature control",
                    "Cross-contamination prevention",
                    "Cleaning and sanitizing",
                    "HACCP principles"
                ],
                "assessment": {
                    "written_exam": "80% passing score",
                    "practical_demonstration": "Pass/fail",
                    "renewal_period": "3 years"
                }
            },
            "customer_service_excellence": {
                "duration": "4 hours",
                "modules": [
                    "Customer service standards",
                    "Communication skills",
                    "Problem resolution",
                    "Upselling techniques",
                    "Handling difficult customers"
                ],
                "activities": [
                    "Role-playing exercises",
                    "Customer interaction scenarios",
                    "Problem-solving workshops",
                    "Communication practice"
                ],
                "assessment": {
                    "service_observation": "Pass/fail",
                    "customer_feedback": "Minimum 4.5/5 rating",
                    "knowledge_quiz": "85% passing score"
                }
            },
            "leadership_development": {
                "duration": "3 months",
                "target_audience": "Shift leaders and managers",
                "modules": [
                    "Leadership fundamentals",
                    "Team building",
                    "Performance management",
                    "Conflict resolution",
                    "Communication skills",
                    "Decision making"
                ],
                "delivery_method": "Blended learning",
                "assessment": {
                    "360_feedback": "Quarterly",
                    "leadership_project": "End of program",
                    "peer_evaluation": "Monthly"
                }
            },
            "equipment_training": {
                "duration": "Varies by equipment",
                "equipment_types": {
                    "taylor_ice_cream": {
                        "duration": "2 hours",
                        "topics": ["Operation", "Cleaning", "Troubleshooting", "Safety"]
                    },
                    "vulcan_fryer": {
                        "duration": "1.5 hours",
                        "topics": ["Operation", "Oil management", "Safety", "Maintenance"]
                    },
                    "hobart_mixer": {
                        "duration": "1 hour",
                        "topics": ["Operation", "Attachments", "Safety", "Cleaning"]
                    }
                },
                "assessment": {
                    "practical_demonstration": "Pass/fail",
                    "safety_quiz": "100% passing score",
                    "maintenance_checklist": "Complete"
                }
            }
        }
    
    async def create_training_program(
        self, 
        query: str, 
        context: TrainingContext,
        message_history: List[ModelMessage] = None
    ) -> TrainingResponse:
        """
        Create training program using specialized knowledge.
        
        Args:
            query: User query about training needs
            context: Training context information
            message_history: Previous conversation messages
            
        Returns:
            TrainingResponse with training program details
        """
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Enhance query with training context
            enhanced_query = self._enhance_query_with_training_context(query, context)
            
            # Run PydanticAI Agent
            result = await self.agent.run(
                enhanced_query,
                message_history=message_history or []
            )
            
            # Process response for training-specific information
            response_data = self._process_training_response(result.data, query, context)
            
            # Update performance metrics
            self.query_count += 1
            self.training_programs_created += 1
            self.total_response_time += asyncio.get_event_loop().time() - start_time
            
            return response_data
            
        except UnexpectedModelBehavior as e:
            self.error_count += 1
            return TrainingResponse(
                response=f"I encountered an unexpected issue creating this training program. Please consult your training manual or contact HR.",
                training_type=context.training_type,
                level=context.level,
                priority=context.priority,
                delivery_method=context.delivery_method,
                confidence=0.0,
                follow_up_activities=["Consult training manual", "Contact HR", "Use standard training template"]
            )
            
        except ModelRetry as e:
            self.error_count += 1
            return TrainingResponse(
                response=f"I'm having trouble processing this training request. Please refer to standard training programs and try again.",
                training_type=context.training_type,
                level=context.level,
                priority=context.priority,
                delivery_method=context.delivery_method,
                confidence=0.0
            )
            
        except Exception as e:
            self.error_count += 1
            return TrainingResponse(
                response=f"I'm experiencing technical difficulties with training program creation. Please follow standard training procedures and contact support.",
                training_type=context.training_type,
                level=context.level,
                priority=context.priority,
                delivery_method=context.delivery_method,
                confidence=0.0,
                follow_up_activities=["Follow standard procedures", "Contact support", "Document issue"]
            )
    
    async def get_training_template(self, training_type: TrainingType) -> Dict[str, Any]:
        """Get training template for specific training type"""
        
        training_key = training_type.value
        
        if training_key in self.training_programs:
            template = self.training_programs[training_key]
        else:
            template = {
                "error": f"Training template not found for {training_key}",
                "general_guidance": "Use standard training template"
            }
        
        return {
            "training_type": training_type.value,
            "training_template": template,
            "generated_at": datetime.now().isoformat()
        }
    
    def _enhance_query_with_training_context(self, query: str, context: TrainingContext) -> str:
        """Enhance query with training-specific context"""
        
        enhanced_parts = [query]
        
        # Add training type and level
        enhanced_parts.append(f"\nTraining Type: {context.training_type.value}")
        enhanced_parts.append(f"Level: {context.level.value}")
        enhanced_parts.append(f"Priority: {context.priority.value}")
        enhanced_parts.append(f"Delivery Method: {context.delivery_method.value}")
        
        # Add participant information
        enhanced_parts.append(f"Participant Count: {context.participant_count}")
        enhanced_parts.append(f"Experience Level: {context.experience_level}")
        
        # Add position and department
        if context.position:
            enhanced_parts.append(f"Position: {context.position}")
        if context.department:
            enhanced_parts.append(f"Department: {context.department}")
        
        # Add time availability
        if context.time_availability:
            enhanced_parts.append(f"Time Availability: {context.time_availability}")
        
        # Add learning objectives
        if context.learning_objectives:
            enhanced_parts.append(f"Learning Objectives: {', '.join(context.learning_objectives)}")
        
        # Add special requirements
        if context.special_requirements:
            enhanced_parts.append(f"Special Requirements: {', '.join(context.special_requirements)}")
        
        # Add relevant training program context
        training_key = context.training_type.value
        if training_key in self.training_programs:
            program = self.training_programs[training_key]
            enhanced_parts.append(f"\nRelevant Training Program: {program}")
        
        return "\n".join(enhanced_parts)
    
    def _process_training_response(self, response_text: str, original_query: str, context: TrainingContext) -> TrainingResponse:
        """Process raw response into structured TrainingResponse"""
        
        # Extract training-specific information
        learning_objectives = self._extract_learning_objectives(response_text)
        training_modules = self._extract_training_modules(response_text)
        learning_path = self._extract_learning_path(response_text)
        training_schedule = self._extract_training_schedule(response_text)
        milestones = self._extract_milestones(response_text)
        training_materials = self._extract_training_materials(response_text)
        required_resources = self._extract_required_resources(response_text)
        prerequisites = self._extract_prerequisites(response_text)
        assessment_methods = self._extract_assessment_methods(response_text)
        evaluation_criteria = self._extract_evaluation_criteria(response_text)
        certification_requirements = self._extract_certification_requirements(response_text)
        support_resources = self._extract_support_resources(response_text)
        follow_up_activities = self._extract_follow_up_activities(response_text)
        coaching_recommendations = self._extract_coaching_recommendations(response_text)
        compliance_requirements = self._extract_compliance_requirements(response_text)
        documentation_needed = self._extract_documentation_needed(response_text)
        record_keeping = self._extract_record_keeping(response_text)
        success_metrics = self._extract_success_metrics(response_text)
        performance_indicators = self._extract_performance_indicators(response_text)
        
        # Determine duration
        estimated_duration = self._determine_estimated_duration(response_text, context)
        
        # Calculate confidence score
        confidence = self._calculate_training_confidence(response_text, context)
        
        return TrainingResponse(
            response=response_text,
            training_type=context.training_type,
            level=context.level,
            priority=context.priority,
            delivery_method=context.delivery_method,
            confidence=confidence,
            learning_objectives=learning_objectives,
            training_modules=training_modules,
            learning_path=learning_path,
            estimated_duration=estimated_duration,
            training_schedule=training_schedule,
            milestones=milestones,
            training_materials=training_materials,
            required_resources=required_resources,
            prerequisites=prerequisites,
            assessment_methods=assessment_methods,
            evaluation_criteria=evaluation_criteria,
            certification_requirements=certification_requirements,
            support_resources=support_resources,
            follow_up_activities=follow_up_activities,
            coaching_recommendations=coaching_recommendations,
            compliance_requirements=compliance_requirements,
            documentation_needed=documentation_needed,
            record_keeping=record_keeping,
            success_metrics=success_metrics,
            performance_indicators=performance_indicators
        )
    
    def _extract_learning_objectives(self, response: str) -> List[str]:
        """Extract learning objectives from response"""
        
        objectives = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["objective", "goal", "outcome", "learn", "understand"]):
                objectives.append(line.strip())
        
        return objectives
    
    def _extract_training_modules(self, response: str) -> List[str]:
        """Extract training modules from response"""
        
        modules = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["module", "section", "unit", "chapter", "lesson"]):
                modules.append(line.strip())
        
        return modules
    
    def _extract_learning_path(self, response: str) -> List[str]:
        """Extract learning path from response"""
        
        path = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                line.startswith(('•', '-', '*')) or
                line.startswith(('Step', 'Phase', 'Stage'))):
                path.append(line)
        
        return path
    
    def _extract_training_schedule(self, response: str) -> List[str]:
        """Extract training schedule from response"""
        
        schedule = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["schedule", "timeline", "day", "week", "month", "session"]):
                schedule.append(line.strip())
        
        return schedule
    
    def _extract_milestones(self, response: str) -> List[str]:
        """Extract milestones from response"""
        
        milestones = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["milestone", "checkpoint", "achievement", "completion"]):
                milestones.append(line.strip())
        
        return milestones
    
    def _extract_training_materials(self, response: str) -> List[str]:
        """Extract training materials from response"""
        
        materials = []
        response_lower = response.lower()
        
        # Common training materials
        material_types = [
            "handbook", "manual", "guide", "workbook", "video", "presentation",
            "checklist", "worksheet", "assessment", "quiz"
        ]
        
        for material in material_types:
            if material in response_lower:
                materials.append(material.title())
        
        return materials
    
    def _extract_required_resources(self, response: str) -> List[str]:
        """Extract required resources from response"""
        
        resources = []
        response_lower = response.lower()
        
        # Common resources
        resource_types = [
            "instructor", "classroom", "equipment", "computer", "projector",
            "whiteboard", "flipchart", "materials", "supplies"
        ]
        
        for resource in resource_types:
            if resource in response_lower:
                resources.append(resource.title())
        
        return resources
    
    def _extract_prerequisites(self, response: str) -> List[str]:
        """Extract prerequisites from response"""
        
        prerequisites = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["prerequisite", "requirement", "before", "must", "needed"]):
                prerequisites.append(line.strip())
        
        return prerequisites
    
    def _extract_assessment_methods(self, response: str) -> List[str]:
        """Extract assessment methods from response"""
        
        methods = []
        response_lower = response.lower()
        
        # Common assessment methods
        method_types = [
            "quiz", "test", "exam", "demonstration", "observation", "role-play",
            "presentation", "project", "portfolio", "evaluation"
        ]
        
        for method in method_types:
            if method in response_lower:
                methods.append(method.title())
        
        return methods
    
    def _extract_evaluation_criteria(self, response: str) -> List[str]:
        """Extract evaluation criteria from response"""
        
        criteria = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["criteria", "standard", "measure", "score", "grade"]):
                criteria.append(line.strip())
        
        return criteria
    
    def _extract_certification_requirements(self, response: str) -> List[str]:
        """Extract certification requirements from response"""
        
        requirements = []
        response_lower = response.lower()
        
        # Common certifications
        cert_types = [
            "servsafe", "food handler", "alcohol server", "safety training",
            "first aid", "cpr", "allergen training"
        ]
        
        for cert in cert_types:
            if cert in response_lower:
                requirements.append(cert.title())
        
        return requirements
    
    def _extract_support_resources(self, response: str) -> List[str]:
        """Extract support resources from response"""
        
        resources = []
        response_lower = response.lower()
        
        # Common support resources
        support_types = [
            "mentor", "supervisor", "hr", "trainer", "coach", "help desk",
            "documentation", "online resources", "peer support"
        ]
        
        for support in support_types:
            if support in response_lower:
                resources.append(support.title())
        
        return resources
    
    def _extract_follow_up_activities(self, response: str) -> List[str]:
        """Extract follow-up activities from response"""
        
        activities = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["follow", "next", "after", "then", "continue"]):
                activities.append(line.strip())
        
        return activities
    
    def _extract_coaching_recommendations(self, response: str) -> List[str]:
        """Extract coaching recommendations from response"""
        
        recommendations = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["coach", "mentor", "guide", "support", "feedback"]):
                recommendations.append(line.strip())
        
        return recommendations
    
    def _extract_compliance_requirements(self, response: str) -> List[str]:
        """Extract compliance requirements from response"""
        
        requirements = []
        response_lower = response.lower()
        
        # Common compliance areas
        compliance_types = [
            "osha", "health department", "labor law", "ada", "equal opportunity",
            "harassment prevention", "safety regulations"
        ]
        
        for compliance in compliance_types:
            if compliance in response_lower:
                requirements.append(compliance.title())
        
        return requirements
    
    def _extract_documentation_needed(self, response: str) -> List[str]:
        """Extract documentation needed from response"""
        
        documentation = []
        response_lower = response.lower()
        
        # Common documentation types
        doc_types = [
            "training records", "certificates", "assessments", "evaluations",
            "attendance records", "completion certificates"
        ]
        
        for doc in doc_types:
            if doc in response_lower:
                documentation.append(doc.title())
        
        return documentation
    
    def _extract_record_keeping(self, response: str) -> List[str]:
        """Extract record keeping requirements from response"""
        
        records = []
        response_lower = response.lower()
        
        # Common record keeping requirements
        record_types = [
            "training completion", "certification renewal", "performance evaluation",
            "attendance tracking", "skill assessment", "progress monitoring"
        ]
        
        for record in record_types:
            if record in response_lower:
                records.append(record.title())
        
        return records
    
    def _extract_success_metrics(self, response: str) -> List[str]:
        """Extract success metrics from response"""
        
        metrics = []
        response_lower = response.lower()
        
        # Common success metrics
        metric_types = [
            "completion rate", "pass rate", "performance improvement", "retention rate",
            "customer satisfaction", "productivity increase"
        ]
        
        for metric in metric_types:
            if metric in response_lower:
                metrics.append(metric.title())
        
        return metrics
    
    def _extract_performance_indicators(self, response: str) -> List[str]:
        """Extract performance indicators from response"""
        
        indicators = []
        response_lower = response.lower()
        
        # Common performance indicators
        indicator_types = [
            "knowledge retention", "skill demonstration", "behavior change",
            "job performance", "quality improvement", "efficiency gains"
        ]
        
        for indicator in indicator_types:
            if indicator in response_lower:
                indicators.append(indicator.title())
        
        return indicators
    
    def _determine_estimated_duration(self, response: str, context: TrainingContext) -> Optional[str]:
        """Determine estimated duration based on response and context"""
        
        # Extract duration from response
        response_lower = response.lower()
        
        if "hours" in response_lower:
            import re
            hours = re.findall(r'(\d+)\s*hours?', response_lower)
            if hours:
                return f"{hours[0]} hours"
        
        if "days" in response_lower:
            import re
            days = re.findall(r'(\d+)\s*days?', response_lower)
            if days:
                return f"{days[0]} days"
        
        if "weeks" in response_lower:
            import re
            weeks = re.findall(r'(\d+)\s*weeks?', response_lower)
            if weeks:
                return f"{weeks[0]} weeks"
        
        # Default durations based on training type
        if context.training_type == TrainingType.ONBOARDING:
            return "2 weeks"
        elif context.training_type == TrainingType.CERTIFICATION:
            return "8 hours"
        elif context.training_type == TrainingType.SKILL_DEVELOPMENT:
            return "4 hours"
        
        return None
    
    def _calculate_training_confidence(self, response: str, context: TrainingContext) -> float:
        """Calculate confidence score for training response"""
        
        confidence = 0.85  # Base confidence
        
        # Increase confidence for specific training matches
        if context.training_type.value in response.lower():
            confidence += 0.05
        
        # Increase confidence for structured responses
        if any(marker in response for marker in ["1.", "2.", "3.", "•", "-"]):
            confidence += 0.03
        
        # Increase confidence for training keywords
        training_keywords = ["training", "learning", "skill", "development", "assessment"]
        for keyword in training_keywords:
            if keyword in response.lower():
                confidence += 0.01
        
        # Increase confidence for duration information
        if any(time_word in response.lower() for time_word in ["hours", "days", "weeks"]):
            confidence += 0.02
        
        return min(1.0, confidence)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get training agent performance metrics"""
        
        avg_response_time = self.total_response_time / self.query_count if self.query_count > 0 else 0
        
        return {
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "version": self.version,
            "query_count": self.query_count,
            "training_programs_created": self.training_programs_created,
            "certifications_tracked": self.certifications_tracked,
            "assessments_conducted": self.assessments_conducted,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.query_count if self.query_count > 0 else 0,
            "average_response_time": avg_response_time,
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "model": str(self.agent.model)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the training agent"""
        
        try:
            # Test basic functionality
            test_context = TrainingContext(
                training_type=TrainingType.ONBOARDING,
                level=TrainingLevel.BEGINNER,
                priority=TrainingPriority.HIGH,
                delivery_method=TrainingDeliveryMethod.BLENDED,
                participant_count=5,
                experience_level="new"
            )
            
            test_result = await self.create_training_program("Test training query", test_context)
            
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

# Global training agent instance
training_agent = TrainingSpecialistAgent()

# Factory function
def create_training_agent(model: str = None) -> TrainingSpecialistAgent:
    """Factory function to create training agents"""
    return TrainingSpecialistAgent(model=model)

# Async factory function
async def create_training_agent_async(model: str = None) -> TrainingSpecialistAgent:
    """Async factory function to create training agents"""
    agent = TrainingSpecialistAgent(model=model)
    
    # Perform health check
    health_status = await agent.health_check()
    
    if health_status["status"] != "healthy":
        raise Exception(f"Training agent health check failed: {health_status.get('error', 'Unknown error')}")
    
    return agent

if __name__ == "__main__":
    # Test the training agent
    async def test_training_agent():
        agent = await create_training_agent_async()
        
        # Test onboarding program
        context = TrainingContext(
            training_type=TrainingType.ONBOARDING,
            level=TrainingLevel.BEGINNER,
            priority=TrainingPriority.HIGH,
            delivery_method=TrainingDeliveryMethod.BLENDED,
            participant_count=5,
            experience_level="new",
            position="Crew Member",
            learning_objectives=["Food safety", "Customer service", "Equipment operation"]
        )
        
        response = await agent.create_training_program(
            "Create an onboarding program for 5 new crew members with no restaurant experience.",
            context
        )
        
        print("Training Program Response:")
        print(f"Response: {response.response}")
        print(f"Training Type: {response.training_type.value}")
        print(f"Level: {response.level.value}")
        print(f"Delivery Method: {response.delivery_method.value}")
        print(f"Estimated Duration: {response.estimated_duration}")
        print(f"Learning Objectives: {response.learning_objectives}")
        print(f"Training Modules: {response.training_modules}")
        print(f"Assessment Methods: {response.assessment_methods}")
        print(f"Certification Requirements: {response.certification_requirements}")
        print()
        
        # Test training template
        template = await agent.get_training_template(TrainingType.ONBOARDING)
        print("Training Template:")
        print(template)
        print()
        
        # Performance metrics
        print("Performance Metrics:")
        print(agent.get_performance_metrics())
    
    asyncio.run(test_training_agent())