#!/usr/bin/env python3
"""
Enhanced File Validation Service
================================

Integrates multi-format validation with existing Line Lead error handling patterns.
Provides consistent validation experience across all file types while preserving
existing PDF validation behavior.

Following Phase 0 findings:
- Preserves all existing PDF functionality
- Follows existing error handling patterns
- Maintains existing performance characteristics  
- Integrates with existing health monitoring

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from dataclasses import dataclass
from fastapi import HTTPException, UploadFile

# Import existing validation patterns
from .multi_format_validator import (
    multi_format_validator, 
    FileType, 
    ValidationResult, 
    FileValidationResult
)

logger = logging.getLogger(__name__)

@dataclass 
class EnhancedValidationResult:
    """Enhanced validation result with Line Lead patterns"""
    success: bool
    file_type: Optional[FileType] = None
    file_size: int = 0
    error_message: Optional[str] = None
    http_status_code: int = 200
    metadata: Dict[str, Any] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.warnings is None:
            self.warnings = []

class EnhancedFileValidationService:
    """
    Enhanced file validation service that integrates with existing Line Lead patterns
    """
    
    def __init__(self):
        self.validator = multi_format_validator
        self.logger = logging.getLogger(__name__)
    
    def validate_upload_file(self, file: UploadFile) -> EnhancedValidationResult:
        """
        Validate uploaded file following existing Line Lead patterns
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            EnhancedValidationResult with validation outcome
            
        Raises:
            HTTPException: Following existing error patterns
        """
        try:
            # Step 1: Basic file checks (following existing pattern)
            if not file.filename:
                return EnhancedValidationResult(
                    success=False,
                    error_message="No filename provided",
                    http_status_code=400
                )
            
            if not file.filename.strip():
                return EnhancedValidationResult(
                    success=False,
                    error_message="Empty filename provided",
                    http_status_code=400
                )
            
            # Step 2: Check if file type is supported
            file_type = self.validator._detect_file_type(file.filename)
            if not file_type:
                supported_types = self.validator.get_supported_file_types()
                return EnhancedValidationResult(
                    success=False,
                    error_message=f"Unsupported file type. Supported types: {', '.join(supported_types)}",
                    http_status_code=400
                )
            
            return EnhancedValidationResult(
                success=True,
                file_type=file_type,
                metadata={'filename': file.filename, 'content_type': file.content_type}
            )
            
        except Exception as e:
            self.logger.error(f"Upload file validation error: {e}")
            return EnhancedValidationResult(
                success=False,
                error_message=f"Validation failed: {str(e)}",
                http_status_code=500
            )
    
    async def validate_file_content(self, file: UploadFile) -> EnhancedValidationResult:
        """
        Validate file content following existing Line Lead patterns
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            EnhancedValidationResult with validation outcome
        """
        try:
            # Step 1: Read file content
            content = await file.read()
            
            # Reset file position for potential reuse
            await file.seek(0)
            
            # Step 2: Validate content using multi-format validator
            validation_result = self.validator.validate_file(file.filename, content)
            
            # Step 3: Convert to enhanced result following existing patterns
            return self._convert_validation_result(validation_result, file.filename)
            
        except Exception as e:
            self.logger.error(f"File content validation error: {e}")
            return EnhancedValidationResult(
                success=False,
                error_message=f"Content validation failed: {str(e)}",
                http_status_code=500
            )
    
    def _convert_validation_result(self, result: FileValidationResult, filename: str) -> EnhancedValidationResult:
        """Convert validation result to enhanced result following existing patterns"""
        
        # Map validation results to HTTP status codes (following existing pattern)
        status_code_map = {
            ValidationResult.VALID: 200,
            ValidationResult.INVALID_TYPE: 400,
            ValidationResult.INVALID_SIZE: 400,
            ValidationResult.INVALID_CONTENT: 400,
            ValidationResult.SECURITY_RISK: 400,
            ValidationResult.CORRUPTED: 400
        }
        
        # Create enhanced result
        enhanced_result = EnhancedValidationResult(
            success=(result.result == ValidationResult.VALID),
            file_type=result.file_type,
            file_size=result.file_size,
            error_message=result.error_message,
            http_status_code=status_code_map.get(result.result, 500),
            metadata=result.metadata or {},
            warnings=result.warnings or []
        )
        
        # Add additional metadata
        enhanced_result.metadata.update({
            'filename': filename,
            'detected_mime': result.detected_mime,
            'validation_result': result.result.value
        })
        
        return enhanced_result
    
    def raise_validation_exception(self, result: EnhancedValidationResult):
        """
        Raise HTTPException following existing Line Lead patterns
        
        Args:
            result: EnhancedValidationResult with error details
            
        Raises:
            HTTPException: With appropriate status code and message
        """
        if result.success:
            return  # No exception needed
        
        # Log error following existing pattern
        self.logger.error(f"Validation failed: {result.error_message}")
        
        # Raise exception following existing error patterns
        raise HTTPException(
            status_code=result.http_status_code,
            detail=result.error_message or "Validation failed"
        )
    
    def get_file_type_info(self, filename: str) -> Dict[str, Any]:
        """Get information about file type"""
        file_type = self.validator._detect_file_type(filename)
        if not file_type:
            return {}
        
        return self.validator.get_file_type_info(file_type)
    
    def is_pdf_file(self, filename: str) -> bool:
        """Check if file is PDF (preserving existing pattern)"""
        file_type = self.validator._detect_file_type(filename)
        return file_type == FileType.PDF
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return self.validator.get_supported_file_types()
    
    def get_max_file_size(self, filename: str) -> int:
        """Get maximum file size for given file type"""
        file_type = self.validator._detect_file_type(filename)
        if not file_type:
            return 0
        
        return self.validator.SUPPORTED_FORMATS[file_type]['max_size']
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def create_validation_summary(self, result: EnhancedValidationResult) -> Dict[str, Any]:
        """Create validation summary for logging/monitoring"""
        return {
            'success': result.success,
            'file_type': result.file_type.value if result.file_type else None,
            'file_size': result.file_size,
            'file_size_formatted': self.format_file_size(result.file_size),
            'error_message': result.error_message,
            'warnings_count': len(result.warnings),
            'metadata': result.metadata
        }

# Global service instance
enhanced_validation_service = EnhancedFileValidationService()

# Compatibility functions for existing code
def validate_file_upload(file: UploadFile) -> EnhancedValidationResult:
    """Validate file upload (convenience function)"""
    return enhanced_validation_service.validate_upload_file(file)

async def validate_file_content(file: UploadFile) -> EnhancedValidationResult:
    """Validate file content (convenience function)"""
    return await enhanced_validation_service.validate_file_content(file)

def is_supported_file_type(filename: str) -> bool:
    """Check if file type is supported"""
    file_type = multi_format_validator._detect_file_type(filename)
    return file_type is not None

def get_file_type_from_filename(filename: str) -> Optional[FileType]:
    """Get file type from filename"""
    return multi_format_validator._detect_file_type(filename)

# For backward compatibility with existing PDF validation
def is_pdf_file(filename: str) -> bool:
    """Check if file is PDF (backward compatibility)"""
    return enhanced_validation_service.is_pdf_file(filename)

def get_supported_file_types() -> List[str]:
    """Get supported file types (backward compatibility)"""
    return enhanced_validation_service.get_supported_extensions()