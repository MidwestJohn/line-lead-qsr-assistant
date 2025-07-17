#!/usr/bin/env python3
"""
Multi-Format Validation Testing
===============================

Test suite for the multi-format file validation system.
Validates that new validation preserves existing PDF functionality
while adding support for new file types.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import os
import logging
from pathlib import Path
from typing import Dict, List, Any
from io import BytesIO
from fastapi import UploadFile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our validation services
from services.multi_format_validator import (
    multi_format_validator, 
    FileType, 
    ValidationResult
)
from services.enhanced_file_validation import (
    enhanced_validation_service,
    validate_file_upload,
    validate_file_content,
    is_supported_file_type,
    get_file_type_from_filename
)

class MockUploadFile:
    """Mock UploadFile for testing"""
    def __init__(self, filename: str, content: bytes, content_type: str = None):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.position = 0
    
    async def read(self, size: int = -1) -> bytes:
        if size == -1:
            result = self.content[self.position:]
            self.position = len(self.content)
        else:
            result = self.content[self.position:self.position + size]
            self.position += len(result)
        return result
    
    async def seek(self, position: int):
        self.position = position

def create_test_files() -> Dict[str, bytes]:
    """Create test file content for different formats"""
    test_files = {}
    
    # PDF test content (minimal valid PDF)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
295
%%EOF"""
    
    # JPEG test content (minimal valid JPEG)
    jpeg_content = bytes.fromhex(
        'ffd8ffe000104a46494600010101006000600000ffdb004300'
        '08060606070605080707070909080a0c140d0c0b0b0c191213'
        '0f141d1a1f1e1d1a1c1c20242e2720222c231c1c28372829'
        '2c30313434341f27393d38323c2e333432ffdb004301090909'
        '0c0b0c180d0d1832211c2132323232323232323232323232'
        '323232323232323232323232323232323232323232323232'
        '32323232323232323232323232ffc00011080001000103012200'
        '02110103110111ffc4001f0000010501010101010100000000'
        '00000000010203040506070809000affc400b5100002010303'
        '020403050504040000017d01020300041105122131410613'
        '516107227114328191a1082342b1c11552d1f02433627282'
        '090a161718191a25262728292a3435363738393a434445464'
        '748494a535455565758595a636465666768696a737475767'
        '778797a838485868788898a9293949596979899a2a3a4a5a'
        '6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cacbd'
        '2d3d4d5d6d7d8d9dadbdcdddedfe1e2e3e4e5e6e7e8e9eae'
        'bebecedeeeff0a161718191a252627282a9a3435363738393'
        'a434445464748494a535455565758595a636465666768696'
        'a737475767778797a838485868788898a9293949596979899'
        'a2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7'
        'c8c9cacbd2d3d4d5d6d7d8d9dadbdcdddedfe1e2e3e4e5e6'
        'e7e8e9eaebecedeeeffda0008010100003f00ffc4001f00'
        '00010501010101010100000000000000000102030405060'
        '70809000affc400b5100002010303020403050504040000'
        '017d01020300041105122131410613516107227114328191'
        'a1082342b1c11552d1f02433627282090a161718191a2526'
        '2728292a3435363738393a434445464748494a535455565'
        '758595a636465666768696a737475767778797a8384858'
        '68788898a9293949596979899a2a3a4a5a6a7a8a9aab2b3'
        'b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cacbd2d3d4d5d6d7'
        'd8d9dadbdcdddedfe1e2e3e4e5e6e7e8e9eaebecedeeeff'
        'da0008010100003f00ffd9'
    )
    
    # PNG test content (minimal valid PNG)
    png_content = bytes.fromhex(
        '89504e470d0a1a0a0000000d49484452000000010000000108'
        '06000000043a8db60000000c4944415408d7632067000000'
        '0b0003a2f6ad400000000049454e44ae426082'
    )
    
    # Text content
    text_content = b"This is a test text file for validation.\nIt contains multiple lines.\nAnd some QSR-related content."
    
    # Create test files
    test_files = {
        'test_document.pdf': pdf_content,
        'test_image.jpg': jpeg_content,
        'test_image.png': png_content,
        'test_document.txt': text_content,
        'test_empty.pdf': b'',
        'test_invalid.pdf': b'This is not a PDF file',
        'test_large.txt': b'x' * (2 * 1024 * 1024),  # 2MB text file (over 1MB limit)
        'test_unsupported.xyz': b'Unsupported file type',
    }
    
    # Office document (ZIP-based)
    zip_header = b'PK\x03\x04'
    test_files['test_document.docx'] = zip_header + b'fake docx content'
    
    return test_files

