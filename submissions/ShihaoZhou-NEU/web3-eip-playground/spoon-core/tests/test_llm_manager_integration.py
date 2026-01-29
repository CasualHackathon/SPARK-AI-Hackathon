"""
Integration tests for LLM Manager and related components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from spoon_ai.llm.manager import LLMManager, FallbackStrategy, LoadBalancer
from spoon_ai.llm.registry import LLMProviderRegistry
from spoon_ai.llm.config import ConfigurationManager
from spoon_ai.llm.monitoring import DebugLogger, MetricsCollector
from spoon_ai.llm.response_normalizer import ResponseNormalizer
from spoon_ai.llm.interface import LLMProviderInterface, LLMResponse, ProviderCapability
from spoon_ai.llm.errors import ProviderError, ConfigurationError
from spoon_ai.schema import Message
from spoon_ai.utils.config_manager import ConfigManager as EnvConfigManager


class MockProvider(LLMProviderInterface):
    """Mock provider for testing."""
    
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.initialized = False
    
    async def initialize(self, config: dict) -> None:
        self.initialized = True
    
    async def chat(self, messages: list, **kwargs) -> LLMResponse:
        if self.should_fail:
            raise ProviderError(self.name, "Mock provider failure")
        
        return LLMResponse(
            content=f"Response from {self.name}",
            provider=self.name,
            model="mock-model",
            finish_reason="stop",
            native_finish_reason="stop"
        )
    
    async def chat_stream(self, messages: list, **kwargs):
        if self.should_fail:
            raise ProviderError(self.name, "Mock provider failure")
        
        for chunk in [f"Chunk from {self.name}"]:
            yield chunk
    
    async def completion(self, prompt: str, **kwargs) -> LLMResponse:
        if self.should_fail:
            raise ProviderError(self.name, "Mock provider failure")
        
        return LLMResponse(
            content=f"Completion from {self.name}",
            provider=self.name,
            model="mock-model",
            finish_reason="stop",
            native_finish_reason="stop"
        )
    
    async def chat_with_tools(self, messages: list, tools: list, **kwargs) -> LLMResponse:
        if self.should_fail:
            raise ProviderError(self.name, "Mock provider failure")
        
        return LLMResponse(
            content=f"Tool response from {self.name}",
            provider=self.name,
            model="mock-model",
            finish_reason="tool_calls",
            native_finish_reason="tool_calls"
        )
    
    def get_metadata(self):
        from spoon_ai.llm.interface import ProviderMetadata
        return ProviderMetadata(
            name=self.name,
            version="1.0.0",
            capabilities=[ProviderCapability.CHAT, ProviderCapability.TOOLS],
            max_tokens=4096,
            supports_system_messages=True,
            rate_limits={}
        )
    
    async def health_check(self) -> bool:
        return not self.should_fail
    
    async def cleanup(self) -> None:
        pass


class TestLLMManagerIntegration:
    """Test LLM Manager integration."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager."""
        config_manager = Mock(spec=ConfigurationManager)
        config_manager.list_configured_providers.return_value = ["openai", "anthropic"]
        config_manager.get_default_provider.return_value = "openai"
        config_manager.get_fallback_chain.return_value = []
        config_manager.get_available_providers_by_priority.return_value = [
            "openai", "anthropic"
        ]
        config_manager.load_provider_config.return_value = Mock(model_dump=Mock(return_value={}))
        return config_manager
    
    @pytest.fixture
    def mock_registry(self):
        """Create mock registry with test providers."""
        registry = LLMProviderRegistry()
        
        # Register mock providers
        for provider in ["openai", "anthropic", "failing_provider", "gemini", "deepseek", "openrouter"]:
            registry.register(provider, MockProvider)

        # Pre-seed default instances
        registry._instances["openai"] = MockProvider("openai")
        registry._instances["anthropic"] = MockProvider("anthropic")
        
        return registry
    
    @pytest.fixture
    def llm_manager(self, mock_config_manager, mock_registry):
        """Create LLM Manager with mocked dependencies."""
        debug_logger = Mock(spec=DebugLogger)
        debug_logger.log_request.return_value = "request_123"
        debug_logger.log_response = Mock()
        debug_logger.log_error = Mock()
        
        metrics_collector = Mock(spec=MetricsCollector)
        metrics_collector.record_request = Mock()
        
        response_normalizer = Mock(spec=ResponseNormalizer)
        response_normalizer.normalize_response.side_effect = lambda x: x
        
        with patch('spoon_ai.llm.manager.asyncio.create_task'):
            manager = LLMManager(
                config_manager=mock_config_manager,
                debug_logger=debug_logger,
                metrics_collector=metrics_collector,
                response_normalizer=response_normalizer,
                registry=mock_registry
            )
        
        return manager
    
    @pytest.mark.asyncio
    async def test_chat_with_default_provider(self, llm_manager):
        """Test chat with default provider."""
        messages = [Message(role="user", content="Hello")]
        
        response = await llm_manager.chat(messages)
        
        assert response.content == "Response from openai"
        assert response.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_chat_with_specific_provider(self, llm_manager):
        """Test chat with specific provider."""
        messages = [Message(role="user", content="Hello")]
        
        response = await llm_manager.chat(messages, provider="anthropic")
        
        assert response.content == "Response from anthropic"
        assert response.provider == "anthropic"
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, llm_manager, mock_registry):
        """Test fallback mechanism when primary provider fails."""
        # Set up failing primary provider
        mock_registry._instances["openai"] = MockProvider("openai", should_fail=True)
        mock_registry._instances["anthropic"] = MockProvider("anthropic", should_fail=False)
        
        llm_manager.set_fallback_chain(["openai", "anthropic"])
        
        messages = [Message(role="user", content="Hello")]
        
        response = await llm_manager.chat(messages)
        
        # Should fallback to anthropic
        assert response.content == "Response from anthropic"
        assert response.provider == "anthropic"
    
    @pytest.mark.asyncio
    async def test_chat_with_tools(self, llm_manager):
        """Test chat with tools functionality."""
        messages = [Message(role="user", content="Use a tool")]
        tools = [{
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A test tool"
            }
        }]
        
        response = await llm_manager.chat_with_tools(messages, tools)
        
        assert response.content == "Tool response from openai"
        assert response.finish_reason == "tool_calls"
    
    @pytest.mark.asyncio
    async def test_health_check_all(self, llm_manager, mock_registry):
        """Test health check for all providers."""
        # Set up providers with different health states
        mock_registry._instances["openai"] = MockProvider("openai", should_fail=False)
        mock_registry._instances["anthropic"] = MockProvider("anthropic", should_fail=True)
        
        health_status = await llm_manager.health_check_all()
        
        assert health_status["openai"] is True
        assert health_status["anthropic"] is False
    
    @pytest.mark.asyncio
    async def test_load_balancing(self, llm_manager):
        """Test load balancing functionality."""
        llm_manager.enable_load_balancing("random")
        llm_manager.set_fallback_chain(["openai", "anthropic"])
        
        messages = [Message(role="user", content="Hello")]
        
        # Make multiple requests to test load balancing
        responses = []
        for _ in range(5):
            response = await llm_manager.chat(messages)
            responses.append(response.provider)
        
        # Should have used different providers (with some randomness)
        assert len(set(responses)) >= 1  # At least one provider used
    
    def test_set_fallback_chain(self, llm_manager):
        """Test setting fallback chain."""
        providers = ["openai", "anthropic"]
        llm_manager.set_fallback_chain(providers)

        assert llm_manager.fallback_chain == providers

    def test_default_provider_leads_fallback_chain(self, llm_manager):
        """Ensure default provider is always attempted before fallback chain."""
        llm_manager.set_fallback_chain(["gemini", "deepseek", "openrouter", "openai"])

        providers = llm_manager._get_providers_for_request(requested_provider=None)

        assert providers == ["openai", "gemini", "deepseek", "openrouter"]

    def test_automatic_fallback_when_chain_unset(self, llm_manager, mock_config_manager):
        """Auto-build fallback chain from available providers when env is unset."""
        llm_manager.fallback_chain = []
        mock_config_manager.get_available_providers_by_priority.return_value = [
            "openai", "anthropic", "gemini"
        ]
        llm_manager.registry._instances["gemini"] = MockProvider("gemini")

        providers = llm_manager._get_providers_for_request(requested_provider=None)

        assert providers == ["openai", "anthropic", "gemini"]
    
    def test_set_invalid_fallback_chain(self, llm_manager):
        """Test setting invalid fallback chain."""
        with pytest.raises(ConfigurationError):
            llm_manager.set_fallback_chain(["invalid_provider"])
    
    def test_enable_load_balancing(self, llm_manager):
        """Test enabling load balancing."""
        llm_manager.enable_load_balancing("weighted")
        
        assert llm_manager.load_balancing_enabled is True
        assert llm_manager.load_balancing_strategy == "weighted"
    
    def test_enable_invalid_load_balancing(self, llm_manager):
        """Test enabling invalid load balancing strategy."""
        with pytest.raises(ConfigurationError):
            llm_manager.enable_load_balancing("invalid_strategy")
    
    def test_get_stats(self, llm_manager):
        """Test getting manager statistics."""
        stats = llm_manager.get_stats()
        
        assert "manager" in stats
        assert "providers" in stats
        assert "summary" in stats
        assert stats["manager"]["default_provider"] == "openai"


