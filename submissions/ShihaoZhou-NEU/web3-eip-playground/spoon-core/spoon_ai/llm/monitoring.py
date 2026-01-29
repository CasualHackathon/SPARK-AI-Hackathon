"""
Comprehensive monitoring, debugging, and metrics collection for LLM operations.
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from logging import getLogger
import json

from .interface import LLMResponse
from .errors import LLMError

logger = getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single LLM request."""
    request_id: str
    provider: str
    method: str
    model: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    success: bool = False
    error: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderStats:
    """Aggregated statistics for a provider."""
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration: float = 0.0
    average_duration: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    error_rate: float = 0.0
    last_request: Optional[datetime] = None
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def get(self, key: str, default=None):
        """Get attribute value with default fallback for dictionary-like access.
        
        Args:
            key: Attribute name
            default: Default value if attribute doesn't exist
            
        Returns:
            Attribute value or default
        """
        return getattr(self, key, default)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    @property
    def avg_response_time(self) -> float:
        """Get average response time."""
        return self.average_duration


class DebugLogger:
    """Comprehensive logging and debugging system for LLM operations."""
    
    def __init__(self, max_history: int = 1000, enable_detailed_logging: bool = True):
        """Initialize debug logger.
        
        Args:
            max_history: Maximum number of requests to keep in history
            enable_detailed_logging: Whether to enable detailed request/response logging
        """
        self.max_history = max_history
        self.enable_detailed_logging = enable_detailed_logging
        self.request_history: deque = deque(maxlen=max_history)
        self.active_requests: Dict[str, RequestMetrics] = {}
    
    def log_request(self, provider: str, method: str, params: Dict[str, Any]) -> str:
        """Log request with unique ID.
        
        Args:
            provider: Provider name
            method: Method being called (chat, completion, etc.)
            params: Request parameters
            
        Returns:
            str: Unique request ID
        """
        request_id = str(uuid.uuid4())
        
        # Create request metrics
        metrics = RequestMetrics(
            request_id=request_id,
            provider=provider,
            method=method,
            model=params.get('model', 'unknown'),
            start_time=datetime.now(),
            metadata={'params': params if self.enable_detailed_logging else {}}
        )
        
        self.active_requests[request_id] = metrics
        
        if self.enable_detailed_logging:
            logger.debug(f"[{request_id}] {provider}.{method} started", extra={
                'request_id': request_id,
                'provider': provider,
                'method': method,
                'params': params
            })
        else:
            logger.info(f"[{request_id}] {provider}.{method} started")
        
        return request_id
    
    def log_response(self, request_id: str, response: LLMResponse, duration: float) -> None:
        """Log response with timing information.
        
        Args:
            request_id: Request ID from log_request
            response: LLM response object
            duration: Request duration in seconds
        """
        if request_id not in self.active_requests:
            logger.warning(f"Response logged for unknown request ID: {request_id}")
            return
        
        metrics = self.active_requests[request_id]
        metrics.end_time = datetime.now()
        metrics.duration = duration
        metrics.success = True
        
        # Extract token usage if available
        if response.usage:
            metrics.input_tokens = response.usage.get('prompt_tokens', 0)
            metrics.output_tokens = response.usage.get('completion_tokens', 0)
            metrics.total_tokens = response.usage.get('total_tokens', 0)
        
        # Store response metadata
        if self.enable_detailed_logging:
            metrics.metadata.update({
                'response': {
                    'content_length': len(response.content),
                    'finish_reason': response.finish_reason,
                    'tool_calls_count': len(response.tool_calls),
                    'metadata': response.metadata
                }
            })
        
        # Move to history
        self.request_history.append(metrics)
        del self.active_requests[request_id]
        
        if self.enable_detailed_logging:
            logger.debug(f"[{request_id}] {metrics.provider}.{metrics.method} completed in {duration:.3f}s", extra={
                'request_id': request_id,
                'provider': metrics.provider,
                'method': metrics.method,
                'duration': duration,
                'tokens': metrics.total_tokens,
                'success': True
            })
        else:
            logger.info(f"[{request_id}] {metrics.provider}.{metrics.method} completed in {duration:.3f}s")
    
    def log_error(self, request_id: str, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with context.
        
        Args:
            request_id: Request ID from log_request
            error: Exception that occurred
            context: Additional error context
        """
        if request_id not in self.active_requests:
            logger.warning(f"Error logged for unknown request ID: {request_id}")
            return
        
        metrics = self.active_requests[request_id]
        metrics.end_time = datetime.now()
        metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.success = False
        metrics.error = str(error)
        metrics.metadata.update({'error_context': context})
        
        # Move to history
        self.request_history.append(metrics)
        del self.active_requests[request_id]
        
        logger.error(f"[{request_id}] {metrics.provider}.{metrics.method} failed: {error}", extra={
            'request_id': request_id,
            'provider': metrics.provider,
            'method': metrics.method,
            'error': str(error),
            'context': context,
            'duration': metrics.duration
        })
    
    def log_fallback(self, from_provider: str, to_provider: str, reason: str) -> None:
        """Log provider fallback event.
        
        Args:
            from_provider: Provider that failed
            to_provider: Provider being used as fallback
            reason: Reason for fallback
        """
        logger.warning(f"Fallback from {from_provider} to {to_provider}: {reason}", extra={
            'from_provider': from_provider,
            'to_provider': to_provider,
            'reason': reason,
            'event_type': 'fallback'
        })
    
    def get_request_history(self, provider: Optional[str] = None, limit: Optional[int] = None) -> List[RequestMetrics]:
        """Get request history.
        
        Args:
            provider: Filter by provider (optional)
            limit: Maximum number of requests to return (optional)
            
        Returns:
            List[RequestMetrics]: List of request metrics
        """
        history = list(self.request_history)
        
        if provider:
            history = [r for r in history if r.provider == provider]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_active_requests(self) -> List[RequestMetrics]:
        """Get currently active requests.
        
        Returns:
            List[RequestMetrics]: List of active request metrics
        """
        return list(self.active_requests.values())
    
    def clear_history(self) -> None:
        """Clear request history."""
        self.request_history.clear()
        logger.info("Request history cleared")


class MetricsCollector:
    """Collects and aggregates performance metrics for LLM providers."""
    
    def __init__(self, window_size: int = 3600):
        """Initialize metrics collector.
        
        Args:
            window_size: Time window in seconds for rolling metrics
        """
        self.window_size = window_size
        self.provider_stats: Dict[str, ProviderStats] = {}
        self.rolling_metrics: deque = deque()
        self._cost_per_token = {
            'openai': {'gpt-4.1': 0.00003, 'gpt-3.5-turbo': 0.000002},
            'anthropic': {'claude-3-sonnet': 0.000015, 'claude-3-haiku': 0.000001},
            'gemini': {'gemini-2.5-pro': 0.000001}
        }
    
    def record_request(self, provider: str, method: str, duration: float, success: bool, 
                      tokens: int = 0, model: str = '', error: Optional[str] = None) -> None:
        """Record request metrics.
        
        Args:
            provider: Provider name
            method: Method called
            duration: Request duration in seconds
            success: Whether request was successful
            tokens: Number of tokens used
            model: Model name
            error: Error message if failed
        """
        # Initialize provider stats if needed
        if provider not in self.provider_stats:
            self.provider_stats[provider] = ProviderStats(provider=provider)
        
        stats = self.provider_stats[provider]
        
        # Update counters
        stats.total_requests += 1
        if success:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1
            if error:
                stats.errors[error] += 1
        
        # Update timing
        stats.total_duration += duration
        stats.average_duration = stats.total_duration / stats.total_requests
        stats.last_request = datetime.now()
        
        # Update tokens and cost
        stats.total_tokens += tokens
        if model and tokens > 0:
            cost = self._calculate_cost(provider, model, tokens)
            stats.total_cost += cost
        
        # Update error rate
        stats.error_rate = stats.failed_requests / stats.total_requests
        
        # Add to rolling metrics
        self.rolling_metrics.append({
            'timestamp': datetime.now(),
            'provider': provider,
            'method': method,
            'duration': duration,
            'success': success,
            'tokens': tokens,
            'model': model,
            'error': error
        })
        
        # Clean old metrics
        self._clean_old_metrics()
    
    def _calculate_cost(self, provider: str, model: str, tokens: int) -> float:
        """Calculate cost for token usage.
        
        Args:
            provider: Provider name
            model: Model name
            tokens: Number of tokens
            
        Returns:
            float: Estimated cost in USD
        """
        if provider in self._cost_per_token and model in self._cost_per_token[provider]:
            return tokens * self._cost_per_token[provider][model]
        return 0.0
    
    def _clean_old_metrics(self) -> None:
        """Remove metrics older than window_size."""
        cutoff = datetime.now() - timedelta(seconds=self.window_size)
        while self.rolling_metrics and self.rolling_metrics[0]['timestamp'] < cutoff:
            self.rolling_metrics.popleft()
    
    def get_provider_stats(self, provider: str) -> Optional[ProviderStats]:
        """Get statistics for a specific provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Optional[ProviderStats]: Provider statistics or None if not found
        """
        return self.provider_stats.get(provider)
    
    def get_all_stats(self) -> Dict[str, ProviderStats]:
        """Get statistics for all providers.
        
        Returns:
            Dict[str, ProviderStats]: Dictionary of provider statistics
        """
        return self.provider_stats.copy()
    
    def get_rolling_metrics(self, provider: Optional[str] = None, 
                           method: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get rolling metrics with optional filtering.
        
        Args:
            provider: Filter by provider (optional)
            method: Filter by method (optional)
            
        Returns:
            List[Dict[str, Any]]: List of metrics
        """
        self._clean_old_metrics()
        
        metrics = list(self.rolling_metrics)
        
        if provider:
            metrics = [m for m in metrics if m['provider'] == provider]
        
        if method:
            metrics = [m for m in metrics if m['method'] == method]
        
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall summary statistics.
        
        Returns:
            Dict[str, Any]: Summary statistics
        """
        total_requests = sum(stats.total_requests for stats in self.provider_stats.values())
        total_successful = sum(stats.successful_requests for stats in self.provider_stats.values())
        total_failed = sum(stats.failed_requests for stats in self.provider_stats.values())
        total_tokens = sum(stats.total_tokens for stats in self.provider_stats.values())
        total_cost = sum(stats.total_cost for stats in self.provider_stats.values())
        
        return {
            'total_requests': total_requests,
            'successful_requests': total_successful,
            'failed_requests': total_failed,
            'overall_success_rate': total_successful / total_requests if total_requests > 0 else 0,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'active_providers': len(self.provider_stats),
            'window_size_seconds': self.window_size,
            'metrics_count': len(self.rolling_metrics)
        }
    
    def reset_stats(self, provider: Optional[str] = None) -> None:
        """Reset statistics.
        
        Args:
            provider: Reset specific provider only (optional)
        """
        if provider:
            if provider in self.provider_stats:
                del self.provider_stats[provider]
                logger.info(f"Reset statistics for provider: {provider}")
        else:
            self.provider_stats.clear()
            self.rolling_metrics.clear()
            logger.info("Reset all statistics")


# Global instances for convenience
_global_debug_logger = DebugLogger()
_global_metrics_collector = MetricsCollector()


def get_debug_logger() -> DebugLogger:
    """Get global debug logger instance.
    
    Returns:
        DebugLogger: Global debug logger
    """
    return _global_debug_logger


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance.
    
    Returns:
        MetricsCollector: Global metrics collector
    """
    return _global_metrics_collector