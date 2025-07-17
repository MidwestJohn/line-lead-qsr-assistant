#!/usr/bin/env python3
"""
Enhanced Multi-Format Upload Endpoints
======================================

FastAPI endpoints for multi-format file upload with enhanced Ragie integration.
Follows existing Line Lead patterns while adding comprehensive file type support.

Following Phase 2 strategy:
- Integrates validation with Ragie processing
- Maintains existing endpoint patterns
- Provides real-time status tracking
- Follows existing error handling

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import our enhanced services
from services.enhanced_qsr_ragie_service import (
    enhanced_qsr_ragie_service,
    MultiFormatUploadResult,
    ProcessingStatus,
    upload_multi_format_file,
    get_processing_status,
    search_multi_format_documents,
    get_supported_file_types,
    is_ragie_service_available
)

# Import existing patterns
from services.enhanced_file_validation import enhanced_validation_service

logger = logging.getLogger(__name__)

# Response models following existing patterns
class MultiFormatUploadResponse(BaseModel):
    """Response for multi-format upload"""
    success: bool
    message: str
    filename: str
    document_id: str
    file_type: str
    file_size: int
    processing_status: str
    ragie_document_id: Optional[str] = None
    
    # Status tracking endpoints
    status_endpoint: str
    progress_endpoint: str
    search_endpoint: str
    
    # Processing metadata
    qsr_category: str
    processing_mode: str
    estimated_completion_time: Optional[str] = None

class ProcessingStatusResponse(BaseModel):
    """Response for processing status"""
    document_id: str
    status: str
    progress_percent: float
    current_operation: str
    error_message: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MultiFormatSearchRequest(BaseModel):
    """Request for multi-format search"""
    query: str
    file_types: Optional[List[str]] = None
    qsr_categories: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)

class MultiFormatSearchResponse(BaseModel):
    """Response for multi-format search"""
    success: bool
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    file_types_found: List[str]
    qsr_categories_found: List[str]
    processing_time_ms: float

class SupportedFormatsResponse(BaseModel):
    """Response for supported formats"""
    total_formats: int
    supported_extensions: List[str]
    qsr_categories: List[str]
    processing_modes: Dict[str, str]
    file_type_mapping: Dict[str, str]
    service_status: Dict[str, Any]

class ServiceStatusResponse(BaseModel):
    """Response for service status"""
    service_available: bool
    validation_service_status: bool
    ragie_service_status: bool
    processing_summary: Dict[str, Any]
    supported_formats: int
    active_processes: int

# Create router
multi_format_router = APIRouter(prefix="/api/multi-format", tags=["Multi-Format Upload"])

@multi_format_router.post("/upload", response_model=MultiFormatUploadResponse)
async def upload_multi_format_file_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    background_processing: bool = Query(True, description="Enable background processing")
):
    """
    Upload multi-format file with comprehensive validation and Ragie integration
    
    Supports 21 file types:
    - Documents: PDF, DOCX, XLSX, PPTX, DOCM, XLSM, TXT, MD, CSV
    - Images: JPG, JPEG, PNG, GIF, WEBP
    - Audio/Video: MP4, MOV, AVI, WAV, MP3, M4A
    
    Features:
    - Comprehensive validation
    - Ragie integration for search
    - Real-time status tracking
    - QSR-specific categorization
    """
    
    try:
        # Check service availability
        if not is_ragie_service_available():
            raise HTTPException(
                status_code=503,
                detail="Ragie service not available. Please check configuration."
            )
        
        # Upload with enhanced processing
        result = await upload_multi_format_file(file, background_processing)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error_message or "Upload failed"
            )
        
        # Estimate completion time
        estimated_time = None
        if background_processing:
            # Rough estimate based on file size and type
            file_size_mb = result.file_size / (1024 * 1024)
            base_time = 30  # Base 30 seconds
            size_multiplier = max(1, file_size_mb / 10)  # +time per 10MB
            estimated_seconds = base_time * size_multiplier
            estimated_time = datetime.now().timestamp() + estimated_seconds
        
        return MultiFormatUploadResponse(
            success=True,
            message=f"File uploaded successfully. Processing {'in background' if background_processing else 'completed'}.",
            filename=result.filename,
            document_id=result.document_id,
            file_type=result.file_type,
            file_size=result.file_size,
            processing_status=result.processing_status,
            ragie_document_id=result.ragie_document_id,
            status_endpoint=f"/api/multi-format/status/{result.document_id}",
            progress_endpoint=f"/api/multi-format/progress/{result.document_id}",
            search_endpoint=f"/api/multi-format/search",
            qsr_category=result.metadata.get("qsr_category", "manual"),
            processing_mode=result.metadata.get("processing_mode", "fast"),
            estimated_completion_time=str(estimated_time) if estimated_time else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-format upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@multi_format_router.get("/status/{document_id}", response_model=ProcessingStatusResponse)
async def get_processing_status_endpoint(document_id: str):
    """
    Get processing status for a document
    
    Returns real-time status including:
    - Processing progress percentage
    - Current operation description
    - Completion status
    - Error information if failed
    """
    
    try:
        status = get_processing_status(document_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        return ProcessingStatusResponse(
            document_id=status.document_id,
            status=status.status,
            progress_percent=status.progress_percent,
            current_operation=status.current_operation,
            error_message=status.error_message,
            completed_at=status.completed_at.isoformat() if status.completed_at else None,
            metadata=status.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )

@multi_format_router.get("/progress/{document_id}")
async def get_processing_progress_endpoint(document_id: str):
    """
    Get simplified progress information for WebSocket/polling
    
    Returns lightweight progress data for real-time updates
    """
    
    try:
        status = get_processing_status(document_id)
        
        if not status:
            return JSONResponse(
                status_code=404,
                content={
                    "error": f"Document {document_id} not found",
                    "progress": 0,
                    "status": "not_found"
                }
            )
        
        return {
            "document_id": document_id,
            "progress": status.progress_percent,
            "status": status.status,
            "operation": status.current_operation,
            "completed": status.status == "completed",
            "failed": status.status == "failed",
            "error": status.error_message
        }
        
    except Exception as e:
        logger.error(f"Progress check error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Progress check failed: {str(e)}",
                "progress": 0,
                "status": "error"
            }
        )

@multi_format_router.post("/search", response_model=MultiFormatSearchResponse)
async def search_multi_format_documents_endpoint(request: MultiFormatSearchRequest):
    """
    Search across multi-format documents with filtering
    
    Features:
    - Full-text search across all supported file types
    - Filter by file types and QSR categories
    - Relevance scoring
    - Metadata extraction
    """
    
    try:
        start_time = datetime.now()
        
        # Validate file types if provided
        if request.file_types:
            supported_types = get_supported_file_types()
            invalid_types = [ft for ft in request.file_types if ft not in supported_types]
            if invalid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file types: {invalid_types}. Supported: {supported_types}"
                )
        
        # Perform search
        result = await search_multi_format_documents(
            query=request.query,
            file_types=request.file_types,
            qsr_categories=request.qsr_categories,
            limit=request.limit
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Search failed")
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Extract metadata from results
        search_results = result.get("results", [])
        file_types_found = list(set([r.get("file_type") for r in search_results if r.get("file_type")]))
        qsr_categories_found = list(set([r.get("qsr_category") for r in search_results if r.get("qsr_category")]))
        
        return MultiFormatSearchResponse(
            success=True,
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            file_types_found=file_types_found,
            qsr_categories_found=qsr_categories_found,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@multi_format_router.get("/supported-formats", response_model=SupportedFormatsResponse)
async def get_supported_formats_endpoint():
    """
    Get comprehensive information about supported file formats
    
    Returns:
    - Supported file extensions
    - QSR categories
    - Processing modes
    - File type mappings
    - Service status
    """
    
    try:
        # Get format information
        supported_extensions = enhanced_validation_service.get_supported_extensions()
        qsr_categories = enhanced_qsr_ragie_service.get_qsr_categories()
        processing_modes = enhanced_qsr_ragie_service.get_processing_modes()
        file_type_mapping = {
            ft.value: cat for ft, cat in enhanced_qsr_ragie_service.QSR_FILE_TYPE_MAPPING.items()
        }
        
        # Get service status
        service_status = enhanced_qsr_ragie_service.create_status_summary()
        
        return SupportedFormatsResponse(
            total_formats=len(supported_extensions),
            supported_extensions=supported_extensions,
            qsr_categories=qsr_categories,
            processing_modes=processing_modes,
            file_type_mapping=file_type_mapping,
            service_status=service_status
        )
        
    except Exception as e:
        logger.error(f"Supported formats error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supported formats: {str(e)}"
        )

@multi_format_router.get("/service-status", response_model=ServiceStatusResponse)
async def get_service_status_endpoint():
    """
    Get comprehensive service status for monitoring
    
    Returns:
    - Service availability
    - Processing summary
    - Active processes
    - Error information
    """
    
    try:
        # Check service availability
        ragie_available = is_ragie_service_available()
        validation_available = enhanced_validation_service is not None
        
        # Get processing summary
        processing_summary = enhanced_qsr_ragie_service.create_status_summary()
        
        return ServiceStatusResponse(
            service_available=ragie_available and validation_available,
            validation_service_status=validation_available,
            ragie_service_status=ragie_available,
            processing_summary=processing_summary,
            supported_formats=len(enhanced_validation_service.get_supported_extensions()),
            active_processes=processing_summary.get("processing", 0)
        )
        
    except Exception as e:
        logger.error(f"Service status error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service status: {str(e)}"
        )

# Health check endpoint
@multi_format_router.get("/health")
async def health_check():
    """Simple health check for multi-format service"""
    try:
        return {
            "status": "healthy",
            "service": "multi-format-upload",
            "validation_service": enhanced_validation_service is not None,
            "ragie_service": is_ragie_service_available(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )

# Error handling middleware
@multi_format_router.exception_handler(Exception)
async def multi_format_exception_handler(request, exc):
    """Global exception handler for multi-format endpoints"""
    logger.error(f"Multi-format endpoint error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Multi-format service error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )