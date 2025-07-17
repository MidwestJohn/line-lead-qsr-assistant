#!/usr/bin/env python3
"""
Frontend Integration Helpers
============================

Helper functions and endpoints to integrate enhanced multi-format upload
with existing frontend components. Provides backward compatibility while
adding new capabilities.

Features:
- Backward compatible API responses
- Enhanced file upload information
- Real-time progress integration
- Multi-format support information
- Frontend-friendly error messages

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import enhanced services
from services.enhanced_file_validation import enhanced_validation_service
from services.enhanced_qsr_ragie_service import enhanced_qsr_ragie_service

# Import existing patterns
from main import load_documents_db, simple_progress_store

logger = logging.getLogger(__name__)

# Response models for frontend compatibility
class FileTypeInfo(BaseModel):
    """File type information for frontend"""
    extension: str
    category: str
    max_size: int
    max_size_formatted: str
    supported: bool
    description: str

class UploadCapabilities(BaseModel):
    """Upload capabilities information"""
    total_supported_formats: int
    categories: Dict[str, List[str]]
    size_limits: Dict[str, int]
    enhanced_processing: bool
    ragie_integration: bool
    real_time_progress: bool
    background_processing: bool

class ProcessingSummary(BaseModel):
    """Processing summary for dashboard"""
    total_documents: int
    active_processes: int
    completed_today: int
    failed_today: int
    processing_types: Dict[str, int]
    average_processing_time: float
    success_rate: float

class DocumentSummaryEnhanced(BaseModel):
    """Enhanced document summary with multi-format support"""
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    file_size_formatted: str
    upload_timestamp: str
    processing_status: str
    qsr_category: Optional[str] = None
    ragie_document_id: Optional[str] = None
    url: str
    preview_available: bool
    search_indexed: bool

# Create router for frontend integration
frontend_router = APIRouter(prefix="/api/frontend", tags=["Frontend Integration"])

@frontend_router.get("/upload-capabilities", response_model=UploadCapabilities)
async def get_upload_capabilities():
    """
    Get comprehensive upload capabilities for frontend configuration
    
    Returns detailed information about supported file types, size limits,
    and available features for frontend file upload components.
    """
    
    try:
        # Get supported extensions
        supported_extensions = enhanced_validation_service.get_supported_extensions()
        
        # Categorize extensions
        categories = {
            "documents": [],
            "images": [],
            "audio": [],
            "video": [],
            "text": []
        }
        
        size_limits = {}
        
        # Process each extension
        for ext in supported_extensions:
            test_filename = f"test{ext}"
            max_size = enhanced_validation_service.get_max_file_size(test_filename)
            size_limits[ext] = max_size
            
            # Categorize
            if ext in ['.pdf', '.docx', '.xlsx', '.pptx', '.docm', '.xlsm']:
                categories["documents"].append(ext)
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                categories["images"].append(ext)
            elif ext in ['.mp3', '.wav', '.m4a']:
                categories["audio"].append(ext)
            elif ext in ['.mp4', '.mov', '.avi']:
                categories["video"].append(ext)
            elif ext in ['.txt', '.md', '.csv']:
                categories["text"].append(ext)
        
        # Check service availability
        ragie_available = enhanced_qsr_ragie_service.is_available()
        
        return UploadCapabilities(
            total_supported_formats=len(supported_extensions),
            categories=categories,
            size_limits=size_limits,
            enhanced_processing=True,
            ragie_integration=ragie_available,
            real_time_progress=True,
            background_processing=True
        )
        
    except Exception as e:
        logger.error(f"Get upload capabilities failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@frontend_router.get("/file-type-info")
async def get_file_type_info(extension: str = Query(..., description="File extension (e.g., .pdf)")):
    """
    Get detailed information about a specific file type
    
    Returns comprehensive information about file type capabilities,
    size limits, and processing features for frontend display.
    """
    
    try:
        # Validate extension format
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        # Check if supported
        supported_extensions = enhanced_validation_service.get_supported_extensions()
        is_supported = extension in supported_extensions
        
        if not is_supported:
            return FileTypeInfo(
                extension=extension,
                category="unsupported",
                max_size=0,
                max_size_formatted="0 B",
                supported=False,
                description=f"File type {extension} is not supported"
            )
        
        # Get file type info
        test_filename = f"test{extension}"
        max_size = enhanced_validation_service.get_max_file_size(test_filename)
        max_size_formatted = enhanced_validation_service.format_file_size(max_size)
        
        # Determine category and description
        category_map = {
            '.pdf': ('documents', 'PDF document with text extraction and search'),
            '.docx': ('documents', 'Microsoft Word document with content analysis'),
            '.xlsx': ('documents', 'Microsoft Excel spreadsheet with data extraction'),
            '.pptx': ('documents', 'Microsoft PowerPoint presentation with slide analysis'),
            '.docm': ('documents', 'Microsoft Word macro-enabled document'),
            '.xlsm': ('documents', 'Microsoft Excel macro-enabled spreadsheet'),
            '.jpg': ('images', 'JPEG image with visual content analysis'),
            '.jpeg': ('images', 'JPEG image with visual content analysis'),
            '.png': ('images', 'PNG image with visual content analysis'),
            '.gif': ('images', 'GIF image with animation support'),
            '.webp': ('images', 'WebP image with advanced compression'),
            '.mp4': ('video', 'MP4 video with metadata extraction'),
            '.mov': ('video', 'QuickTime video with metadata extraction'),
            '.avi': ('video', 'AVI video with metadata extraction'),
            '.mp3': ('audio', 'MP3 audio with metadata extraction'),
            '.wav': ('audio', 'WAV audio with metadata extraction'),
            '.m4a': ('audio', 'M4A audio with metadata extraction'),
            '.txt': ('text', 'Plain text file with content analysis'),
            '.md': ('text', 'Markdown document with formatting support'),
            '.csv': ('text', 'CSV data file with structured data extraction')
        }
        
        category, description = category_map.get(extension, ('other', f'{extension} file'))
        
        return FileTypeInfo(
            extension=extension,
            category=category,
            max_size=max_size,
            max_size_formatted=max_size_formatted,
            supported=True,
            description=description
        )
        
    except Exception as e:
        logger.error(f"Get file type info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@frontend_router.get("/processing-summary", response_model=ProcessingSummary)
async def get_processing_summary():
    """
    Get processing summary for frontend dashboard
    
    Returns comprehensive statistics about upload processing,
    success rates, and system performance for dashboard display.
    """
    
    try:
        # Get document statistics
        docs_db = load_documents_db()
        total_documents = len(docs_db)
        
        # Get active processes
        active_processes = len(simple_progress_store)
        
        # Count documents by processing status
        processing_types = {}
        completed_today = 0
        failed_today = 0
        
        today = datetime.now().date()
        
        for doc_info in docs_db.values():
            # Count by file type
            file_type = doc_info.get('file_type', 'unknown')
            processing_types[file_type] = processing_types.get(file_type, 0) + 1
            
            # Count completed/failed today
            upload_time = doc_info.get('upload_timestamp', '')
            if upload_time:
                try:
                    upload_date = datetime.fromisoformat(upload_time.replace('Z', '+00:00')).date()
                    if upload_date == today:
                        processing_status = doc_info.get('processing_status', 'completed')
                        if processing_status == 'completed':
                            completed_today += 1
                        elif processing_status == 'failed':
                            failed_today += 1
                except:
                    pass
        
        # Calculate success rate
        total_today = completed_today + failed_today
        success_rate = (completed_today / total_today * 100) if total_today > 0 else 100.0
        
        # Estimate average processing time (placeholder)
        average_processing_time = 45.0  # seconds
        
        return ProcessingSummary(
            total_documents=total_documents,
            active_processes=active_processes,
            completed_today=completed_today,
            failed_today=failed_today,
            processing_types=processing_types,
            average_processing_time=average_processing_time,
            success_rate=success_rate
        )
        
    except Exception as e:
        logger.error(f"Get processing summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@frontend_router.get("/documents-enhanced")
async def get_documents_enhanced(
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of documents"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get enhanced document list with multi-format support
    
    Returns document list with enhanced metadata including file types,
    processing status, and multi-format specific information.
    """
    
    try:
        # Get documents database
        docs_db = load_documents_db()
        
        # Filter and sort documents
        documents = []
        for doc_id, doc_info in docs_db.items():
            # Apply file type filter
            if file_type and doc_info.get('file_type') != file_type:
                continue
            
            # Format file size
            file_size = doc_info.get('file_size', 0)
            file_size_formatted = enhanced_validation_service.format_file_size(file_size)
            
            # Determine processing status
            processing_status = doc_info.get('processing_status', 'completed')
            if 'ragie_document_id' in doc_info:
                processing_status = 'indexed'
            
            # Check if preview is available
            file_type_value = doc_info.get('file_type', 'unknown')
            preview_available = file_type_value in ['pdf', 'txt', 'md', 'jpg', 'jpeg', 'png']
            
            # Get QSR category
            qsr_category = None
            if 'validation_metadata' in doc_info:
                qsr_category = doc_info['validation_metadata'].get('qsr_category')
            
            document = DocumentSummaryEnhanced(
                id=doc_info['id'],
                filename=doc_info['filename'],
                original_filename=doc_info['original_filename'],
                file_type=file_type_value,
                file_size=file_size,
                file_size_formatted=file_size_formatted,
                upload_timestamp=doc_info['upload_timestamp'],
                processing_status=processing_status,
                qsr_category=qsr_category,
                ragie_document_id=doc_info.get('ragie_document_id'),
                url=f"/files/{doc_info['filename']}",
                preview_available=preview_available,
                search_indexed=bool(doc_info.get('ragie_document_id'))
            )
            
            documents.append(document)
        
        # Sort by upload timestamp (newest first)
        documents.sort(key=lambda x: x.upload_timestamp, reverse=True)
        
        # Apply pagination
        paginated_documents = documents[offset:offset + limit]
        
        return {
            "success": True,
            "documents": paginated_documents,
            "total_count": len(documents),
            "filtered_count": len(documents),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(documents)
        }
        
    except Exception as e:
        logger.error(f"Get enhanced documents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@frontend_router.get("/validation-config")
async def get_validation_config():
    """
    Get validation configuration for frontend file input
    
    Returns configuration data for frontend file upload components
    including validation rules, size limits, and supported formats.
    """
    
    try:
        # Get supported extensions
        supported_extensions = enhanced_validation_service.get_supported_extensions()
        
        # Build validation config
        validation_config = {
            "supported_extensions": supported_extensions,
            "max_file_sizes": {},
            "mime_types": {},
            "validation_rules": {
                "required": True,
                "multiple": False,
                "directory": False
            },
            "error_messages": {
                "invalid_type": "File type not supported. Please select a valid file.",
                "too_large": "File size exceeds maximum limit. Please select a smaller file.",
                "empty_file": "File is empty. Please select a valid file.",
                "invalid_format": "File format is invalid. Please select a valid file."
            }
        }
        
        # Get size limits and MIME types
        for ext in supported_extensions:
            test_filename = f"test{ext}"
            max_size = enhanced_validation_service.get_max_file_size(test_filename)
            validation_config["max_file_sizes"][ext] = max_size
            
            # Get MIME types (simplified)
            mime_map = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.mp4': 'video/mp4',
                '.mov': 'video/quicktime',
                '.avi': 'video/x-msvideo',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.m4a': 'audio/mp4',
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.csv': 'text/csv'
            }
            
            validation_config["mime_types"][ext] = mime_map.get(ext, 'application/octet-stream')
        
        return {
            "success": True,
            "validation_config": validation_config,
            "total_supported_formats": len(supported_extensions),
            "enhanced_validation": True
        }
        
    except Exception as e:
        logger.error(f"Get validation config failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@frontend_router.get("/system-health")
async def get_system_health():
    """
    Get system health information for frontend monitoring
    
    Returns comprehensive system health data including service status,
    resource utilization, and error rates for frontend display.
    """
    
    try:
        # Check service availability
        validation_available = enhanced_validation_service is not None
        ragie_available = enhanced_qsr_ragie_service.is_available()
        
        # Get processing statistics
        active_processes = len(simple_progress_store)
        
        # Count processes by status
        status_counts = {"uploaded": 0, "processing": 0, "completed": 0, "failed": 0}
        for process_data in simple_progress_store.values():
            status = process_data.get("status", "unknown")
            if status in status_counts:
                status_counts[status] += 1
        
        # Calculate health score
        health_score = 100
        if not validation_available:
            health_score -= 40
        if not ragie_available:
            health_score -= 30
        if status_counts["failed"] > 0:
            health_score -= min(20, status_counts["failed"] * 5)
        
        # Determine overall health
        if health_score >= 90:
            health_status = "healthy"
        elif health_score >= 70:
            health_status = "warning"
        elif health_score >= 50:
            health_status = "degraded"
        else:
            health_status = "critical"
        
        return {
            "success": True,
            "health_status": health_status,
            "health_score": health_score,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "validation_service": validation_available,
                "ragie_service": ragie_available,
                "websocket_service": True  # Assume available
            },
            "processing": {
                "active_processes": active_processes,
                "status_counts": status_counts,
                "total_processed": sum(status_counts.values())
            },
            "capabilities": {
                "supported_formats": len(enhanced_validation_service.get_supported_extensions()) if validation_available else 0,
                "multi_format_support": validation_available,
                "real_time_progress": True,
                "background_processing": True
            }
        }
        
    except Exception as e:
        logger.error(f"Get system health failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "health_status": "error",
            "health_score": 0,
            "timestamp": datetime.now().isoformat()
        }

# Helper functions for frontend integration
def format_file_size_for_frontend(size_bytes: int) -> str:
    """Format file size for frontend display"""
    return enhanced_validation_service.format_file_size(size_bytes)

def get_file_type_category(file_type: str) -> str:
    """Get category for file type"""
    category_map = {
        'pdf': 'documents',
        'docx': 'documents',
        'xlsx': 'documents', 
        'pptx': 'documents',
        'docm': 'documents',
        'xlsm': 'documents',
        'jpg': 'images',
        'jpeg': 'images',
        'png': 'images',
        'gif': 'images',
        'webp': 'images',
        'mp4': 'video',
        'mov': 'video',
        'avi': 'video',
        'mp3': 'audio',
        'wav': 'audio',
        'm4a': 'audio',
        'txt': 'text',
        'md': 'text',
        'csv': 'text'
    }
    return category_map.get(file_type, 'other')

def is_preview_available(file_type: str) -> bool:
    """Check if preview is available for file type"""
    preview_types = ['pdf', 'txt', 'md', 'jpg', 'jpeg', 'png', 'gif', 'webp']
    return file_type in preview_types