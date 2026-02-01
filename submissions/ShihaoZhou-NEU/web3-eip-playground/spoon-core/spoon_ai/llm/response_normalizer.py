"""
Response normalizer for ensuring consistent response formats across providers.
"""

from typing import Dict, Any, List, Optional
from logging import getLogger

from .interface import LLMResponse, ProviderCapability
from .errors import ValidationError

logger = getLogger(__name__)


class ResponseNormalizer:
    """Normalizes responses from different providers to ensure consistency."""
    
    def __init__(self):
        self.provider_mappings = {
            'openai': self._normalize_openai_response,
            'anthropic': self._normalize_anthropic_response,
            'gemini': self._normalize_gemini_response
        }
    
    def normalize_response(self, response: LLMResponse) -> LLMResponse:
        """Normalize a response from any provider.
        
        Args:
            response: Raw LLM response
            
        Returns:
            LLMResponse: Normalized response
            
        Raises:
            ValidationError: If response cannot be normalized
        """
        try:
            # Get provider-specific normalizer
            normalizer = self.provider_mappings.get(response.provider)
            
            if normalizer:
                return normalizer(response)
            else:
                # Generic normalization for unknown providers
                return self._normalize_generic_response(response)
                
        except Exception as e:
            raise ValidationError(
                f"Failed to normalize response from {response.provider}: {str(e)}",
                context={"provider": response.provider, "response": response}
            )
    
    def _normalize_openai_response(self, response: LLMResponse) -> LLMResponse:
        """Normalize OpenAI-specific response."""
        # OpenAI responses are already well-structured
        # Just ensure required fields are present
        
        if not response.content:
            response.content = ""
        
        # Ensure finish_reason is standardized
        if response.finish_reason not in ['stop', 'length', 'tool_calls', 'content_filter']:
            logger.warning(f"Unknown finish_reason from OpenAI: {response.finish_reason}")
            response.finish_reason = 'stop'
        
        # Ensure metadata is present
        if not response.metadata:
            response.metadata = {}
        
        return response
    
    def _normalize_anthropic_response(self, response: LLMResponse) -> LLMResponse:
        """Normalize Anthropic-specific response."""
        # Ensure content is present
        if not response.content:
            response.content = ""
        
        # Normalize finish_reason mapping
        finish_reason_mapping = {
            'end_turn': 'stop',
            'max_tokens': 'length',
            'tool_use': 'tool_calls',
            'stop_sequence': 'stop'
        }
        
        if response.finish_reason in finish_reason_mapping:
            response.finish_reason = finish_reason_mapping[response.finish_reason]
        elif response.finish_reason not in ['stop', 'length', 'tool_calls', 'content_filter']:
            logger.warning(f"Unknown finish_reason from Anthropic: {response.finish_reason}")
            response.finish_reason = 'stop'
        
        # Ensure metadata includes cache metrics if available
        if not response.metadata:
            response.metadata = {}
        
        return response
    
    def _normalize_gemini_response(self, response: LLMResponse) -> LLMResponse:
        """Normalize Gemini-specific response."""
        # Ensure content is present
        if not response.content:
            response.content = ""
        
        # Clean JSON responses: Gemini sometimes returns JSON wrapped in markdown code blocks.
        # Remove markdown code block markers to make JSON parsing easier for users.
        if response.content:
            import re
            content = response.content.strip()
            
            # Remove markdown code block markers if present (common when LLM returns JSON)
            content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
            content = content.strip()
            
            response.content = content
        
        # Gemini doesn't provide detailed finish reasons, default to 'stop'
        if not response.finish_reason:
            response.finish_reason = 'stop'
        
        # Ensure metadata is present
        if not response.metadata:
            response.metadata = {}
        
        # Handle image-specific metadata
        if 'image_paths' in response.metadata:
            response.metadata['has_multimodal_content'] = True
        
        return response
    
    def _normalize_generic_response(self, response: LLMResponse) -> LLMResponse:
        """Generic normalization for unknown providers."""
        # Ensure basic fields are present
        if not response.content:
            response.content = ""
        
        if not response.finish_reason:
            response.finish_reason = 'stop'
        
        if not response.metadata:
            response.metadata = {}
        
        # Standardize finish_reason if it's not already standard
        if response.finish_reason not in ['stop', 'length', 'tool_calls', 'content_filter']:
            logger.warning(f"Unknown finish_reason from {response.provider}: {response.finish_reason}")
            response.finish_reason = 'stop'
        
        return response
    
    def validate_response(self, response: LLMResponse) -> bool:
        """Validate that a response meets minimum requirements.
        
        Args:
            response: Response to validate
            
        Returns:
            bool: True if response is valid
            
        Raises:
            ValidationError: If response is invalid
        """
        errors = []
        
        # Check required fields
        if not hasattr(response, 'content'):
            errors.append("Missing 'content' field")
        
        if not hasattr(response, 'provider') or not response.provider:
            errors.append("Missing or empty 'provider' field")
        
        if not hasattr(response, 'model') or not response.model:
            errors.append("Missing or empty 'model' field")
        
        if not hasattr(response, 'finish_reason') or not response.finish_reason:
            errors.append("Missing or empty 'finish_reason' field")
        
        # Check finish_reason is valid
        valid_finish_reasons = ['stop', 'length', 'tool_calls', 'content_filter']
        if hasattr(response, 'finish_reason') and response.finish_reason not in valid_finish_reasons:
            errors.append(f"Invalid finish_reason: {response.finish_reason}. Must be one of {valid_finish_reasons}")
        
        # Check tool_calls format if present
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for i, tool_call in enumerate(response.tool_calls):
                if not hasattr(tool_call, 'id') or not tool_call.id:
                    errors.append(f"Tool call {i} missing 'id' field")
                if not hasattr(tool_call, 'type') or not tool_call.type:
                    errors.append(f"Tool call {i} missing 'type' field")
                if hasattr(tool_call, 'function'):
                    if not hasattr(tool_call.function, 'name') or not tool_call.function.name:
                        errors.append(f"Tool call {i} function missing 'name' field")
        
        # Check usage format if present
        if hasattr(response, 'usage') and response.usage:
            required_usage_fields = ['prompt_tokens', 'completion_tokens', 'total_tokens']
            for field in required_usage_fields:
                if field not in response.usage:
                    errors.append(f"Usage missing '{field}' field")
                elif not isinstance(response.usage[field], int) or response.usage[field] < 0:
                    errors.append(f"Usage '{field}' must be a non-negative integer")
        
        if errors:
            raise ValidationError(
                f"Response validation failed: {'; '.join(errors)}",
                context={"provider": response.provider, "errors": errors}
            )
        
        return True
    
    def add_provider_mapping(self, provider_name: str, normalizer_func) -> None:
        """Add a custom normalizer for a new provider.
        
        Args:
            provider_name: Name of the provider
            normalizer_func: Function that takes and returns LLMResponse
        """
        self.provider_mappings[provider_name] = normalizer_func
        logger.info(f"Added custom normalizer for provider: {provider_name}")
    
    def get_supported_providers(self) -> List[str]:
        """Get list of providers with custom normalizers.
        
        Returns:
            List[str]: List of provider names
        """
        return list(self.provider_mappings.keys())


# Global instance for convenience
_global_normalizer = ResponseNormalizer()


def get_response_normalizer() -> ResponseNormalizer:
    """Get global response normalizer instance.
    
    Returns:
        ResponseNormalizer: Global normalizer instance
    """
    return _global_normalizer