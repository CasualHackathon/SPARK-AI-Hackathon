"""
LLM Response Caching - Cache LLM responses to avoid redundant API calls.
"""

import hashlib
import json
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from logging import getLogger

from spoon_ai.schema import Message
from spoon_ai.llm.interface import LLMResponse
from spoon_ai.llm.manager import LLMManager

logger = getLogger(__name__)


class LLMResponseCache:
    """Cache for LLM responses to avoid redundant API calls."""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """Initialize the cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
            max_size: Maximum number of cached entries (default: 1000)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
    
    def _generate_cache_key(self, messages: List[Message], provider: Optional[str] = None, **kwargs) -> str:
        """Generate a cache key from messages and parameters.
        
        Args:
            messages: List of conversation messages
            provider: Provider name (optional)
            **kwargs: Additional parameters
            
        Returns:
            str: Cache key hash
        """
        # Create a dictionary with all relevant parameters
        cache_data = {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name,
                }
                for msg in messages
            ],
            "provider": provider,
            "params": {k: v for k, v in kwargs.items() if k not in ['callbacks']}  # Exclude callbacks
        }
        
        # Convert to JSON string and hash
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def get(self, messages: List[Message], provider: Optional[str] = None, **kwargs) -> Optional[LLMResponse]:
        """Get cached response if available.
        
        Args:
            messages: List of conversation messages
            provider: Provider name (optional)
            **kwargs: Additional parameters
            
        Returns:
            Optional[LLMResponse]: Cached response if found and not expired, None otherwise
        """
        cache_key = self._generate_cache_key(messages, provider, **kwargs)
        
        if cache_key not in self.cache:
            return None
        
        entry = self.cache[cache_key]
        
        # Check if entry has expired
        if datetime.now() > entry['expires_at']:
            del self.cache[cache_key]
            logger.debug(f"Cache entry expired for key: {cache_key[:8]}...")
            return None
        
        logger.debug(f"Cache hit for key: {cache_key[:8]}...")
        return entry['response']
    
    def set(self, messages: List[Message], response: LLMResponse, 
            provider: Optional[str] = None, ttl: Optional[int] = None, **kwargs) -> None:
        """Store response in cache.
        
        Args:
            messages: List of conversation messages
            response: LLM response to cache
            provider: Provider name (optional)
            ttl: Time-to-live in seconds (optional, uses default if not provided)
            **kwargs: Additional parameters
        """
        # Enforce max size by removing oldest entries if needed
        if len(self.cache) >= self.max_size:
            # Remove oldest entries (by expiration time)
            sorted_entries = sorted(self.cache.items(), key=lambda x: x[1]['expires_at'])
            entries_to_remove = len(self.cache) - self.max_size + 1
            for key, _ in sorted_entries[:entries_to_remove]:
                del self.cache[key]
            logger.debug(f"Cache size limit reached, removed {entries_to_remove} oldest entries")
        
        cache_key = self._generate_cache_key(messages, provider, **kwargs)
        expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
        
        self.cache[cache_key] = {
            'response': response,
            'expires_at': expires_at,
            'cached_at': datetime.now()
        }
        
        logger.debug(f"Cached response for key: {cache_key[:8]}... (expires at {expires_at})")
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics including size, max_size, etc.
        """
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'default_ttl': self.default_ttl
        }


class CachedLLMManager:
    """Wrapper around LLMManager that adds response caching."""
    
    def __init__(self, llm_manager: LLMManager, cache: Optional[LLMResponseCache] = None):
        """Initialize cached LLM manager.
        
        Args:
            llm_manager: The underlying LLMManager instance
            cache: Optional cache instance (creates new one if not provided)
        """
        self.llm_manager = llm_manager
        self.cache = cache or LLMResponseCache()
    
    async def chat(self, messages: List[Message], provider: Optional[str] = None, 
                   use_cache: bool = True, cache_ttl: Optional[int] = None, **kwargs) -> LLMResponse:
        """Send chat request with caching support.
        
        Args:
            messages: List of conversation messages
            provider: Specific provider to use (optional)
            use_cache: Whether to use cache (default: True)
            cache_ttl: Custom TTL for this request (optional)
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse: LLM response (from cache or API)
        """
        # Try to get from cache first
        if use_cache:
            cached_response = self.cache.get(messages, provider, **kwargs)
            if cached_response is not None:
                logger.info("Returning cached response")
                return cached_response
        
        # If not in cache, make API call
        response = await self.llm_manager.chat(messages, provider=provider, **kwargs)
        
        # Store in cache
        if use_cache:
            self.cache.set(messages, response, provider, ttl=cache_ttl, **kwargs)
        
        return response
    
    async def chat_stream(self, messages: List[Message], provider: Optional[str] = None, 
                         callbacks: Optional[List] = None, **kwargs):
        """Send streaming chat request (caching not supported for streaming).
        
        Args:
            messages: List of conversation messages
            provider: Specific provider to use (optional)
            callbacks: Optional callback handlers
            **kwargs: Additional parameters
            
        Yields:
            LLMResponseChunk: Streaming response chunks
        """
        # Streaming responses cannot be cached, so just delegate to manager
        async for chunk in self.llm_manager.chat_stream(messages, provider=provider, 
                                                         callbacks=callbacks, **kwargs):
            yield chunk
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        return self.cache.get_stats()
