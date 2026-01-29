"""Utility classes for intelligent MCP tool discovery and configuration.

Core graph components no longer hard-code external tools; instead, user code
registers tool specifications and optional transport/configuration details via
these helpers.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional

from spoon_ai.tools.mcp_tool import MCPTool


@dataclass
class MCPToolSpec:
    """Specification describing a desired MCP tool."""

    name: str
    server: Optional[str] = None
    capability: Optional[str] = None
    preferred: bool = True


class MCPConfigManager:
    """Centralised configuration loader for MCP tools."""

    def __init__(self) -> None:
        self._explicit_configs: Dict[str, Dict[str, object]] = {}
        self._lock = threading.Lock()

    def register_config(self, tool_name: str, config: Dict[str, object]) -> None:
        with self._lock:
            self._explicit_configs[tool_name] = dict(config)

    def get_config(self, tool_name: str) -> Dict[str, object]:
        with self._lock:
            if tool_name in self._explicit_configs:
                return dict(self._explicit_configs[tool_name])

        safe_tool_name = tool_name.upper().replace("-", "_").replace(" ", "_")
        env_prefix = f"MCP_{safe_tool_name}"
        url = os.getenv(f"{env_prefix}_URL")
        if url:
            return {
                "url": url,
                "transport": os.getenv(f"{env_prefix}_TRANSPORT", "sse"),
                "headers": {
                    key[len(env_prefix) + 1 :]: value
                    for key, value in os.environ.items()
                    if key.startswith(f"{env_prefix}_HEADER_")
                },
            }

        command = os.getenv(f"{env_prefix}_COMMAND")
        if command:
            args = os.getenv(f"{env_prefix}_ARGS", "").split()
            env_vars = {
                key[len(env_prefix) + 1 :]: value
                for key, value in os.environ.items()
                if key.startswith(f"{env_prefix}_ENV_")
            }
            return {"command": command, "args": args, "env": env_vars}

        raise RuntimeError(f"No MCP configuration registered for tool '{tool_name}'.")


class MCPToolDiscoveryEngine:
    """Discover MCP tools based on registered intent mappings."""

    def __init__(self) -> None:
        self._registry: Dict[str, List[MCPToolSpec]] = {}
        self._lock = threading.Lock()

    def register_tool(self, intent_category: str, spec: MCPToolSpec) -> None:
        with self._lock:
            specs = self._registry.setdefault(intent_category, [])
            specs.append(spec)

    def discover_tools(self, intent_category: str) -> List[MCPToolSpec]:
        with self._lock:
            return list(self._registry.get(intent_category, []))


class MCPIntegrationManager:
    """High level coordinator for MCP tool usage within graphs."""

    def __init__(self, *, config_manager: Optional[MCPConfigManager] = None, discovery_engine: Optional[MCPToolDiscoveryEngine] = None) -> None:
        self.config_manager = config_manager or MCPConfigManager()
        self.discovery_engine = discovery_engine or MCPToolDiscoveryEngine()
        self._tool_cache: Dict[str, MCPTool] = {}
        self._lock = threading.Lock()

    def register_tool(self, *, intent_category: str, spec: MCPToolSpec, config: Optional[Dict[str, object]] = None) -> None:
        if config is not None:
            self.config_manager.register_config(spec.name, config)
        self.discovery_engine.register_tool(intent_category, spec)

    def ensure_tools_for_intent(self, intent_category: str) -> List[MCPToolSpec]:
        return self.discovery_engine.discover_tools(intent_category)

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        with self._lock:
            if tool_name in self._tool_cache:
                return self._tool_cache[tool_name]

            try:
                mcp_config = self.config_manager.get_config(tool_name)
            except Exception:
                return None

            try:
                tool = MCPTool(
                    name=tool_name,
                    description=f"Auto-integrated MCP tool {tool_name}",
                    mcp_config=mcp_config,
                )
            except Exception:
                return None

            self._tool_cache[tool_name] = tool
            return tool
