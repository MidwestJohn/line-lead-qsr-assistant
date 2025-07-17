#!/usr/bin/env python3
"""
Ragie Integration Models
=======================

Pydantic models for Ragie response parsing and QSR-specific data structures.
Provides type safety and validation for multi-modal content handling.

Author: Generated with Memex (https://memex.tech)
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    """Content type enumeration for multi-modal content"""
    TEXT = "text"
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    PDF = "pdf"
    UNKNOWN = "unknown"

class SafetyLevel(str, Enum):
    """Safety level classification for QSR procedures"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DifficultyLevel(str, Enum):
    """Difficulty level for procedures"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class RagieChunk(BaseModel):
    """Ragie chunk data model with all optional fields"""
    text: str = Field(..., description="Main text content of the chunk")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score from Ragie")
    id: str = Field(..., description="Unique chunk identifier")
    index: int = Field(..., ge=0, description="Chunk index within document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    document_id: str = Field(..., description="Source document identifier")
    document_name: str = Field(..., description="Human-readable document name")
    document_metadata: Dict[str, Any] = Field(default_factory=dict, description="Document-level metadata")
    
    # Optional multi-modal fields
    media_url: Optional[str] = Field(None, description="URL to associated media content")
    start_time: Optional[float] = Field(None, ge=0.0, description="Start time for video/audio content")
    end_time: Optional[float] = Field(None, ge=0.0, description="End time for video/audio content")
    file_type: Optional[str] = Field(None, description="Source file type")
    tags: Optional[List[str]] = Field(default_factory=list, description="Content tags")
    
    # QSR-specific enhancements
    equipment_mentioned: Optional[List[str]] = Field(default_factory=list, description="Equipment mentioned in chunk")
    contains_steps: Optional[bool] = Field(False, description="Whether chunk contains step-by-step instructions")
    safety_warning: Optional[bool] = Field(False, description="Whether chunk contains safety warnings")
    adjusted_score: Optional[float] = Field(None, description="QSR-adjusted relevance score")
    
    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Validate that end_time is after start_time"""
        if v is not None and 'start_time' in values and values['start_time'] is not None:
            if v <= values['start_time']:
                raise ValueError('end_time must be greater than start_time')
        return v

