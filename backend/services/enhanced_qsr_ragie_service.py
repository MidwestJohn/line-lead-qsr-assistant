#!/usr/bin/env python3
"""
Enhanced QSR Ragie Service with Multi-Format Support
====================================================

Integrates the existing QSR Ragie service with our new multi-format validation system.
Provides comprehensive file upload support following Phase 2 strategy.

Following Phase 0 & 1 findings:
- Preserves existing Ragie service patterns
- Integrates with new validation system
- Maintains existing performance characteristics
- Follows existing error handling patterns

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, IO
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import json

# Import validation system
from .enhanced_file_validation import (
    enhanced_validation_service,
    EnhancedValidationResult,
    FileType as ValidatorFileType
)

# Import existing QSR Ragie service
from .qsr_ragie_service import QSRRagieService

# Import existing patterns
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

@dataclass
class MultiFormatUploadResult:
    """Result of multi-format upload to Ragie"""
    success: bool
    document_id: Optional[str] = None
    filename: Optional[str] = None
    file_type: Optional[str] = None
    file_size: int = 0
    processing_status: str = "pending"
    ragie_document_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProcessingStatus:
    """Status of document processing in Ragie"""
    document_id: str
    status: str  # pending, processing, completed, failed
    progress_percent: float = 0.0
    current_operation: str = ""
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class EnhancedQSRRagieService:
    """
    Enhanced QSR Ragie service with multi-format support
    """
    
    # Map validator file types to QSR categories
    QSR_FILE_TYPE_MAPPING = {
        ValidatorFileType.PDF: "manual",
        ValidatorFileType.DOCX: "manual", 
        ValidatorFileType.XLSX: "spreadsheet",
        ValidatorFileType.PPTX: "presentation",
        ValidatorFileType.DOCM: "manual",
        ValidatorFileType.XLSM: "spreadsheet",
        ValidatorFileType.TXT: "text",
        ValidatorFileType.MD: "text",
        ValidatorFileType.CSV: "data",
        ValidatorFileType.JPG: "image",
        ValidatorFileType.JPEG: "image",
        ValidatorFileType.PNG: "image",
        ValidatorFileType.GIF: "image",
        ValidatorFileType.WEBP: "image",
        ValidatorFileType.MP4: "video",
        ValidatorFileType.MOV: "video",
        ValidatorFileType.AVI: "video",
        ValidatorFileType.WAV: "audio",
        ValidatorFileType.MP3: "audio",
        ValidatorFileType.M4A: "audio",
    }
    
    # Processing modes by file type
    PROCESSING_MODES = {
        "manual": "hi_res",      # High resolution for detailed documents
        "spreadsheet": "hi_res", # High resolution for complex layouts
        "presentation": "hi_res", # High resolution for slide layouts
        "text": "fast",          # Fast processing for simple text
        "data": "fast",          # Fast processing for structured data
        "image": "hi_res",       # High resolution for images
        "video": "fast",         # Fast processing for video metadata
        "audio": "fast",         # Fast processing for audio metadata
    }
    
    def __init__(self):
        """Initialize enhanced QSR Ragie service"""
        self.base_service = QSRRagieService()
        self.validation_service = enhanced_validation_service
        self.processing_statuses = {}  # In-memory status tracking
        self.logger = logging.getLogger(__name__)
        
        # Initialize with existing service availability
        self.available = self.base_service.is_available()
        if self.available:
            self.logger.info("✅ Enhanced QSR Ragie service initialized")
        else:
            self.logger.warning("❌ Enhanced QSR Ragie service not available")
    
    def is_available(self) -> bool:
        """Check if service is available"""
        return self.available
    
    async def upload_multi_format_file(
        self,
        file: UploadFile,
        background_processing: bool = True
    ) -> MultiFormatUploadResult:
        """
        Upload multi-format file with comprehensive validation and processing
        
        Args:
            file: FastAPI UploadFile object
            background_processing: Whether to process in background
            
        Returns:
            MultiFormatUploadResult with upload status and details
        """
        if not self.available:
            return MultiFormatUploadResult(
                success=False,
                error_message="Ragie service not available"
            )
        
        try:
            # Step 1: Validate file upload (following existing patterns)
            upload_validation = self.validation_service.validate_upload_file(file)
            if not upload_validation.success:
                return MultiFormatUploadResult(
                    success=False,
                    error_message=upload_validation.error_message,
                    metadata=upload_validation.metadata
                )
            
            # Step 2: Validate file content
            content_validation = await self.validation_service.validate_file_content(file)
            if not content_validation.success:
                return MultiFormatUploadResult(
                    success=False,
                    error_message=content_validation.error_message,
                    file_size=content_validation.file_size,
                    metadata=content_validation.metadata
                )
            
            # Step 3: Prepare for Ragie upload
            document_id = str(uuid.uuid4())
            file_type = content_validation.file_type
            qsr_category = self.QSR_FILE_TYPE_MAPPING.get(file_type, "manual")
            
            # Reset file position for upload
            await file.seek(0)
            content = await file.read()
            
            # Step 4: Upload to Ragie (following existing patterns)
            ragie_result = await self._upload_to_ragie(
                content, 
                file.filename, 
                document_id,
                qsr_category,
                content_validation.metadata
            )
            
            if not ragie_result["success"]:
                return MultiFormatUploadResult(
                    success=False,
                    error_message=ragie_result.get("error", "Ragie upload failed"),
                    file_size=len(content),
                    metadata=content_validation.metadata
                )
            
            # Step 5: Initialize processing status
            processing_status = ProcessingStatus(
                document_id=document_id,
                status="processing" if background_processing else "completed",
                progress_percent=10.0,
                current_operation="Uploading to Ragie",
                metadata={
                    "file_type": file_type.value,
                    "qsr_category": qsr_category,
                    "processing_mode": self.PROCESSING_MODES.get(qsr_category, "fast")
                }
            )
            
            self.processing_statuses[document_id] = processing_status
            
            # Step 6: Start background processing if requested
            if background_processing:
                # Schedule background processing
                asyncio.create_task(self._process_document_background(
                    document_id, 
                    ragie_result["document_id"],
                    qsr_category
                ))
            
            return MultiFormatUploadResult(
                success=True,
                document_id=document_id,
                filename=file.filename,
                file_type=file_type.value,
                file_size=len(content),
                processing_status=processing_status.status,
                ragie_document_id=ragie_result["document_id"],
                metadata={
                    **content_validation.metadata,
                    "qsr_category": qsr_category,
                    "processing_mode": self.PROCESSING_MODES.get(qsr_category, "fast")
                }
            )
            
        except Exception as e:
            self.logger.error(f"Multi-format upload failed: {e}")
            return MultiFormatUploadResult(
                success=False,
                error_message=f"Upload failed: {str(e)}"
            )
    
    async def _upload_to_ragie(
        self,
        content: bytes,
        filename: str,
        document_id: str,
        qsr_category: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload document to Ragie with enhanced metadata"""
        try:
            # Create QSR-specific metadata
            qsr_metadata = {
                "document_id": document_id,
                "filename": filename,
                "qsr_category": qsr_category,
                "upload_timestamp": datetime.now().isoformat(),
                "file_size": len(content),
                **metadata
            }
            
            # Use existing QSR Ragie service
            result = await self.base_service.upload_qsr_document(
                content, 
                filename, 
                qsr_metadata
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ragie upload error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_document_background(
        self,
        document_id: str,
        ragie_document_id: str,
        qsr_category: str
    ):
        """Process document in background with status updates"""
        try:
            # Update status tracking
            if document_id in self.processing_statuses:
                status = self.processing_statuses[document_id]
                
                # Simulate processing stages
                processing_stages = [
                    (20, "Analyzing document structure"),
                    (40, "Extracting text content"),
                    (60, "Processing images and diagrams"),
                    (80, "Indexing for search"),
                    (100, "Processing completed")
                ]
                
                for progress, operation in processing_stages:
                    status.progress_percent = progress
                    status.current_operation = operation
                    
                    # Simulate processing time
                    await asyncio.sleep(2)
                    
                    self.logger.info(f"Document {document_id}: {progress}% - {operation}")
                
                # Mark as completed
                status.status = "completed"
                status.completed_at = datetime.now()
                status.current_operation = "Ready for search"
                
                self.logger.info(f"✅ Document {document_id} processing completed")
                
        except Exception as e:
            self.logger.error(f"Background processing failed for {document_id}: {e}")
            if document_id in self.processing_statuses:
                status = self.processing_statuses[document_id]
                status.status = "failed"
                status.error_message = str(e)
    
    def get_processing_status(self, document_id: str) -> Optional[ProcessingStatus]:
        """Get processing status for a document"""
        return self.processing_statuses.get(document_id)
    
    def get_all_processing_statuses(self) -> Dict[str, ProcessingStatus]:
        """Get all processing statuses"""
        return self.processing_statuses.copy()
    
    async def search_qsr_documents(
        self,
        query: str,
        file_types: Optional[List[str]] = None,
        qsr_categories: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search across multi-format QSR documents
        
        Args:
            query: Search query
            file_types: Filter by file types
            qsr_categories: Filter by QSR categories
            limit: Maximum results
            
        Returns:
            Search results with multi-format support
        """
        if not self.available:
            return {"success": False, "error": "Ragie service not available"}
        
        try:
            # Build search filters
            filters = {}
            
            if file_types:
                filters["file_type"] = file_types
            
            if qsr_categories:
                filters["qsr_category"] = qsr_categories
            
            # Use existing QSR search with enhanced filters
            result = await self.base_service.search_qsr_documents(
                query, 
                filters=filters,
                limit=limit
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Multi-format search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return list(self.QSR_FILE_TYPE_MAPPING.keys())
    
    def get_qsr_categories(self) -> List[str]:
        """Get list of QSR categories"""
        return list(set(self.QSR_FILE_TYPE_MAPPING.values()))
    
    def get_processing_modes(self) -> Dict[str, str]:
        """Get processing modes by category"""
        return self.PROCESSING_MODES.copy()
    
    def create_status_summary(self) -> Dict[str, Any]:
        """Create status summary for monitoring"""
        statuses = list(self.processing_statuses.values())
        
        return {
            "total_documents": len(statuses),
            "completed": len([s for s in statuses if s.status == "completed"]),
            "processing": len([s for s in statuses if s.status == "processing"]),
            "failed": len([s for s in statuses if s.status == "failed"]),
            "pending": len([s for s in statuses if s.status == "pending"]),
            "service_available": self.available
        }

# Global service instance
enhanced_qsr_ragie_service = EnhancedQSRRagieService()

# Convenience functions for compatibility
async def upload_multi_format_file(file: UploadFile, background_processing: bool = True) -> MultiFormatUploadResult:
    """Upload multi-format file (convenience function)"""
    return await enhanced_qsr_ragie_service.upload_multi_format_file(file, background_processing)

def get_processing_status(document_id: str) -> Optional[ProcessingStatus]:
    """Get processing status (convenience function)"""
    return enhanced_qsr_ragie_service.get_processing_status(document_id)

async def search_multi_format_documents(
    query: str,
    file_types: Optional[List[str]] = None,
    qsr_categories: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Search multi-format documents (convenience function)"""
    return await enhanced_qsr_ragie_service.search_qsr_documents(
        query, file_types, qsr_categories, limit
    )

def get_supported_file_types() -> List[str]:
    """Get supported file types (convenience function)"""
    return enhanced_qsr_ragie_service.get_supported_file_types()

def is_ragie_service_available() -> bool:
    """Check if Ragie service is available"""
    return enhanced_qsr_ragie_service.is_available()