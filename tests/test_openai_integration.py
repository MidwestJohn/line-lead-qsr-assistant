"""Tests for OpenAI integration module."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from openai_integration import QSRAssistant


class TestQSRAssistant:
    """Test cases for QSRAssistant class."""

    def test_initialization(self):
        """Test QSRAssistant initializes correctly."""
        assistant = QSRAssistant()
        assert assistant.model == "gpt-4"
        assert assistant.temperature == 0.2
        assert assistant.max_tokens == 500

    def test_create_system_prompt(self):
        """Test system prompt creation."""
        assistant = QSRAssistant()
        prompt = assistant.create_system_prompt()
        
        assert "Lina" in prompt
        assert "friendly" in prompt
        assert "simple" in prompt.lower()
        assert "Good question!" in prompt

    def test_format_context_with_chunks(self):
        """Test context formatting with document chunks."""
        assistant = QSRAssistant()
        
        chunks = [
            {
                'text': 'Turn off the fryer and let it cool down.',
                'metadata': {'filename': 'manual.pdf'},
                'similarity': 0.8
            }
        ]
        
        context = assistant.format_context(chunks)
        
        assert "training" in context.lower()
        assert "turn off" in context.lower()
        assert not "MANUAL CONTEXT" in context  # Should not have corporate formatting

    def test_format_context_empty(self):
        """Test context formatting with no chunks."""
        assistant = QSRAssistant()
        context = assistant.format_context([])
        
        assert "don't have specific info" in context

    def test_simplify_manual_text(self):
        """Test manual text simplification."""
        assistant = QSRAssistant()
        
        formal_text = "Personnel must utilize proper equipment maintenance protocols"
        simplified = assistant._simplify_manual_text(formal_text)
        
        assert "workers" in simplified
        assert "use" in simplified
        assert "utilize" not in simplified
        assert "protocols" not in simplified

    @pytest.mark.asyncio
    async def test_generate_response_demo_mode(self):
        """Test response generation in demo mode."""
        with patch.object(QSRAssistant, '__init__', lambda x: None):
            assistant = QSRAssistant()
            assistant.demo_mode = True
            assistant.client = None
            
            chunks = [{'text': 'test', 'metadata': {'filename': 'test.pdf'}, 'similarity': 0.5}]
            
            result = await assistant.generate_response("test question", chunks)
            
            assert result['type'] == 'ai_powered_demo'
            assert 'response' in result

    def test_is_available_with_client(self):
        """Test availability check with valid client."""
        assistant = QSRAssistant()
        assistant.client = Mock()
        assistant.demo_mode = False
        
        assert assistant.is_available() is True

    def test_is_available_demo_mode(self):
        """Test availability check in demo mode."""
        assistant = QSRAssistant()
        assistant.client = None
        assistant.demo_mode = True
        
        assert assistant.is_available() is True

    def test_is_not_available(self):
        """Test availability check when not available."""
        assistant = QSRAssistant()
        assistant.client = None
        assistant.demo_mode = False
        
        assert assistant.is_available() is False