class TestFallbackStrategy:
    """Test fallback strategy."""
    
    @pytest.fixture
    def debug_logger(self):
        """Create mock debug logger."""
        logger = Mock(spec=DebugLogger)
        logger.log_fallback = Mock()
        return logger
    
    @pytest.fixture
    def fallback_strategy(self, debug_logger):
        """Create fallback strategy."""
        return FallbackStrategy(debug_logger)
    
    @pytest.mark.asyncio
    async def test_successful_first_provider(self, fallback_strategy):
        """Test successful execution with first provider."""
        async def mock_operation(provider):
            return f"Success from {provider}"
        
        result = await fallback_strategy.execute_with_fallback(
            ["provider1", "provider2"], mock_operation
        )
        
        assert result == "Success from provider1"
    
    @pytest.mark.asyncio
    async def test_fallback_to_second_provider(self, fallback_strategy, debug_logger):
        """Test fallback to second provider."""
        call_count = 0
        
        async def mock_operation(provider):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First provider failed")
            return f"Success from {provider}"
        
        result = await fallback_strategy.execute_with_fallback(
            ["provider1", "provider2"], mock_operation
        )
        
        assert result == "Success from provider2"
        debug_logger.log_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self, fallback_strategy):
        """Test when all providers fail."""
        async def mock_operation(provider):
            raise Exception(f"{provider} failed")
        
        with pytest.raises(ProviderError):
            await fallback_strategy.execute_with_fallback(
                ["provider1", "provider2"], mock_operation
            )


