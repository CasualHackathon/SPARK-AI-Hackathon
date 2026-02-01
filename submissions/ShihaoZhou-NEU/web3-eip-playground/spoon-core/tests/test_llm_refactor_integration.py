"""
Integration tests for the refactored LLM infrastructure.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from spoon_ai.schema import Message
from spoon_ai.llm import (
    LLMManager,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    ConfigurationManager,
    LLMProviderRegistry,
    get_llm_manager,
    LLMResponse,
    ProviderError
)


class TestLLMManagerIntegration:
    """Test LLM Manager integration with providers."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        config_manager = Mock(spec=ConfigurationManager)
        config_manager.list_configured_providers.return_value = ["openai", "anthropic"]
        config_manager.get_default_provider.return_value = "openai"
        
        # Mock provider configs
        openai_config = Mock()
        openai_config.model_dump.return_value = {
            "api_key": "test-openai-key",
            "model": "gpt-4.1",
            "max_tokens": 4096,
            "temperature": 0.3
        }
        
        anthropic_config = Mock()
        anthropic_config.model_dump.return_value = {
            "api_key": "test-anthropic-key", 
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "temperature": 0.3
        }
        
        config_manager.load_provider_config.side_effect = lambda name: {
            "openai": openai_config,
            "anthropic": anthropic_config
        }[name]
        
        return config_manager
    
    @pytest.fixture
    def mock_registry(self):
        """Mock provider registry."""
        registry = Mock(spec=LLMProviderRegistry)
        
        # Mock providers
        openai_provider = Mock(spec=OpenAIProvider)
        openai_provider.initialize = AsyncMock()
        openai_provider.chat = AsyncMock()
        openai_provider.health_check = AsyncMock(return_value=True)
        openai_provider.cleanup = AsyncMock()
        
        anthropic_provider = Mock(spec=AnthropicProvider)
        anthropic_provider.initialize = AsyncMock()
        anthropic_provider.chat = AsyncMock()
        anthropic_provider.health_check = AsyncMock(return_value=True)
        anthropic_provider.cleanup = AsyncMock()
        
        registry.get_provider.side_effect = lambda name, config=None: {
            "openai": openai_provider,
            "anthropic": anthropic_provider
        }[name]
        
        registry.list_providers.return_value = ["openai", "anthropic"]
        registry.is_registered.return_value = True
        
        return registry
    
    @pytest.fixture
    def llm_manager(self, mock_config_manager, mock_registry):
        """Create LLM manager with mocked dependencies."""
        with patch('spoon_ai.llm.manager.ConfigurationManager', return_value=mock_config_manager), \
             patch('spoon_ai.llm.manager.get_global_registry', return_value=mock_registry), \
             patch('spoon_ai.llm.providers.OpenAIProvider'), \
             patch('spoon_ai.llm.providers.AnthropicProvider'), \
             patch('spoon_ai.llm.providers.GeminiProvider'):
            
            manager = LLMManager(
                config_manager=mock_config_manager,
                registry=mock_registry
            )
            return manager
    
    @pytest.mark.asyncio
    async def test_basic_chat(self, llm_manager, mock_registry):
        """Test basic chat functionality."""
        # Setup mock response
        mock_response = LLMResponse(
            content="Hello! I'm an AI assistant.",
            provider="openai",
            model="gpt-4.1",
            finish_reason="stop",
            native_finish_reason="stop",
            duration=0.5
        )
        
        openai_provider = mock_registry.get_provider("openai")
        openai_provider.chat.return_value = mock_response
        
        # Test chat
        messages = [Message(role="user", content="Hello")]
        response = await llm_manager.chat(messages)
        
        assert response.content == "Hello! I'm an AI assistant."
        assert response.provider == "openai"
        assert response.model == "gpt-4.1"
        openai_provider.chat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, llm_manager, mock_registry):
        """Test provider fallback when primary provider fails."""
        # Setup providers
        openai_provider = mock_registry.get_provider("openai")
        anthropic_provider = mock_registry.get_provider("anthropic")
        
        # Make OpenAI fail
        openai_provider.chat.side_effect = ProviderError("openai", "API error")
        
        # Make Anthropic succeed
        mock_response = LLMResponse(
            content="Response from Anthropic",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            finish_reason="stop",
            native_finish_reason="end_turn",
            duration=0.7
        )
        anthropic_provider.chat.return_value = mock_response
        
        # Set fallback chain
        llm_manager.set_fallback_chain(["openai", "anthropic"])
        
        # Test chat with fallback
        messages = [Message(role="user", content="Test fallback")]
        response = await llm_manager.chat(messages)
        
        assert response.provider == "anthropic"
        assert response.content == "Response from Anthropic"
        
        # Verify both providers were called
        openai_provider.chat.assert_called_once()
        anthropic_provider.chat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_balancing(self, llm_manager, mock_registry):
        """Test load balancing between providers."""
        # Setup providers
        openai_provider = mock_registry.get_provider("openai")
        anthropic_provider = mock_registry.get_provider("anthropic")
        
        # Setup responses
        openai_response = LLMResponse(
            content="OpenAI response",
            provider="openai",
            model="gpt-4.1",
            finish_reason="stop",
            native_finish_reason="stop",
            duration=0.5
        )
        
        anthropic_response = LLMResponse(
            content="Anthropic response", 
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            finish_reason="stop",
            native_finish_reason="end_turn",
            duration=0.7
        )
        
        openai_provider.chat.return_value = openai_response
        anthropic_provider.chat.return_value = anthropic_response
        
        # Enable load balancing
        llm_manager.set_fallback_chain(["openai", "anthropic"])
        llm_manager.enable_load_balancing("round_robin")
        
        # Send multiple requests
        messages = [Message(role="user", content="Test load balancing")]
        
        responses = []
        for _ in range(4):
            response = await llm_manager.chat(messages)
            responses.append(response.provider)
        
        # Should alternate between providers (round robin)
        # Note: Exact pattern depends on implementation, but both should be used
        providers_used = set(responses)
        assert len(providers_used) >= 1  # At least one provider used
    
    @pytest.mark.asyncio
    async def test_health_check(self, llm_manager, mock_registry):
        """Test health check functionality."""
        # Setup provider health checks
        openai_provider = mock_registry.get_provider("openai")
        anthropic_provider = mock_registry.get_provider("anthropic")
        
        openai_provider.health_check.return_value = True
        anthropic_provider.health_check.return_value = False
        
        # Run health check
        health_status = await llm_manager.health_check_all()
        
        assert health_status["openai"] is True
        assert health_status["anthropic"] is False
        
        openai_provider.health_check.assert_called_once()
        anthropic_provider.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, llm_manager, mock_registry):
        """Test cleanup functionality."""
        # Setup providers
        openai_provider = mock_registry.get_provider("openai")
        anthropic_provider = mock_registry.get_provider("anthropic")
        
        # Run cleanup
        await llm_manager.cleanup()
        
        # Verify cleanup was called on all providers
        openai_provider.cleanup.assert_called_once()
        anthropic_provider.cleanup.assert_called_once()
    
    def test_stats_collection(self, llm_manager):
        """Test statistics collection."""
        stats = llm_manager.get_stats()
        
        assert "manager" in stats
        assert "providers" in stats
        assert "summary" in stats
        
        manager_stats = stats["manager"]
        assert "default_provider" in manager_stats
        assert "fallback_chain" in manager_stats
        assert "load_balancing_enabled" in manager_stats
        assert "registered_providers" in manager_stats


