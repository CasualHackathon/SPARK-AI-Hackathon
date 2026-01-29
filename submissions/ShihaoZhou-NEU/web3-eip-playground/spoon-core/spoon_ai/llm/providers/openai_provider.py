"""
OpenAI Provider implementation for the unified LLM interface.
"""

from typing import Dict, Any
from logging import getLogger

from ..interface import ProviderMetadata, ProviderCapability
from ..registry import register_provider
from .openai_compatible_provider import OpenAICompatibleProvider

logger = getLogger(__name__)


@register_provider("openai", [
    ProviderCapability.CHAT,
    ProviderCapability.COMPLETION,
    ProviderCapability.TOOLS,
    ProviderCapability.STREAMING
])
class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI provider implementation."""
    
    def __init__(self):
        super().__init__()
        self.provider_name = "openai"
        self.default_base_url = "https://api.openai.com/v1"
        self.default_model = "gpt-4.1"
    
    def get_metadata(self) -> ProviderMetadata:
        """Get OpenAI provider metadata."""
        return ProviderMetadata(
            name="openai",
            version="1.0.0",
            capabilities=[
                ProviderCapability.CHAT,
                ProviderCapability.COMPLETION,
                ProviderCapability.TOOLS,
                ProviderCapability.STREAMING
            ],
            max_tokens=128000,  # GPT-4 context limit
            supports_system_messages=True,
            rate_limits={
                "requests_per_minute": 3500,
                "tokens_per_minute": 90000
            }
        )