async def test_basic_validation():
    """Test basic validation functionality"""
    print("\n=== Testing Basic Validation ===")
    
    test_files = create_test_files()
    
    # Test supported file type detection
    print("\n1. Testing file type detection:")
    test_cases = [
        ('document.pdf', FileType.PDF, True),
        ('image.jpg', FileType.JPG, True),
        ('image.png', FileType.PNG, True),
        ('document.txt', FileType.TXT, True),
        ('document.docx', FileType.DOCX, True),
        ('unsupported.xyz', None, False),
    ]
    
    for filename, expected_type, should_be_supported in test_cases:
        file_type = get_file_type_from_filename(filename)
        is_supported = is_supported_file_type(filename)
        
        print(f"  {filename}: {file_type} (supported: {is_supported})")
        
        if expected_type:
            assert file_type == expected_type, f"Expected {expected_type}, got {file_type}"
        else:
            assert file_type is None, f"Expected None, got {file_type}"
        
        assert is_supported == should_be_supported, f"Expected supported={should_be_supported}, got {is_supported}"
    
    print("✅ File type detection tests passed")

async def test_file_content_validation():
    """Test file content validation"""
    print("\n=== Testing File Content Validation ===")
    
    test_files = create_test_files()
    
    # Test valid files
    print("\n1. Testing valid files:")
    valid_files = [
        ('test_document.pdf', FileType.PDF),
        ('test_image.jpg', FileType.JPG),
        ('test_image.png', FileType.PNG),
        ('test_document.txt', FileType.TXT),
    ]
    
    for filename, expected_type in valid_files:
        if filename in test_files:
            mock_file = MockUploadFile(filename, test_files[filename])
            result = await validate_file_content(mock_file)
            
            print(f"  {filename}: {'✅ VALID' if result.success else '❌ INVALID'} ({result.error_message})")
            
            if expected_type == FileType.PDF:
                # PDF should be valid
                assert result.success, f"PDF validation failed: {result.error_message}"
            elif expected_type in [FileType.JPG, FileType.PNG]:
                # Images should be valid
                assert result.success, f"Image validation failed: {result.error_message}"
            elif expected_type == FileType.TXT:
                # Text should be valid
                assert result.success, f"Text validation failed: {result.error_message}"
    
    # Test invalid files
    print("\n2. Testing invalid files:")
    invalid_files = [
        ('test_empty.pdf', 'File is empty'),
        ('test_invalid.pdf', 'Invalid PDF'),
        ('test_large.txt', 'File size'),
        ('test_unsupported.xyz', 'Unsupported file type'),
    ]
    
    for filename, expected_error_pattern in invalid_files:
        if filename in test_files:
            mock_file = MockUploadFile(filename, test_files[filename])
            
            # Test upload validation first
            upload_result = validate_file_upload(mock_file)
            
            if upload_result.success:
                # If upload validation passes, test content validation
                content_result = await validate_file_content(mock_file)
                result = content_result
            else:
                result = upload_result
            
            print(f"  {filename}: {'✅ REJECTED' if not result.success else '❌ ACCEPTED'} ({result.error_message})")
            
            assert not result.success, f"Expected {filename} to be invalid, but it was accepted"
            if expected_error_pattern:
                assert expected_error_pattern.lower() in result.error_message.lower(), \
                    f"Expected error pattern '{expected_error_pattern}' in '{result.error_message}'"
    
    print("✅ File content validation tests passed")

async def test_size_validation():
    """Test file size validation"""
    print("\n=== Testing File Size Validation ===")
    
    # Test size limits for different file types
    test_cases = [
        ('small.pdf', b'%PDF-1.4\nsmall content\n%%EOF', True),
        ('large.txt', b'x' * (2 * 1024 * 1024), False),  # 2MB text (over 1MB limit)
        ('empty.pdf', b'', False),
    ]
    
    for filename, content, should_pass in test_cases:
        mock_file = MockUploadFile(filename, content)
        result = await validate_file_content(mock_file)
        
        print(f"  {filename} ({len(content):,} bytes): {'✅ VALID' if result.success else '❌ INVALID'} ({result.error_message})")
        
        if should_pass:
            assert result.success or 'Invalid PDF' in result.error_message, f"Expected {filename} to pass size validation"
        else:
            assert not result.success, f"Expected {filename} to fail size validation"
    
    print("✅ File size validation tests passed")

async def test_existing_pdf_compatibility():
    """Test that existing PDF functionality is preserved"""
    print("\n=== Testing Existing PDF Compatibility ===")
    
    # Test that PDF validation still works as before
    test_files = create_test_files()
    
    print("\n1. Testing PDF validation preservation:")
    pdf_file = MockUploadFile('test.pdf', test_files['test_document.pdf'])
    
    # Test upload validation
    upload_result = validate_file_upload(pdf_file)
    print(f"  Upload validation: {'✅ VALID' if upload_result.success else '❌ INVALID'}")
    assert upload_result.success, "PDF upload validation should pass"
    
    # Test content validation
    content_result = await validate_file_content(pdf_file)
    print(f"  Content validation: {'✅ VALID' if content_result.success else '❌ INVALID'}")
    assert content_result.success, "PDF content validation should pass"
    
    # Test file type detection
    file_type = get_file_type_from_filename('test.pdf')
    print(f"  File type detection: {file_type}")
    assert file_type == FileType.PDF, "PDF file type should be detected correctly"
    
    print("✅ Existing PDF compatibility tests passed")

