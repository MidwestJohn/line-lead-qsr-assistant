#!/usr/bin/env python3
"""
Multi-Format File Validator
===========================

Extends existing PDF validation patterns to support comprehensive multi-format file validation.
Follows established Line Lead patterns for consistency and reliability.

Based on Phase 0 investigation findings:
- Preserves existing PDF validation logic
- Extends current error handling patterns
- Maintains existing performance characteristics
- Integrates with existing health monitoring

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import logging
import mimetypes
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import PyPDF2
from io import BytesIO

# Import existing PDF validation functions to preserve patterns
try:
    from main import is_valid_pdf, extract_pdf_text
    PDF_VALIDATION_AVAILABLE = True
except ImportError:
    PDF_VALIDATION_AVAILABLE = False

# Handle magic import gracefully
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class FileType(Enum):
    """Supported file types with validation categories"""
    # Documents
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    DOCM = "docm"
    XLSM = "xlsm"
    TXT = "txt"
    
    # Images
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
    
    # Audio/Video
    MP4 = "mp4"
    MOV = "mov"
    AVI = "avi"
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    
    # Text
    MD = "md"
    CSV = "csv"

class ValidationResult(Enum):
    """Validation result types"""
    VALID = "valid"
    INVALID_TYPE = "invalid_type"
    INVALID_SIZE = "invalid_size"
    INVALID_CONTENT = "invalid_content"
    SECURITY_RISK = "security_risk"
    CORRUPTED = "corrupted"

@dataclass
class FileValidationResult:
    """Result of file validation"""
    result: ValidationResult
    file_type: Optional[FileType] = None
    detected_mime: Optional[str] = None
    file_size: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}

class MultiFormatValidator:
    """
    Multi-format file validator following existing Line Lead patterns
    """
    
    # File type configurations based on existing patterns
    SUPPORTED_FORMATS = {
        # Documents (complex validation)
        FileType.PDF: {
            'extensions': ['.pdf'],
            'mime_types': ['application/pdf'],
            'max_size': 10 * 1024 * 1024,  # 10MB - matches existing PDF limit
            'validation_level': 'complex'
        },
        FileType.DOCX: {
            'extensions': ['.docx'],
            'mime_types': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'validation_level': 'complex'
        },
        FileType.XLSX: {
            'extensions': ['.xlsx'],
            'mime_types': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'validation_level': 'complex'
        },
        FileType.PPTX: {
            'extensions': ['.pptx'],
            'mime_types': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
            'max_size': 25 * 1024 * 1024,  # 25MB (presentations can be larger)
            'validation_level': 'complex'
        },
        FileType.DOCM: {
            'extensions': ['.docm'],
            'mime_types': ['application/vnd.ms-word.document.macroEnabled.12'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'validation_level': 'complex'
        },
        FileType.XLSM: {
            'extensions': ['.xlsm'],
            'mime_types': ['application/vnd.ms-excel.sheet.macroEnabled.12'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'validation_level': 'complex'
        },
        
        # Images (simpler validation)
        FileType.JPG: {
            'extensions': ['.jpg'],
            'mime_types': ['image/jpeg'],
            'max_size': 5 * 1024 * 1024,  # 5MB
            'validation_level': 'simple'
        },
        FileType.JPEG: {
            'extensions': ['.jpeg'],
            'mime_types': ['image/jpeg'],
            'max_size': 5 * 1024 * 1024,  # 5MB
            'validation_level': 'simple'
        },
        FileType.PNG: {
            'extensions': ['.png'],
            'mime_types': ['image/png'],
            'max_size': 5 * 1024 * 1024,  # 5MB
            'validation_level': 'simple'
        },
        FileType.GIF: {
            'extensions': ['.gif'],
            'mime_types': ['image/gif'],
            'max_size': 10 * 1024 * 1024,  # 10MB (GIFs can be larger)
            'validation_level': 'simple'
        },
        FileType.WEBP: {
            'extensions': ['.webp'],
            'mime_types': ['image/webp'],
            'max_size': 5 * 1024 * 1024,  # 5MB
            'validation_level': 'simple'
        },
        
        # Audio/Video (complex validation)
        FileType.MP4: {
            'extensions': ['.mp4'],
            'mime_types': ['video/mp4'],
            'max_size': 50 * 1024 * 1024,  # 50MB
            'validation_level': 'complex'
        },
        FileType.MOV: {
            'extensions': ['.mov'],
            'mime_types': ['video/quicktime'],
            'max_size': 50 * 1024 * 1024,  # 50MB
            'validation_level': 'complex'
        },
        FileType.AVI: {
            'extensions': ['.avi'],
            'mime_types': ['video/x-msvideo'],
            'max_size': 100 * 1024 * 1024,  # 100MB
            'validation_level': 'complex'
        },
        FileType.WAV: {
            'extensions': ['.wav'],
            'mime_types': ['audio/wav', 'audio/x-wav'],
            'max_size': 25 * 1024 * 1024,  # 25MB
            'validation_level': 'complex'
        },
        FileType.MP3: {
            'extensions': ['.mp3'],
            'mime_types': ['audio/mpeg'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'validation_level': 'complex'
        },
        FileType.M4A: {
            'extensions': ['.m4a'],
            'mime_types': ['audio/mp4'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'validation_level': 'complex'
        },
        
        # Text (simplest validation)
        FileType.TXT: {
            'extensions': ['.txt'],
            'mime_types': ['text/plain'],
            'max_size': 1 * 1024 * 1024,  # 1MB
            'validation_level': 'simple'
        },
        FileType.MD: {
            'extensions': ['.md'],
            'mime_types': ['text/markdown', 'text/x-markdown'],
            'max_size': 1 * 1024 * 1024,  # 1MB
            'validation_level': 'simple'
        },
        FileType.CSV: {
            'extensions': ['.csv'],
            'mime_types': ['text/csv'],
            'max_size': 5 * 1024 * 1024,  # 5MB
            'validation_level': 'simple'
        }
    }
    
    def __init__(self):
        """Initialize validator with existing patterns"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize MIME type detection
        if MAGIC_AVAILABLE:
            try:
                self.magic_mime = magic.Magic(mime=True)
                self.magic_available = True
            except:
                self.magic_available = False
                self.logger.warning("python-magic not available, using mimetypes fallback")
        else:
            self.magic_available = False
            self.logger.info("python-magic not installed, using basic MIME detection")
    
    def validate_file(self, filename: str, content: bytes) -> FileValidationResult:
        """
        Validate file following existing Line Lead patterns
        
        Args:
            filename: Original filename
            content: File content bytes
            
        Returns:
            FileValidationResult with validation outcome
        """
        try:
            # Step 1: Detect file type (following existing pattern)
            file_type = self._detect_file_type(filename)
            if not file_type:
                return FileValidationResult(
                    result=ValidationResult.INVALID_TYPE,
                    error_message=f"Unsupported file type: {Path(filename).suffix}",
                    file_size=len(content)
                )
            
            # Step 2: Validate file size (following existing pattern)
            size_result = self._validate_file_size(file_type, content)
            if size_result.result != ValidationResult.VALID:
                return size_result
            
            # Step 3: Validate MIME type (new security layer)
            mime_result = self._validate_mime_type(file_type, content)
            if mime_result.result != ValidationResult.VALID:
                return mime_result
            
            # Step 4: Content validation (following existing PDF pattern)
            content_result = self._validate_content(file_type, content)
            if content_result.result != ValidationResult.VALID:
                return content_result
            
            # Step 5: Security validation (new security layer)
            security_result = self._validate_security(file_type, content)
            if security_result.result != ValidationResult.VALID:
                return security_result
            
            # Successful validation
            return FileValidationResult(
                result=ValidationResult.VALID,
                file_type=file_type,
                detected_mime=self._detect_mime_type(content),
                file_size=len(content),
                metadata=self._extract_metadata(file_type, content)
            )
            
        except Exception as e:
            self.logger.error(f"Validation error for {filename}: {e}")
            return FileValidationResult(
                result=ValidationResult.CORRUPTED,
                error_message=f"File validation failed: {str(e)}",
                file_size=len(content)
            )
    
    def _detect_file_type(self, filename: str) -> Optional[FileType]:
        """Detect file type from filename extension"""
        extension = Path(filename).suffix.lower()
        
        for file_type, config in self.SUPPORTED_FORMATS.items():
            if extension in config['extensions']:
                return file_type
        
        return None
    
    def _validate_file_size(self, file_type: FileType, content: bytes) -> FileValidationResult:
        """Validate file size following existing pattern"""
        file_size = len(content)
        max_size = self.SUPPORTED_FORMATS[file_type]['max_size']
        
        if file_size > max_size:
            return FileValidationResult(
                result=ValidationResult.INVALID_SIZE,
                file_type=file_type,
                file_size=file_size,
                error_message=f"File size ({file_size:,} bytes) exceeds maximum allowed size ({max_size:,} bytes)"
            )
        
        if file_size == 0:
            return FileValidationResult(
                result=ValidationResult.INVALID_SIZE,
                file_type=file_type,
                file_size=file_size,
                error_message="File is empty"
            )
        
        return FileValidationResult(
            result=ValidationResult.VALID,
            file_type=file_type,
            file_size=file_size
        )
    
    def _detect_mime_type(self, content: bytes) -> Optional[str]:
        """Detect MIME type from content"""
        try:
            if self.magic_available:
                return self.magic_mime.from_buffer(content)
            else:
                # Fallback to basic detection
                if content.startswith(b'%PDF'):
                    return 'application/pdf'
                elif content.startswith(b'PK'):
                    return 'application/zip'  # Office documents are ZIP-based
                elif content.startswith(b'\xff\xd8\xff'):
                    return 'image/jpeg'
                elif content.startswith(b'\x89PNG'):
                    return 'image/png'
                else:
                    return 'application/octet-stream'
        except:
            return None
    
    def _validate_mime_type(self, file_type: FileType, content: bytes) -> FileValidationResult:
        """Validate MIME type matches expected type"""
        detected_mime = self._detect_mime_type(content)
        expected_mimes = self.SUPPORTED_FORMATS[file_type]['mime_types']
        
        if detected_mime and detected_mime not in expected_mimes:
            # Special handling for Office documents (they're ZIP-based)
            if file_type in [FileType.DOCX, FileType.XLSX, FileType.PPTX, FileType.DOCM, FileType.XLSM]:
                if detected_mime in ['application/zip', 'application/x-zip-compressed']:
                    # This is acceptable for Office documents
                    pass
                else:
                    return FileValidationResult(
                        result=ValidationResult.SECURITY_RISK,
                        file_type=file_type,
                        detected_mime=detected_mime,
                        error_message=f"MIME type mismatch: detected {detected_mime}, expected one of {expected_mimes}"
                    )
            # Special handling for text files (they often get detected as application/octet-stream)
            elif file_type in [FileType.TXT, FileType.MD, FileType.CSV]:
                if detected_mime in ['application/octet-stream', 'text/plain']:
                    # Try to validate as text by attempting to decode
                    try:
                        content.decode('utf-8')
                        # If it decodes successfully, it's likely text
                        pass
                    except UnicodeDecodeError:
                        return FileValidationResult(
                            result=ValidationResult.SECURITY_RISK,
                            file_type=file_type,
                            detected_mime=detected_mime,
                            error_message=f"File appears to be binary, not text: {detected_mime}"
                        )
                else:
                    return FileValidationResult(
                        result=ValidationResult.SECURITY_RISK,
                        file_type=file_type,
                        detected_mime=detected_mime,
                        error_message=f"MIME type mismatch: detected {detected_mime}, expected one of {expected_mimes}"
                    )
            else:
                return FileValidationResult(
                    result=ValidationResult.SECURITY_RISK,
                    file_type=file_type,
                    detected_mime=detected_mime,
                    error_message=f"MIME type mismatch: detected {detected_mime}, expected one of {expected_mimes}"
                )
        
        return FileValidationResult(
            result=ValidationResult.VALID,
            file_type=file_type,
            detected_mime=detected_mime
        )
    
    def _validate_content(self, file_type: FileType, content: bytes) -> FileValidationResult:
        """Validate file content following existing patterns"""
        try:
            # PDF validation (preserve existing logic)
            if file_type == FileType.PDF:
                if PDF_VALIDATION_AVAILABLE:
                    if not is_valid_pdf(content):
                        return FileValidationResult(
                            result=ValidationResult.INVALID_CONTENT,
                            file_type=file_type,
                            error_message="Invalid PDF file"
                        )
                    
                    # Check if text can be extracted
                    try:
                        text, pages = extract_pdf_text(content)
                        if not text.strip():
                            return FileValidationResult(
                                result=ValidationResult.INVALID_CONTENT,
                                file_type=file_type,
                                error_message="No text could be extracted from PDF"
                            )
                        
                        return FileValidationResult(
                            result=ValidationResult.VALID,
                            file_type=file_type,
                            metadata={'pages': pages, 'text_length': len(text)}
                        )
                    except Exception as e:
                        return FileValidationResult(
                            result=ValidationResult.INVALID_CONTENT,
                            file_type=file_type,
                            error_message=f"PDF text extraction failed: {str(e)}"
                        )
                else:
                    # Basic PDF validation
                    if not content.startswith(b'%PDF'):
                        return FileValidationResult(
                            result=ValidationResult.INVALID_CONTENT,
                            file_type=file_type,
                            error_message="Invalid PDF file format"
                        )
            
            # Office documents validation
            elif file_type in [FileType.DOCX, FileType.XLSX, FileType.PPTX, FileType.DOCM, FileType.XLSM]:
                if not content.startswith(b'PK'):
                    return FileValidationResult(
                        result=ValidationResult.INVALID_CONTENT,
                        file_type=file_type,
                        error_message="Invalid Office document format"
                    )
            
            # Image validation
            elif file_type in [FileType.JPG, FileType.JPEG]:
                if not content.startswith(b'\xff\xd8\xff'):
                    return FileValidationResult(
                        result=ValidationResult.INVALID_CONTENT,
                        file_type=file_type,
                        error_message="Invalid JPEG format"
                    )
            
            elif file_type == FileType.PNG:
                if not content.startswith(b'\x89PNG'):
                    return FileValidationResult(
                        result=ValidationResult.INVALID_CONTENT,
                        file_type=file_type,
                        error_message="Invalid PNG format"
                    )
            
            elif file_type == FileType.GIF:
                if not content.startswith(b'GIF'):
                    return FileValidationResult(
                        result=ValidationResult.INVALID_CONTENT,
                        file_type=file_type,
                        error_message="Invalid GIF format"
                    )
            
            # Text validation
            elif file_type in [FileType.TXT, FileType.MD, FileType.CSV]:
                try:
                    # Try to decode as UTF-8
                    text = content.decode('utf-8')
                    if not text.strip():
                        return FileValidationResult(
                            result=ValidationResult.INVALID_CONTENT,
                            file_type=file_type,
                            error_message="Text file is empty"
                        )
                except UnicodeDecodeError:
                    return FileValidationResult(
                        result=ValidationResult.INVALID_CONTENT,
                        file_type=file_type,
                        error_message="Text file contains invalid UTF-8 characters"
                    )
            
            # Video/Audio validation (basic)
            elif file_type in [FileType.MP4, FileType.MOV, FileType.AVI, FileType.WAV, FileType.MP3, FileType.M4A]:
                # Basic header validation for common formats
                if file_type == FileType.MP4:
                    # MP4 files have 'ftyp' box early in the file
                    if b'ftyp' not in content[:100]:
                        return FileValidationResult(
                            result=ValidationResult.INVALID_CONTENT,
                            file_type=file_type,
                            error_message="Invalid MP4 format"
                        )
                
                elif file_type == FileType.WAV:
                    if not content.startswith(b'RIFF'):
                        return FileValidationResult(
                            result=ValidationResult.INVALID_CONTENT,
                            file_type=file_type,
                            error_message="Invalid WAV format"
                        )
                
                elif file_type == FileType.MP3:
                    if not (content.startswith(b'ID3') or content.startswith(b'\xff\xfb')):
                        return FileValidationResult(
                            result=ValidationResult.INVALID_CONTENT,
                            file_type=file_type,
                            error_message="Invalid MP3 format"
                        )
            
            return FileValidationResult(
                result=ValidationResult.VALID,
                file_type=file_type
            )
            
        except Exception as e:
            return FileValidationResult(
                result=ValidationResult.CORRUPTED,
                file_type=file_type,
                error_message=f"Content validation failed: {str(e)}"
            )
    
    def _validate_security(self, file_type: FileType, content: bytes) -> FileValidationResult:
        """Basic security validation"""
        # Check for suspicious patterns
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'eval(',
            b'exec(',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in content.lower():
                return FileValidationResult(
                    result=ValidationResult.SECURITY_RISK,
                    file_type=file_type,
                    error_message=f"Suspicious content detected: {pattern.decode('utf-8', errors='ignore')}"
                )
        
        return FileValidationResult(
            result=ValidationResult.VALID,
            file_type=file_type
        )
    
    def _extract_metadata(self, file_type: FileType, content: bytes) -> Dict[str, Any]:
        """Extract basic metadata from file"""
        metadata = {
            'file_type': file_type.value,
            'file_size': len(content),
            'mime_type': self._detect_mime_type(content)
        }
        
        # PDF-specific metadata (preserve existing pattern)
        if file_type == FileType.PDF and PDF_VALIDATION_AVAILABLE:
            try:
                text, pages = extract_pdf_text(content)
                metadata.update({
                    'pages': pages,
                    'text_length': len(text),
                    'has_text': bool(text.strip())
                })
            except:
                pass
        
        # Text file metadata
        elif file_type in [FileType.TXT, FileType.MD, FileType.CSV]:
            try:
                text = content.decode('utf-8')
                metadata.update({
                    'text_length': len(text),
                    'line_count': len(text.splitlines())
                })
            except:
                pass
        
        return metadata
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file extensions"""
        extensions = []
        for config in self.SUPPORTED_FORMATS.values():
            extensions.extend(config['extensions'])
        return sorted(extensions)
    
    def get_file_type_info(self, file_type: FileType) -> Dict[str, Any]:
        """Get information about a specific file type"""
        return self.SUPPORTED_FORMATS.get(file_type, {})

# Global validator instance
multi_format_validator = MultiFormatValidator()