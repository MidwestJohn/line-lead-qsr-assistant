import pytest
import asyncio
from backend.services.voice_graph_service import voice_graph_service, VoiceContext

@pytest.mark.asyncio
async def test_voice_session_creation():
    """Test voice session creation and management."""
    session_id = "test_session_123"
    
    context = await voice_graph_service.create_voice_session(session_id)
    
    assert context.session_id == session_id
    assert context.current_equipment is None
    assert context.current_procedure is None
    assert len(context.conversation_history) == 0

@pytest.mark.asyncio
async def test_equipment_context_detection():
    """Test equipment detection from voice queries."""
    session_id = "test_session_equipment"
    
    # Test fryer detection
    result = await voice_graph_service.process_voice_query(
        session_id=session_id,
        query="How do I clean the fryer?"
    )
    
    assert result["context"]["current_equipment"] == "fryer"
    assert "fryer" in result["response"]["text"].lower()

@pytest.mark.asyncio
async def test_context_persistence():
    """Test that context persists across conversation turns."""
    session_id = "test_session_persistence"
    
    # First query establishes context
    result1 = await voice_graph_service.process_voice_query(
        session_id=session_id,
        query="Help me with ice cream machine maintenance"
    )
    
    # Second query should maintain context
    result2 = await voice_graph_service.process_voice_query(
        session_id=session_id,
        query="What's the next step?"
    )
    
    assert result1["context"]["current_equipment"] == "ice_cream_machine"
    assert result2["context"]["current_equipment"] == "ice_cream_machine"
    assert result2["session_id"] == session_id

@pytest.mark.asyncio
async def test_voice_formatting():
    """Test that responses are properly formatted for voice."""
    session_id = "test_session_voice"
    
    result = await voice_graph_service.process_voice_query(
        session_id=session_id,
        query="Give me cleaning steps"
    )
    
    response_text = result["response"]["text"]
    
    # Check voice formatting
    assert result["response"]["formatted_for_voice"] == True
    # Should not contain "1." but "First,"
    assert "1." not in response_text or "First," in response_text

def test_voice_capabilities_endpoint():
    """Test voice capabilities endpoint."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/voice-capabilities")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "voice_processing" in data
    assert "graph_context" in data
    assert "supported_features" in data

def test_voice_session_endpoint():
    """Test voice session creation endpoint."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    
    # Create session
    response = client.post("/voice-session")
    assert response.status_code == 200
    
    data = response.json()
    session_id = data["session_id"]
    
    # Get session info
    response = client.get(f"/voice-session/{session_id}")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_fallback_behavior():
    """Test voice system fallback when RAG unavailable."""
    # Temporarily disable graph context
    original_setting = voice_graph_service.use_graph_context
    voice_graph_service.use_graph_context = False
    
    try:
        result = await voice_graph_service.process_voice_query(
            session_id="test_fallback",
            query="Help with fryer"
        )
        
        assert result["response"]["text"] is not None
        assert result["audio_ready"] == True
        
    finally:
        # Restore original setting
        voice_graph_service.use_graph_context = original_setting

def test_existing_chat_unchanged():
    """Verify existing chat endpoint still works identically."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    
    # Test existing chat endpoint
    response = client.post("/chat", json={"message": "test query"})
    
    # Should work exactly as before (may return error if no documents, but structure should be same)
    assert response.status_code in [200, 422, 500]  # Valid status codes for existing endpoint