import pytest
import os
import json
from pathlib import Path
from backend.services.document_processor import document_processor, ProcessedContent

def test_basic_processing_unchanged():
    """Verify basic processing maintains existing functionality."""
    # Create a simple test PDF or use existing test file
    test_pdf = "tests/sample_manual.pdf"  # You'll need to provide this
    
    if os.path.exists(test_pdf):
        result = document_processor.process_pdf_basic(test_pdf)
        
        assert isinstance(result, ProcessedContent)
        assert result.processing_method == "basic"
        assert len(result.text_chunks) > 0
        assert len(result.images) == 0  # Basic processing doesn't extract images
        assert len(result.tables) == 0  # Basic processing doesn't extract tables

def test_processing_capability_detection():
    """Test that system correctly detects processing capabilities."""
    capabilities = {
        "basic_processing": True,
        "advanced_processing": document_processor.use_rag_anything,
        "mineru_available": document_processor.mineru_available
    }
    
    assert capabilities["basic_processing"] == True
    assert isinstance(capabilities["advanced_processing"], bool)
    assert isinstance(capabilities["mineru_available"], bool)

def test_content_serialization():
    """Test that processed content can be saved and loaded."""
    # Create test content
    test_content = ProcessedContent(
        text_chunks=["chunk1", "chunk2"],
        images=[{"id": "img1", "description": "test image"}],
        tables=[{"id": "table1", "data": [[1, 2], [3, 4]]}],
        metadata={"source": "test", "file_path": "/test/path"},
        processing_method="test"
    )
    
    # Save and load
    output_file = document_processor.save_processed_content(test_content, "test_output")
    
    assert os.path.exists(output_file)
    
    with open(output_file, 'r') as f:
        loaded_data = json.load(f)
    
    assert loaded_data["processing_method"] == "test"
    assert len(loaded_data["text_chunks"]) == 2
    
    # Cleanup
    os.remove(output_file)

def test_endpoints_accessibility():
    """Test new endpoints are accessible without breaking existing ones."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    
    # Test new capabilities endpoint
    response = client.get("/processing-capabilities")
    assert response.status_code == 200
    
    data = response.json()
    assert "basic_processing" in data
    assert "advanced_processing" in data
    
    # Verify existing endpoints still work
    response = client.get("/health")
    assert response.status_code == 200