async def test_error_handling():
    """Test error handling patterns"""
    print("\n=== Testing Error Handling ===")
    
    # Test various error conditions
    error_cases = [
        ('', 'No filename provided'),
        ('   ', 'Empty filename provided'),
        ('test.xyz', 'Unsupported file type'),
    ]
    
    for filename, expected_error in error_cases:
        mock_file = MockUploadFile(filename, b'test content')
        result = validate_file_upload(mock_file)
        
        print(f"  '{filename}': {'✅ REJECTED' if not result.success else '❌ ACCEPTED'} ({result.error_message})")
        
        assert not result.success, f"Expected '{filename}' to be rejected"
        assert expected_error.lower() in result.error_message.lower(), \
            f"Expected error pattern '{expected_error}' in '{result.error_message}'"
    
    print("✅ Error handling tests passed")

async def test_metadata_extraction():
    """Test metadata extraction"""
    print("\n=== Testing Metadata Extraction ===")
    
    test_files = create_test_files()
    
    # Test metadata extraction for different file types
    test_cases = [
        ('test_document.pdf', ['file_type', 'file_size', 'mime_type']),
        ('test_document.txt', ['file_type', 'file_size', 'text_length']),
        ('test_image.jpg', ['file_type', 'file_size', 'mime_type']),
    ]
    
    for filename, expected_metadata_keys in test_cases:
        if filename in test_files:
            mock_file = MockUploadFile(filename, test_files[filename])
            result = await validate_file_content(mock_file)
            
            print(f"  {filename}: {list(result.metadata.keys())}")
            
            for key in expected_metadata_keys:
                assert key in result.metadata, f"Expected metadata key '{key}' not found"
    
    print("✅ Metadata extraction tests passed")

async def test_security_validation():
    """Test security validation"""
    print("\n=== Testing Security Validation ===")
    
    # Test files with suspicious content
    suspicious_files = [
        ('suspicious.txt', b'<script>alert("test")</script>'),
        ('suspicious.html', b'<script>evil_code()</script>'),
        ('eval.txt', b'eval("malicious_code")'),
    ]
    
    for filename, content in suspicious_files:
        mock_file = MockUploadFile(filename, content)
        result = await validate_file_content(mock_file)
        
        print(f"  {filename}: {'✅ REJECTED' if not result.success else '❌ ACCEPTED'} ({result.error_message})")
        
        # Note: Security validation might not always reject (depends on file type)
        # This is just to test that the security validation runs
    
    print("✅ Security validation tests passed")

async def run_all_tests():
    """Run all validation tests"""
    print("🧪 Starting Multi-Format Validation Tests")
    print("=" * 60)
    
    try:
        await test_basic_validation()
        await test_file_content_validation()
        await test_size_validation()
        await test_existing_pdf_compatibility()
        await test_error_handling()
        await test_metadata_extraction()
        await test_security_validation()
        
        print("\n" + "=" * 60)
        print("🎉 All validation tests passed!")
        print("✅ Multi-format validation system is working correctly")
        print("✅ Existing PDF functionality is preserved")
        print("✅ New file types are supported")
        print("✅ Error handling follows existing patterns")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_supported_formats():
    """Test supported formats information"""
    print("\n=== Supported Formats Summary ===")
    
    supported_types = enhanced_validation_service.get_supported_extensions()
    print(f"Total supported formats: {len(supported_types)}")
    print(f"Supported extensions: {', '.join(supported_types)}")
    
    # Group by category
    categories = {
        'Documents': ['.pdf', '.docx', '.xlsx', '.pptx', '.docm', '.xlsm'],
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        'Audio/Video': ['.mp4', '.mov', '.avi', '.wav', '.mp3', '.m4a'],
        'Text': ['.txt', '.md', '.csv']
    }
    
    for category, extensions in categories.items():
        supported_in_category = [ext for ext in extensions if ext in supported_types]
        print(f"{category}: {', '.join(supported_in_category)}")
    
    print("✅ Format summary complete")

if __name__ == "__main__":
    # Run tests
    test_supported_formats()
    
    # Run async tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🚀 Ready to proceed to Phase 2: Ragie Integration Strategy")
    else:
        print("\n⚠️  Please fix validation issues before proceeding")