class MediaContent(BaseModel):
    """Multi-modal media content model"""
    media_url: str = Field(..., description="URL to media content")
    content_type: ContentType = Field(..., description="Type of media content")
    start_time: Optional[float] = Field(None, ge=0.0, description="Start timestamp for video/audio")
    end_time: Optional[float] = Field(None, ge=0.0, description="End timestamp for video/audio")
    caption: Optional[str] = Field(None, description="Caption or description for media")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    duration: Optional[float] = Field(None, ge=0.0, description="Total duration in seconds")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Validate end_time is after start_time"""
        if v is not None and 'start_time' in values and values['start_time'] is not None:
            if v <= values['start_time']:
                raise ValueError('end_time must be greater than start_time')
        return v

class QSRStep(BaseModel):
    """QSR procedure step model"""
    step: int = Field(..., ge=1, description="Step number")
    instruction: str = Field(..., min_length=1, description="Step instruction text")
    estimated_time: Optional[str] = Field(None, description="Estimated time for this step")
    equipment_needed: Optional[List[str]] = Field(default_factory=list, description="Equipment required for step")
    safety_warning: Optional[str] = Field(None, description="Safety warning for this step")
    media_reference: Optional[str] = Field(None, description="Reference to associated media")
    
class QSRProcedure(BaseModel):
    """Complete QSR procedure model"""
    has_steps: bool = Field(..., description="Whether procedure contains steps")
    procedure_title: Optional[str] = Field(None, description="Title of the procedure")
    total_steps: int = Field(..., ge=0, description="Total number of steps")
    estimated_total_time: Optional[str] = Field(None, description="Total estimated time")
    steps: List[QSRStep] = Field(default_factory=list, description="List of procedure steps")
    equipment_involved: List[str] = Field(default_factory=list, description="All equipment involved")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Difficulty assessment")
    safety_level: Optional[SafetyLevel] = Field(None, description="Safety level assessment")
    required_tools: Optional[List[str]] = Field(default_factory=list, description="Required tools")

class VisualCitation(BaseModel):
    """Visual citation model for source attribution"""
    citation_id: str = Field(..., description="Unique citation identifier")
    source: str = Field(..., description="Source document name")
    page: Union[int, str] = Field(..., description="Page number or reference")
    manual: str = Field(..., description="Manual name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    chunk_index: Optional[int] = Field(None, description="Chunk index in source")
    media_url: Optional[str] = Field(None, description="Associated media URL")
    content_type: Optional[str] = Field(None, description="Content type")

class ManualReference(BaseModel):
    """Manual reference model"""
    manual_name: str = Field(..., description="Name of the manual")
    page_reference: str = Field(..., description="Page reference information")
    document_type: Optional[str] = Field(None, description="Type of document")
    equipment_type: Optional[str] = Field(None, description="Equipment type if applicable")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    chunk_count: int = Field(..., ge=1, description="Number of chunks from this manual")

class DocumentContext(BaseModel):
    """Document context information"""
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary information")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    coverage: str = Field(..., description="Coverage assessment (comprehensive/partial)")
    media_available: bool = Field(False, description="Whether media content is available")
    total_sources: Optional[int] = Field(None, description="Total number of source documents")

class ContentAnalysis(BaseModel):
    """Content analysis for multi-modal responses"""
    has_video: bool = Field(False, description="Whether response contains video content")
    has_images: bool = Field(False, description="Whether response contains images")
    has_audio: bool = Field(False, description="Whether response contains audio")
    has_steps: bool = Field(False, description="Whether response contains step-by-step procedures")
    media_content: List[MediaContent] = Field(default_factory=list, description="List of media content")
    content_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of content types")

class QSRTaskResponse(BaseModel):
    """Structured QSR task response model"""
    steps: List[QSRStep] = Field(default_factory=list, description="Task steps")
    safety_warnings: List[str] = Field(default_factory=list, description="Safety warnings")
    equipment_needed: List[str] = Field(default_factory=list, description="Required equipment")
    media_references: List[MediaContent] = Field(default_factory=list, description="Media content")
    source_documents: List[str] = Field(default_factory=list, description="Source document names")
    estimated_time: Optional[str] = Field(None, description="Total estimated time")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Task difficulty")
    safety_level: Optional[SafetyLevel] = Field(None, description="Safety level")

class RagieSearchRequest(BaseModel):
    """Ragie search request model"""
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(8, ge=1, le=20, description="Maximum number of results")
    equipment_type: Optional[str] = Field(None, description="Equipment type filter")
    procedure_type: Optional[str] = Field(None, description="Procedure type filter")
    safety_level: Optional[SafetyLevel] = Field(None, description="Safety level filter")
    rerank: bool = Field(True, description="Enable semantic reranking")
    max_chunks_per_document: int = Field(3, ge=1, le=10, description="Max chunks per document")

class RagieSearchResponse(BaseModel):
    """Ragie search response model"""
    chunks: List[RagieChunk] = Field(default_factory=list, description="Retrieved chunks")
    total_results: int = Field(..., ge=0, description="Total number of results")
    search_time_ms: float = Field(..., ge=0.0, description="Search time in milliseconds")
    detected_equipment: Optional[str] = Field(None, description="Auto-detected equipment type")
    detected_procedure: Optional[str] = Field(None, description="Auto-detected procedure type")
    safety_level: Optional[SafetyLevel] = Field(None, description="Detected safety level")

class RagieUploadRequest(BaseModel):
    """Ragie document upload request model"""
    filename: str = Field(..., min_length=1, description="Original filename")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    mode: str = Field("hi_res", description="Processing mode (hi_res/fast)")
    partition: Optional[str] = Field(None, description="Document partition")

class RagieUploadResponse(BaseModel):
    """Ragie document upload response model"""
    success: bool = Field(..., description="Whether upload was successful")
    document_id: Optional[str] = Field(None, description="Ragie document ID")
    filename: str = Field(..., description="Uploaded filename")
    chunk_count: Optional[int] = Field(None, description="Number of chunks created")
    page_count: Optional[int] = Field(None, description="Number of pages processed")
    ragie_metadata: Dict[str, Any] = Field(default_factory=dict, description="Enhanced metadata")
    error: Optional[str] = Field(None, description="Error message if upload failed")

class EnhancedChatResponse(BaseModel):
    """Enhanced chat response with Ragie integration"""
    response: str = Field(..., description="Main response text")
    timestamp: str = Field(..., description="Response timestamp")
    parsed_steps: Optional[QSRProcedure] = Field(None, description="Parsed procedure steps")
    visual_citations: Optional[List[VisualCitation]] = Field(None, description="Visual citations")
    manual_references: Optional[List[ManualReference]] = Field(None, description="Manual references")
    document_context: Optional[DocumentContext] = Field(None, description="Document context")
    hierarchical_path: Optional[List[str]] = Field(None, description="Hierarchical navigation path")
    contextual_recommendations: Optional[List[str]] = Field(None, description="Contextual recommendations")
    retrieval_method: str = Field("ragie_integration", description="Retrieval method used")
    content_analysis: Optional[ContentAnalysis] = Field(None, description="Multi-modal content analysis")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall response quality score")

class QSRMetadata(BaseModel):
    """QSR-specific metadata model"""
    equipment_type: Optional[str] = Field(None, description="Type of equipment")
    procedure_type: Optional[str] = Field(None, description="Type of procedure")
    qsr_document_type: Optional[str] = Field(None, description="Type of document (avoiding reserved 'document_type')")
    safety_level: Optional[SafetyLevel] = Field(None, description="Safety classification")
    target_role: Optional[str] = Field(None, description="Target role (manager, crew, etc.)")
    industry: str = Field("qsr", description="Industry classification")
    language: str = Field("en", description="Document language")
    upload_timestamp: Optional[str] = Field(None, description="Upload timestamp")
    system_source: str = Field("line_lead_assistant", description="System that uploaded document")
    display_name: Optional[str] = Field(None, description="Human-readable display name")
    
    @validator('safety_level', pre=True)
    def validate_safety_level(cls, v):
        """Validate safety level values"""
        if v is not None and isinstance(v, str):
            try:
                return SafetyLevel(v.lower())
            except ValueError:
                return None
        return v

# Response format compatibility models (maintain existing API contract)
class LegacyChatResponse(BaseModel):
    """Legacy chat response format for backward compatibility"""
    response: str
    timestamp: str
    parsed_steps: Optional[Dict] = None
    visual_citations: Optional[List[Dict]] = None
    manual_references: Optional[List[Dict]] = None
    document_context: Optional[Dict] = None
    hierarchical_path: Optional[List[str]] = None
    contextual_recommendations: Optional[List[str]] = None
    retrieval_method: Optional[str] = "ragie_integration"
    
    class Config:
        """Include null fields in JSON output for frontend compatibility"""
        exclude_none = False