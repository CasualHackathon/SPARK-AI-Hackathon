import os
import re
from typing import Any, Dict, Optional

PLACEHOLDER_BASE_URL_VALUES = {
    "your_base_url_here",
    "your-base-url-here",
}


class ConfigManager:
    """Environment-based configuration helper for core usage."""

    def __init__(self) -> None:
        """Initialize manager with environment-backed cache."""
        self.config: Dict[str, Any] = {}
        self.refresh()

    def refresh(self) -> None:
        """Reload configuration snapshot from environment variables."""
        raw_base_url = os.getenv("BASE_URL", "")
        sanitized_base_url = raw_base_url.strip()
        if sanitized_base_url and sanitized_base_url.lower() in PLACEHOLDER_BASE_URL_VALUES:
            raise ValueError(
                "BASE_URL is set to the placeholder value 'your_base_url_here'. "
                "Remove the variable or provide a valid URL."
            )

        self.config = {
            "api_keys": self._load_api_keys(),
            "base_url": sanitized_base_url,
            "default_agent": os.getenv("DEFAULT_AGENT", "react"),
        }

    def _load_api_keys(self) -> Dict[str, str]:
        """Discover API keys from environment variables."""
        api_keys: Dict[str, str] = {}
        for env_key, value in os.environ.items():
            if env_key.endswith("_API_KEY") and value:
                provider = env_key[:-8].lower()
                api_keys[provider] = value
        return api_keys

    def _is_placeholder_value(self, value: str) -> bool:
        """
        Check if the given value is a placeholder API key.

        This method identifies common placeholder patterns used in configuration
        templates and documentation examples. It helps distinguish between actual
        API keys and placeholder values that should be replaced.
        """
        if not value or not isinstance(value, str):
            return True

        value_lower = value.lower().strip()
        if not value_lower:
            return True

        placeholder_patterns = [
            r"^sk-your-.*-key-here$",
            r"^sk-your-openai-api-key-here$",
            r"^sk-ant-your-.*-key-here$",
            r"^sk-ant-your-anthropic-api-key-here$",
            r"^your-.*-api-key-here$",
            r"^your-deepseek-api-key-here$",
            r"^your-api-key-here$",
            r"^insert-your-.*-key.*$",
            r"^your_api_key$",
            r"^api_key_here$",
            r"^your-.*-key$",
            r"^(api_key|your_key|insert_key|placeholder|example_key)$",
            r"^<.*>$",
            r"^\[.*\]$",
            r"^\{.*\}$",
        ]

        for pattern in placeholder_patterns:
            if re.match(pattern, value_lower):
                return True

        placeholder_keywords = [
            "placeholder",
            "example",
            "sample",
            "demo",
            "test",
            "your-key",
            "insert",
            "replace",
            "change-me",
        ]

        return any(keyword in value_lower for keyword in placeholder_keywords)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration item from environment snapshot."""
        self.refresh()
        keys = key.split(".")
        value: Any = self.config

        for part in keys:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                env_key = "_".join(keys).upper()
                env_value = os.getenv(env_key)
                if env_value and not self._is_placeholder_value(env_value):
                    return env_value
                return default

        if isinstance(value, str) and self._is_placeholder_value(value):
            return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration item by exporting to environment variables."""
        keys = key.split(".")
        if keys[0] == "api_keys":
            provider = keys[-1]
            os.environ[f"{provider.upper()}_API_KEY"] = str(value)
        else:
            env_key = "_".join(keys).upper()
            os.environ[env_key] = str(value)
        self.refresh()

    def list_config(self) -> Dict[str, Any]:
        """List configuration snapshot without persisting secrets."""
        self.refresh()
        return self.config.copy()

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider with environment priority."""
        self.refresh()
        env_key = f"{provider.upper()}_API_KEY"
        env_value = os.environ.get(env_key)
        if env_value and not self._is_placeholder_value(env_value):
            return env_value

        api_keys = self.config.get("api_keys", {})
        config_value = api_keys.get(provider)
        if config_value and not self._is_placeholder_value(config_value):
            return config_value

        return None

    def set_api_key(self, provider: str, api_key: str) -> None:
        """Set API key by exporting to environment variables."""
        os.environ[f"{provider.upper()}_API_KEY"] = api_key
        self.refresh()

    def get_model_name(self) -> Optional[str]:
        """Get model name override from environment."""
        self.refresh()
        return os.getenv("MODEL_NAME") or self.config.get("model_name")

    def get_base_url(self) -> Optional[str]:
        """Get base URL override from environment."""
        self.refresh()
        return os.getenv("BASE_URL") or self.config.get("base_url")

    def get_llm_provider(self) -> Optional[str]:
        """Determine LLM provider from environment variables."""
        self.refresh()

        explicit_provider = (
            os.getenv("LLM_PROVIDER")
            or os.getenv("DEFAULT_LLM_PROVIDER")
            or self.config.get("llm_provider")
        )
        if explicit_provider:
            return explicit_provider

        api_keys = self.config.get("api_keys", {})
        for provider in ["anthropic", "openai", "gemini", "deepseek"]:
            key_value = api_keys.get(provider)
            if key_value and not self._is_placeholder_value(key_value):
                return provider

        return None
