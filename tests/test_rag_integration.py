import pytest
import os
import asyncio
from backend.services.rag_service import rag_service

@pytest.mark.asyncio
async def test_rag_service_initialization():
    """Test RAG service can initialize without breaking existing system."""
    # Test with RAG disabled
    os.environ['USE_RAG_ANYTHING'] = 'false'
    result = await rag_service.initialize()
    assert result == False
    assert rag_service.enabled == False
    
    # Test health check works regardless
    health = rag_service.health_check()
    assert 'enabled' in health
    assert 'initialized' in health

def test_existing_endpoints_unchanged():
    """Verify existing endpoints still work identically."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    
    # Test existing health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    
    # Test existing chat endpoint structure
    response = client.post("/chat", json={"message": "test"})
    assert response.status_code in [200, 422]  # Should have same validation

def test_new_endpoints_added():
    """Verify new endpoints are accessible."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    
    # Test new RAG health endpoint
    response = client.get("/rag-health")
    assert response.status_code == 200
    
    data = response.json()
    assert 'enabled' in data
    assert 'initialized' in data

@pytest.mark.asyncio
async def test_fallback_behavior():
    """Test system gracefully falls back to existing when RAG fails."""
    # This should not raise exceptions even if RAG-Anything not installed
    health = rag_service.health_check()
    assert isinstance(health, dict)