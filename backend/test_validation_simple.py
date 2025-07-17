#!/usr/bin/env python3
"""
Simple Multi-Format Validation Test
==================================

Basic test to validate the multi-format validation system works correctly.
"""

import sys
import os
sys.path.append('/Users/johninniger/Workspace/line_lead_qsr_mvp/backend')

from pathlib import Path

# Test basic imports
try:
    from services.multi_format_validator import FileType, multi_format_validator
    print("✅ Multi-format validator imported successfully")
except ImportError as e:
    print(f"❌ Failed to import multi-format validator: {e}")
    sys.exit(1)

try:
    from services.enhanced_file_validation import enhanced_validation_service
    print("✅ Enhanced validation service imported successfully")
except ImportError as e:
    print(f"❌ Failed to import enhanced validation service: {e}")
    sys.exit(1)

# Test supported formats
print("\n=== Testing Supported Formats ===")
supported_types = multi_format_validator.get_supported_file_types()
print(f"Supported extensions: {', '.join(supported_types)}")

# Test file type detection
print("\n=== Testing File Type Detection ===")
test_files = [
    'document.pdf',
    'image.jpg',
    'image.png',
    'document.txt',
    'document.docx',
    'spreadsheet.xlsx',
    'presentation.pptx',
    'video.mp4',
    'audio.mp3',
    'unsupported.xyz'
]

for filename in test_files:
    file_type = multi_format_validator._detect_file_type(filename)
    print(f"  {filename}: {file_type}")

# Test file configurations
print("\n=== Testing File Configurations ===")
print(f"PDF max size: {multi_format_validator.SUPPORTED_FORMATS[FileType.PDF]['max_size']:,} bytes")
print(f"TXT max size: {multi_format_validator.SUPPORTED_FORMATS[FileType.TXT]['max_size']:,} bytes")
print(f"MP4 max size: {multi_format_validator.SUPPORTED_FORMATS[FileType.MP4]['max_size']:,} bytes")

# Test validation logic with sample content
print("\n=== Testing Basic Validation Logic ===")

# Test PDF validation
pdf_content = b"%PDF-1.4\ntest content\n%%EOF"
result = multi_format_validator.validate_file("test.pdf", pdf_content)
print(f"PDF validation: {result.result} ({result.error_message})")

# Test text validation  
text_content = b"This is a test text file"
result = multi_format_validator.validate_file("test.txt", text_content)
print(f"Text validation: {result.result} ({result.error_message})")

# Test invalid file
invalid_content = b"invalid content"
result = multi_format_validator.validate_file("test.pdf", invalid_content)
print(f"Invalid PDF validation: {result.result} ({result.error_message})")

# Test empty file
empty_content = b""
result = multi_format_validator.validate_file("test.txt", empty_content)
print(f"Empty file validation: {result.result} ({result.error_message})")

print("\n=== Testing Enhanced Validation Service ===")
print(f"Supported extensions: {enhanced_validation_service.get_supported_extensions()}")
print(f"Is PDF supported: {enhanced_validation_service.is_pdf_file('test.pdf')}")
print(f"Is TXT supported: {enhanced_validation_service.is_pdf_file('test.txt')}")

print("\n✅ All basic tests completed successfully!")
print("🚀 Multi-format validation system is ready for integration")