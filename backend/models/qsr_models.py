#!/usr/bin/env python3
"""
QSR-Optimized Response Models
============================

Structured Pydantic models for QSR task responses following the comprehensive 
philosophy outlined. These models ensure type-safe, consistent responses
with all critical QSR elements included.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import uuid

class MediaReference(BaseModel):
    """Reference to visual aids and supporting media"""
    type: Literal['image', 'video', 'diagram', 'chart', 'schematic']
    url: str = Field(description="URL or path to media content")
    description: str = Field(description="Description of what the media shows")
    timestamp: Optional[str] = Field(None, description="For video: start/end times (e.g., '2:30-4:15')")
    equipment_relation: Optional[str] = Field(None, description="Which equipment this media relates to")
    safety_critical: bool = Field(False, description="Whether this media shows safety-critical information")

class EquipmentReference(BaseModel):
    """Structured equipment information"""
    name: str = Field(description="Equipment name (e.g., 'Baxter OV520E1')")
    type: str = Field(description="Equipment category (e.g., 'oven', 'fryer', 'grill')")
    manufacturer: Optional[str] = Field(None, description="Equipment manufacturer")
    model_number: Optional[str] = Field(None, description="Specific model identifier")
    location: Optional[str] = Field(None, description="Where equipment is typically located")

class SafetyWarning(BaseModel):
    """Structured safety information"""
    level: Literal['critical', 'high', 'medium', 'low'] = Field(description="Safety warning severity")
    message: str = Field(description="The safety warning text")
    consequences: Optional[str] = Field(None, description="What could happen if ignored")
    required_ppe: List[str] = Field(default_factory=list, description="Required personal protective equipment")

class ProcedureStep(BaseModel):
    """Individual step in a procedure"""
    step_number: int = Field(description="Step sequence number")
    instruction: str = Field(description="What to do in this step")
    duration: Optional[str] = Field(None, description="Estimated time for this step")
    tools_needed: List[str] = Field(default_factory=list, description="Tools/equipment needed for this step")
    safety_notes: List[str] = Field(default_factory=list, description="Step-specific safety considerations")
    verification: Optional[str] = Field(None, description="How to verify step completion")

class QSRTaskResponse(BaseModel):
    """
    Comprehensive QSR task response following the enhanced philosophy
    
    This model ensures all critical QSR elements are captured:
    - Step-by-step procedures
    - Safety warnings with severity levels
    - Equipment requirements
    - Visual aids and media references
    - Source document citations
    - Confidence metrics
    """
    
    # Core procedure information
    task_title: str = Field(description="Clear title of the task/procedure")
    steps: List[ProcedureStep] = Field(description="Detailed step-by-step procedure")
    
    # Safety information
    safety_warnings: List[SafetyWarning] = Field(
        default_factory=list, 
        description="Critical safety information with severity levels"
    )
    
    # Equipment and tools
    equipment_needed: List[EquipmentReference] = Field(
        default_factory=list,
        description="Required equipment with detailed specifications"
    )
    tools_needed: List[str] = Field(
        default_factory=list,
        description="Required tools and supplies"
    )
    
    # Time and scheduling
    estimated_time: str = Field(description="Expected completion time (e.g., '15-20 minutes')")
    best_time_to_perform: Optional[str] = Field(
        None, 
        description="Optimal timing (e.g., 'during slow periods', 'end of shift')"
    )
    
    # Media and visual aids
    media_references: List[MediaReference] = Field(
        default_factory=list,
        description="Visual aids, diagrams, and videos"
    )
    
    # Source and confidence
    source_documents: List[str] = Field(
        default_factory=list,
        description="Citation sources from Ragie retrieval"
    )
    confidence_level: float = Field(
        description="Response confidence 0-1 based on source quality",
        ge=0.0, le=1.0
    )
    
    # QSR-specific metadata
    procedure_type: Literal[
        'cleaning', 'maintenance', 'troubleshooting', 'setup', 
        'safety', 'daily_ops', 'opening', 'closing', 'training'
    ] = Field(description="Type of QSR procedure")
    
    frequency: Optional[str] = Field(
        None,
        description="How often this should be performed (e.g., 'daily', 'weekly', 'as needed')"
    )
    
    prerequisites: List[str] = Field(
        default_factory=list,
        description="What must be completed before starting this task"
    )
    
    followup_tasks: List[str] = Field(
        default_factory=list,
        description="Tasks that should be done after completion"
    )
    
    # Response metadata
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.now)
    ragie_search_time: Optional[float] = Field(None, description="Time spent on Ragie search in seconds")

class QSRSearchResult(BaseModel):
    """Enhanced search result from Ragie with QSR-specific metadata"""
    document_id: str = Field(description="Ragie document identifier")
    chunk_id: str = Field(description="Specific chunk identifier")
    content: str = Field(description="Retrieved content text")
    score: float = Field(description="Relevance score from Ragie")
    
    # QSR-specific metadata extracted from content
    equipment_mentioned: List[str] = Field(default_factory=list)
    procedure_type: Optional[str] = Field(None)
    safety_level: Optional[str] = Field(None)
    contains_steps: bool = Field(False, description="Whether content contains step-by-step instructions")
    contains_images: bool = Field(False, description="Whether content references visual elements")
    
    # Source information
    source_filename: Optional[str] = Field(None, description="Original filename if available")
    page_number: Optional[int] = Field(None, description="Page number in source document")
    
class QSRSearchRequest(BaseModel):
    """Structured request for QSR search operations"""
    query: str = Field(description="User's search query")
    equipment_type: Optional[str] = Field(None, description="Filter by equipment type")
    procedure_type: Optional[str] = Field(None, description="Filter by procedure type")
    safety_level: Optional[str] = Field(None, description="Filter by safety level")
    include_images: bool = Field(False, description="Prioritize results with visual content")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of results to return")

class QSRUploadMetadata(BaseModel):
    """Metadata for files uploaded to Ragie with QSR classification"""
    original_filename: str
    file_type: str = Field(description="File extension (pdf, docx, jpg, etc.)")
    
    # QSR classification
    equipment_types: List[str] = Field(default_factory=list)
    procedure_types: List[str] = Field(default_factory=list) 
    safety_level: Optional[str] = Field(None)
    document_type: Literal['manual', 'sop', 'safety', 'training', 'reference'] = Field('manual')
    
    # Content characteristics
    contains_images: bool = Field(False)
    contains_diagrams: bool = Field(False)
    contains_procedures: bool = Field(False)
    language: str = Field('en', description="Document language")
    
    # Organizational metadata
    department: Optional[str] = Field(None)
    version: Optional[str] = Field(None)
    effective_date: Optional[datetime] = Field(None)
    review_date: Optional[datetime] = Field(None)
    
    # Upload tracking
    uploaded_by: Optional[str] = Field(None)
    upload_timestamp: datetime = Field(default_factory=datetime.now)

# QSR Equipment and Procedure Constants
QSR_EQUIPMENT_TYPES = [
    'fryer', 'grill', 'oven', 'ice_machine', 'pos_system',
    'drive_thru', 'prep_station', 'dishwasher', 'mixer',
    'freezer', 'refrigerator', 'coffee_machine', 'toaster',
    'baxter', 'taylor', 'grote', 'canotto', 'romana'  # Brand-specific
]

QSR_PROCEDURE_TYPES = [
    'cleaning', 'maintenance', 'troubleshooting', 'setup',
    'safety', 'daily_ops', 'opening', 'closing', 'training',
    'inventory', 'quality_control', 'customer_service'
]

QSR_SAFETY_LEVELS = ['critical', 'high', 'medium', 'low']

QSR_DOCUMENT_TYPES = ['manual', 'sop', 'safety', 'training', 'reference']