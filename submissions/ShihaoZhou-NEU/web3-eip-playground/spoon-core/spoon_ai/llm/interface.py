"""
LLM Provider Interface - Abstract base class defining the unified interface for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from spoon_ai.schema import Message, ToolCall, LLMResponseChunk
from spoon_ai.callbacks.base import BaseCallbackHandler


class ProviderCapability(Enum):
    """Enumeration of capabilities that LLM providers can support."""
    CHAT = "chat"
    COMPLETION = "completion"
    TOOLS = "tools"
    STREAMING = "streaming"
    IMAGE_GENERATION = "image_generation"
    VISION = "vision"


@dataclass
class ProviderMetadata:
    """Metadata describing a provider's capabilities and limits."""
    name: str
    version: str
    capabilities: List[ProviderCapability]
    max_tokens: int
    supports_system_messages: bool
    rate_limits: Dict[str, int] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Enhanced LLM response with comprehensive metadata and debugging information."""
    content: str
    provider: str
    model: str
    finish_reason: str
    native_finish_reason: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class LLMProviderInterface(ABC):
    """Abstract base class defining the unified interface for all LLM providers."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Send chat request to the provider.

        Args:
            messages: List of conversation messages
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse: Standardized response object
            
        Raises:
            ProviderError: If the request fails
        """
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: List[Message],callbacks: Optional[List[BaseCallbackHandler]] = None, **kwargs) -> AsyncIterator[LLMResponseChunk]:
        """Send streaming chat request to the provider with callback support.
        
        Args:
            messages: List of conversation messages
            callbacks: Optional list of callback handlers for real-time events
            **kwargs: Additional provider-specific parameters
            
        Yields:
            LLMResponseChunk: Structured streaming response chunks
            
        Raises:
            ProviderError: If the request fails
        """
        pass
    
    @abstractmethod
    async def completion(self, prompt: str, **kwargs) -> LLMResponse:
        """Send completion request to the provider.
        
        Args:
            prompt: Text prompt for completion
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse: Standardized response object
            
        Raises:
            ProviderError: If the request fails
        """
        pass
    
    @abstractmethod
    async def chat_with_tools(self, messages: List[Message], tools: List[Dict], **kwargs) -> LLMResponse:
        """Send chat request with tool support.

        Args:
            messages: List of conversation messages
            tools: List of available tools
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse: Standardized response object with potential tool calls
            
        Raises:
            ProviderError: If the request fails
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> ProviderMetadata:
        """Get provider metadata and capabilities.

        Returns:
            ProviderMetadata: Provider information and capabilities
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and available.

        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources and connections.
        
        This method should be called when the provider is no longer needed.
        """
        pass