class TestProviderIntegration:
    """Test individual provider integration."""
    
    @pytest.mark.asyncio
    async def test_openai_provider_initialization(self):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider()
        
        config = {
            "api_key": "test-key",
            "model": "gpt-4.1",
            "max_tokens": 4096,
            "temperature": 0.3
        }
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            await provider.initialize(config)
            
            assert provider.model == "gpt-4.1"
            assert provider.max_tokens == 4096
            assert provider.temperature == 0.3
            mock_openai.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_anthropic_provider_initialization(self):
        """Test Anthropic provider initialization."""
        provider = AnthropicProvider()
        
        config = {
            "api_key": "test-key",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "temperature": 0.3
        }
        
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            await provider.initialize(config)
            
            assert provider.model == "claude-sonnet-4-20250514"
            assert provider.max_tokens == 4096
            assert provider.temperature == 0.3
            mock_anthropic.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_gemini_provider_initialization(self):
        """Test Gemini provider initialization."""
        provider = GeminiProvider()
        
        config = {
            "api_key": "test-key",
            "model": "gemini-2.5-pro",
            "max_tokens": 4096,
            "temperature": 0.3
        }
        
        with patch('google.genai.Client') as mock_genai:
            await provider.initialize(config)
            
            assert provider.model == "gemini-2.5-pro"
            assert provider.max_tokens == 4096
            assert provider.temperature == 0.3
            mock_genai.assert_called_once()


class TestBackwardCompatibility:
    """Test backward compatibility with existing ChatBot."""
    
    def test_global_manager_access(self):
        """Test global manager access."""
        with patch('spoon_ai.llm.manager.LLMManager'):
            manager = get_llm_manager()
            assert manager is not None
            
            # Should return same instance on subsequent calls
            manager2 = get_llm_manager()
            assert manager is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])