class TestLoadBalancer:
    """Test load balancer."""
    
    @pytest.fixture
    def load_balancer(self):
        """Create load balancer."""
        return LoadBalancer()
    
    def test_round_robin_selection(self, load_balancer):
        """Test round-robin provider selection."""
        providers = ["provider1", "provider2", "provider3"]
        
        # Test multiple selections
        selections = []
        for _ in range(6):
            selection = load_balancer.select_provider(providers, "round_robin")
            selections.append(selection)
        
        # Should cycle through providers
        expected = ["provider1", "provider2", "provider3"] * 2
        assert selections == expected
    
    def test_random_selection(self, load_balancer):
        """Test random provider selection."""
        providers = ["provider1", "provider2", "provider3"]
        
        selections = []
        for _ in range(10):
            selection = load_balancer.select_provider(providers, "random")
            selections.append(selection)
        
        # Should only select from available providers
        assert all(s in providers for s in selections)
    
    def test_weighted_selection(self, load_balancer):
        """Test weighted provider selection."""
        providers = ["provider1", "provider2"]
        
        # Set weights
        load_balancer.set_provider_weight("provider1", 0.8)
        load_balancer.set_provider_weight("provider2", 0.2)
        
        selections = []
        for _ in range(100):
            selection = load_balancer.select_provider(providers, "weighted")
            selections.append(selection)
        
        # Provider1 should be selected more often (roughly 80% of the time)
        provider1_count = selections.count("provider1")
        assert provider1_count > 60  # Allow some variance
    
    def test_health_filtering(self, load_balancer):
        """Test filtering unhealthy providers."""
        providers = ["provider1", "provider2", "provider3"]
        
        # Mark provider2 as unhealthy
        load_balancer.update_provider_health("provider2", False)
        
        selections = []
        for _ in range(10):
            selection = load_balancer.select_provider(providers, "round_robin")
            selections.append(selection)
        
        # Should not select unhealthy provider
        assert "provider2" not in selections
        assert all(s in ["provider1", "provider3"] for s in selections)


class TestConfigurationPlaceholders:
    """Ensure placeholder values are surfaced as configuration errors."""

    def test_llm_configuration_rejects_placeholder_base_url(self, monkeypatch):
        """BASE_URL placeholders should raise a configuration error."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-real-openai-key")
        monkeypatch.setenv("BASE_URL", "your_base_url_here")
        monkeypatch.setattr("spoon_ai.llm.config.HAS_DOTENV", False, raising=False)

        config = ConfigurationManager()

        with pytest.raises(ConfigurationError):
            config.load_provider_config("openai")

    def test_env_config_manager_rejects_placeholder_base_url(self, monkeypatch):
        """Generic ConfigManager should not accept placeholder BASE_URL values."""
        monkeypatch.setenv("BASE_URL", "your_base_url_here")

        with pytest.raises(ValueError):
            EnvConfigManager()


if __name__ == "__main__":
    pytest.main([__file__])
