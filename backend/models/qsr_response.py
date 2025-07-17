#!/usr/bin/env python3
"""
Enhanced QSR Response Models for Cleaned Procedures
==================================================

Structured Pydantic models for cleaned QSR procedures with enhanced
formatting and validation for optimal readability and StepCard integration.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import re
import uuid

class QSRStep(BaseModel):
    """
    Enhanced structured step model for QSR procedures
    
    Designed for optimal display in StepCard components with
    proper task formatting and validation.
    """
    step_number: int = Field(description="Sequential step number")
    title: str = Field(description="Clear, concise step title")
    time_estimate: Optional[str] = Field(None, description="Time estimate for this step (e.g., '5 minutes')")
    tasks: List[str] = Field(description="List of tasks within this step")
    verification: Optional[str] = Field(None, description="How to verify step completion")
    safety_warning: Optional[str] = Field(None, description="Step-specific safety warning")
    media_reference: Optional[str] = Field(None, description="Reference to visual aids")
    equipment_needed: List[str] = Field(default_factory=list, description="Equipment required for this step")
    tools_needed: List[str] = Field(default_factory=list, description="Tools required for this step")
    
    @field_validator('tasks')
    @classmethod
    def clean_task_list(cls, v):
        """Clean and validate task list"""
        if not v:
            return []
        
        cleaned_tasks = []
        for task in v:
            if isinstance(task, str):
                # Remove bullet points from task text
                cleaned_task = re.sub(r'^[•\-\*\u2022\u2023\u25E6]\s*', '', task.strip())
                
                # Ensure proper sentence ending
                if cleaned_task and not cleaned_task.endswith(('.', '!', '?', ':')):
                    cleaned_task += '.'
                
                # Filter out empty or very short tasks
                if len(cleaned_task) > 3:
                    cleaned_tasks.append(cleaned_task)
        
        return cleaned_tasks
    
    @field_validator('title')
    @classmethod
    def clean_title(cls, v):
        """Clean and validate step title"""
        if not v:
            return "Untitled Step"
        
        # Remove step numbering from title if present
        cleaned_title = re.sub(r'^(?:Step\s*\d+:?\s*|Procedure\s*\d+:?\s*)', '', v.strip(), flags=re.IGNORECASE)
        
        # Ensure title is properly capitalized
        if cleaned_title:
            cleaned_title = cleaned_title[0].upper() + cleaned_title[1:] if len(cleaned_title) > 1 else cleaned_title.upper()
        
        return cleaned_title or "Untitled Step"
    
    @field_validator('time_estimate')
    @classmethod
    def standardize_time_format(cls, v):
        """Standardize time format"""
        if not v:
            return None
        
        # Extract numbers and units
        time_match = re.search(r'(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)', v.lower())
        if time_match:
            value = float(time_match.group(1))
            unit = time_match.group(2)
            
            # Normalize unit
            if unit.startswith('min'):
                unit = 'minute' if value == 1 else 'minutes'
            elif unit.startswith('hour') or unit.startswith('hr'):
                unit = 'hour' if value == 1 else 'hours'
            elif unit.startswith('sec'):
                unit = 'second' if value == 1 else 'seconds'
            
            # Format value
            if value == int(value):
                return f"{int(value)} {unit}"
            else:
                return f"{value} {unit}"
        
        return v

class QSRSafetyWarning(BaseModel):
    """Enhanced safety warning model"""
    level: Literal['critical', 'high', 'medium', 'low'] = Field(description="Safety warning severity")
    message: str = Field(description="Safety warning message")
    step_reference: Optional[int] = Field(None, description="Step number this warning relates to")
    keywords: List[str] = Field(default_factory=list, description="Safety keywords found")
    
    @field_validator('message')
    @classmethod
    def clean_safety_message(cls, v):
        """Clean safety message text"""
        if not v:
            return "Safety warning"
        
        # Remove common prefixes
        cleaned = re.sub(r'^(?:Warning:?\s*|Caution:?\s*|Safety:?\s*)', '', v.strip(), flags=re.IGNORECASE)
        
        # Ensure proper capitalization
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
        
        return cleaned or v

class QSRVerificationPoint(BaseModel):
    """Enhanced verification checkpoint model"""
    step_reference: Optional[int] = Field(None, description="Step number this verification relates to")
    checkpoint: str = Field(description="What to verify")
    expected_result: Optional[str] = Field(None, description="Expected result of verification")
    
    @field_validator('checkpoint')
    @classmethod
    def clean_checkpoint(cls, v):
        """Clean verification checkpoint text"""
        # Remove common prefixes
        cleaned = re.sub(r'^(?:Verify:?\s*|Check:?\s*|Ensure:?\s*|Confirm:?\s*)', '', v.strip(), flags=re.IGNORECASE)
        
        # Ensure proper formatting
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        return cleaned or v

class QSRMediaReference(BaseModel):
    """Enhanced media reference model"""
    media_type: Literal['image', 'video', 'diagram', 'illustration', 'chart'] = Field(description="Type of media")
    reference_id: str = Field(description="Media reference identifier")
    description: Optional[str] = Field(None, description="Description of media content")
    step_reference: Optional[int] = Field(None, description="Step number this media relates to")
    url: Optional[str] = Field(None, description="URL to media content")

class CleanedQSRResponse(BaseModel):
    """
    Comprehensive cleaned QSR response model
    
    Structured response with enhanced formatting for optimal
    readability and StepCard component integration.
    """
    title: str = Field(description="Clean procedure title")
    steps: List[QSRStep] = Field(description="Structured step list")
    overall_time: str = Field(description="Total time estimate")
    safety_notes: List[QSRSafetyWarning] = Field(default_factory=list, description="Extracted safety information")
    verification_points: List[QSRVerificationPoint] = Field(default_factory=list, description="Quality checkpoints")
    media_references: List[QSRMediaReference] = Field(default_factory=list, description="Visual aids and media")
    
    # Enhanced metadata
    procedure_type: Literal['cleaning', 'maintenance', 'troubleshooting', 'setup', 'safety', 'training'] = Field(description="Type of procedure")
    difficulty_level: Literal['beginner', 'intermediate', 'advanced'] = Field(default='intermediate', description="Skill level required")
    frequency: Optional[str] = Field(None, description="How often to perform this procedure")
    prerequisites: List[str] = Field(default_factory=list, description="Requirements before starting")
    
    # Processing metadata
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique response identifier")
    processed_at: datetime = Field(default_factory=datetime.now, description="When response was processed")
    confidence_score: float = Field(default=0.8, description="Confidence in response quality", ge=0.0, le=1.0)
    source_documents: List[str] = Field(default_factory=list, description="Source documents used")
    
    @field_validator('title')
    @classmethod
    def clean_title(cls, v):
        """Clean and validate procedure title"""
        if not v:
            return "QSR Procedure"
        
        # Remove common prefixes and clean up
        cleaned = re.sub(r'^(?:Procedure:?\s*|Process:?\s*|How to:?\s*)', '', v.strip(), flags=re.IGNORECASE)
        
        # Ensure proper capitalization
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
        
        return cleaned or v
    
    @field_validator('overall_time')
    @classmethod
    def standardize_overall_time(cls, v):
        """Standardize overall time format"""
        if not v:
            return "Time not specified"
        
        # Try to parse and standardize
        time_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(minutes?|mins?|hours?|hrs?)', v.lower())
        if time_match:
            start_time = float(time_match.group(1))
            end_time = float(time_match.group(2)) if time_match.group(2) else None
            unit = time_match.group(3)
            
            # Normalize unit
            if unit.startswith('min'):
                unit = 'minutes'
            elif unit.startswith('hour') or unit.startswith('hr'):
                unit = 'hours'
            
            # Format time range
            if end_time:
                return f"{int(start_time)}-{int(end_time)} {unit}"
            else:
                return f"{int(start_time)} {unit}"
        
        return v
    
    @model_validator(mode='after')
    def validate_steps_and_references(self):
        """Validate step references in safety warnings and verification points"""
        if not self.steps:
            return self
        
        max_step = max(step.step_number for step in self.steps)
        
        # Validate safety warning step references
        for warning in self.safety_notes:
            if warning.step_reference and warning.step_reference > max_step:
                warning.step_reference = None
        
        # Validate verification point step references
        for verification in self.verification_points:
            if verification.step_reference and verification.step_reference > max_step:
                verification.step_reference = None
        
        # Validate media reference step references
        for media in self.media_references:
            if media.step_reference and media.step_reference > max_step:
                media.step_reference = None
        
        return self
    
    def to_stepcard_format(self) -> Dict[str, Any]:
        """
        Convert to StepCard component format
        
        Returns:
            Dictionary formatted for StepCard component consumption
        """
        return {
            'id': self.response_id,
            'title': self.title,
            'overall_time': self.overall_time,
            'difficulty': self.difficulty_level,
            'steps': [
                {
                    'id': f"step_{step.step_number}",
                    'number': step.step_number,
                    'title': step.title,
                    'time_estimate': step.time_estimate,
                    'tasks': step.tasks,
                    'verification': step.verification,
                    'safety_warning': step.safety_warning,
                    'media_reference': step.media_reference,
                    'equipment_needed': step.equipment_needed,
                    'tools_needed': step.tools_needed
                }
                for step in self.steps
            ],
            'safety_notes': [
                {
                    'level': warning.level,
                    'message': warning.message,
                    'step_reference': warning.step_reference,
                    'keywords': warning.keywords
                }
                for warning in self.safety_notes
            ],
            'verification_points': [
                {
                    'step_reference': vp.step_reference,
                    'checkpoint': vp.checkpoint,
                    'expected_result': vp.expected_result
                }
                for vp in self.verification_points
            ],
            'media_references': [
                {
                    'type': media.media_type,
                    'reference_id': media.reference_id,
                    'description': media.description,
                    'step_reference': media.step_reference,
                    'url': media.url
                }
                for media in self.media_references
            ],
            'metadata': {
                'procedure_type': self.procedure_type,
                'frequency': self.frequency,
                'prerequisites': self.prerequisites,
                'confidence_score': self.confidence_score,
                'processed_at': self.processed_at.isoformat(),
                'source_documents': self.source_documents
            }
        }
    
    def to_voice_format(self) -> Dict[str, Any]:
        """
        Convert to voice/TTS friendly format
        
        Returns:
            Dictionary formatted for voice interaction
        """
        voice_steps = []
        for step in self.steps:
            voice_step = {
                'number': step.step_number,
                'title': step.title,
                'time_estimate': step.time_estimate,
                'instructions': '. '.join(step.tasks),
                'verification': step.verification,
                'safety_note': step.safety_warning
            }
            voice_steps.append(voice_step)
        
        return {
            'title': self.title,
            'total_time': self.overall_time,
            'total_steps': len(self.steps),
            'steps': voice_steps,
            'important_safety_notes': [warning.message for warning in self.safety_notes if warning.level in ['critical', 'high']],
            'voice_navigation_hints': [
                "Say 'next step' to continue",
                "Say 'repeat step' to hear again",
                "Say 'safety warnings' to hear important safety information"
            ]
        }

# Backward compatibility with existing QSRTaskResponse
class EnhancedQSRTaskResponse(CleanedQSRResponse):
    """
    Enhanced QSR task response that extends CleanedQSRResponse
    while maintaining backward compatibility with existing PydanticAI tools
    """
    
    # Additional fields for backward compatibility
    task_title: Optional[str] = Field(None, description="Alias for title")
    estimated_time: Optional[str] = Field(None, description="Alias for overall_time")
    confidence_level: Optional[float] = Field(None, description="Alias for confidence_score")
    equipment_needed: List[str] = Field(default_factory=list, description="Overall equipment needed")
    tools_needed: List[str] = Field(default_factory=list, description="Overall tools needed")
    
    def __init__(self, **data):
        # Handle backward compatibility
        if 'estimated_time' in data and 'overall_time' not in data:
            data['overall_time'] = data['estimated_time']
        
        super().__init__(**data)
        
        # Sync backward compatibility fields
        self.task_title = self.title
        self.estimated_time = self.overall_time
        self.confidence_level = self.confidence_score
        
        # Aggregate equipment and tools from steps
        all_equipment = set()
        all_tools = set()
        
        for step in self.steps:
            all_equipment.update(step.equipment_needed)
            all_tools.update(step.tools_needed)
        
        self.equipment_needed = list(all_equipment)
        self.tools_needed = list(all_tools)