"""Declarative builders and helpers for SpoonAI graphs."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import (Any, Callable, Dict, Iterable, List, Optional, Sequence,
                    Tuple)

from spoon_ai.llm.manager import LLMManager, get_llm_manager
from spoon_ai.schema import Message

from .config import GraphConfig, ParallelGroupConfig
from .engine import END, StateGraph
from .mcp_integration import (MCPIntegrationManager, MCPToolDiscoveryEngine,
                               MCPToolSpec)
from spoon_ai.tools.mcp_tool import MCPTool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Intent analysis helpers
# ---------------------------------------------------------------------------


@dataclass
class Intent:
    """Result of intent analysis."""

    category: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentAnalyzer:
    """LLM-powered intent analyzer.

    Core stays generic; concrete prompts/parsers are supplied by callers.
    """

    def __init__(
        self,
        *,
        llm_manager: Optional[LLMManager] = None,
        prompt_builder: Optional[Callable[[str], List[Message]]] = None,
        parser: Optional[Callable[[str], Dict[str, Any]]] = None,
    ) -> None:
        self._llm: LLMManager = llm_manager or get_llm_manager()
        self._prompt_builder = prompt_builder
        self._parser = parser

    async def analyze(self, query: str) -> Intent:
        if not self._prompt_builder or not self._parser:
            logger.debug("IntentAnalyzer missing prompt/parser; defaulting to general intent")
            return Intent(category="general_qa", confidence=0.0, metadata={})

        try:
            messages = self._prompt_builder(query)
            response = await self._llm.chat(messages, provider=None)
            payload = self._parser(response.content)
        except Exception as exc:
            logger.warning("IntentAnalyzer inference failed: %s", exc)
            payload = {}

        if not isinstance(payload, dict):
            payload = {}

        category = payload.get("category", "general_qa")
        confidence = float(payload.get("confidence", 0.0))
        metadata = {k: v for k, v in payload.items() if k not in {"category", "confidence"}}

        return Intent(category=category, confidence=confidence, metadata=metadata)


# ---------------------------------------------------------------------------
# State construction helpers
# ---------------------------------------------------------------------------


class AdaptiveStateBuilder:
    """Construct initial graph state using query intent and optional parameters."""

    def __init__(self, parameter_inference: "ParameterInferenceEngine"):
        self.parameter_inference = parameter_inference

    async def build_state(self, query: str, user_name: str, intent: Intent) -> Dict[str, Any]:
        parameters = await self.parameter_inference.infer_parameters(query, intent)
        base_state = {
            "user_query": query,
            "user_name": user_name,
            "session_id": "",
            "query_intent": intent.category,
            "routing_decisions": [],
            "execution_log": [],
            "current_step": "initialized",
            "parallel_tasks_completed": 0,
        }
        if parameters:
            base_state.update(parameters)
        return base_state


class ParameterInferenceEngine:
    """LLM delegator for parameter extraction.

    Core keeps this generic; applications provide formatting/parsing via options.
    """

    def __init__(
        self,
        *,
        llm_manager: Optional[LLMManager] = None,
        prompt_builder: Optional[Callable[[str, Intent], List[Message]]] = None,
        parser: Optional[Callable[[str, Intent], Dict[str, Any]]] = None,
    ) -> None:
        self._llm: LLMManager = llm_manager or get_llm_manager()
        self._prompt_builder = prompt_builder
        self._parser = parser

    async def infer_parameters(self, query: str, intent: Intent) -> Dict[str, Any]:
        if self._prompt_builder is None or self._parser is None:
            logger.debug("ParameterInferenceEngine has no prompt/parser; skipping inference")
            return {}

        try:
            messages = self._prompt_builder(query, intent)
            response = await self._llm.chat(messages, provider=None)
            payload = self._parser(response.content, intent)
            if not isinstance(payload, dict):
                return {}
            return payload
        except Exception as exc:
            logger.warning("Parameter inference failed: %s", exc)
            return {}


# ---------------------------------------------------------------------------
# Declarative graph definitions
# ---------------------------------------------------------------------------


@dataclass
class NodeSpec:
    """Declarative node specification."""

    name: str
    handler: Callable[[Dict[str, Any]], Any]
    parallel_group: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeSpec:
    """Declarative edge specification."""

    start: str
    end: Any  # target name or callable router
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None


@dataclass
class ParallelGroupSpec:
    """Parallel group specification."""

    name: str
    nodes: Sequence[str]
    config: Optional[ParallelGroupConfig] = None


@dataclass
class GraphTemplate:
    """Complete declarative template for a graph."""

    entry_point: str
    nodes: Sequence[NodeSpec]
    edges: Sequence[EdgeSpec]
    parallel_groups: Sequence[ParallelGroupSpec] = dataclasses.field(default_factory=list)
    config: Optional[GraphConfig] = None


class DeclarativeGraphBuilder:
    """Build StateGraph instances from declarative templates."""

    def __init__(self, state_schema: type, default_config: Optional[GraphConfig] = None):
        self.state_schema = state_schema
        self.default_config = default_config or GraphConfig()

    def build(self, template: GraphTemplate) -> StateGraph:
        graph = StateGraph(self.state_schema)
        graph.config = template.config or self.default_config

        auto_groups: Dict[str, List[str]] = defaultdict(list)

        for node in template.nodes:
            graph.add_node(node.name, node.handler)
            if node.parallel_group:
                auto_groups[node.parallel_group].append(node.name)

        for edge in template.edges:
            if isinstance(edge.end, dict) and callable(edge.condition):
                graph.add_conditional_edges(edge.start, edge.condition, edge.end)
            else:
                graph.add_edge(edge.start, edge.end, edge.condition)

        explicit_group_map: Dict[str, ParallelGroupSpec] = {spec.name: spec for spec in template.parallel_groups}

        # Merge automatic group membership with explicit specs
        all_group_names = set(auto_groups.keys()) | set(explicit_group_map.keys())
        for group_name in all_group_names:
            nodes: List[str] = []
            if group_name in auto_groups:
                nodes.extend(auto_groups[group_name])
            if group_name in explicit_group_map:
                nodes.extend(list(explicit_group_map[group_name].nodes))
            # Deduplicate while preserving order
            deduped_nodes = []
            seen = set()
            for node_name in nodes:
                if node_name not in seen:
                    deduped_nodes.append(node_name)
                    seen.add(node_name)
            group_config = explicit_group_map[group_name].config if group_name in explicit_group_map else None
            graph.add_parallel_group(group_name, deduped_nodes, group_config)

        graph.set_entry_point(template.entry_point)
        return graph


# ---------------------------------------------------------------------------
# Node plugin system and high-level API
# ---------------------------------------------------------------------------


class NodePlugin:
    """Pluggable node provider."""

    def __init__(self, name: str, factory: Callable[[], Callable], parallel_group: Optional[str] = None):
        self.name = name
        self.factory = factory
        self.parallel_group = parallel_group

    def to_spec(self) -> NodeSpec:
        return NodeSpec(name=self.name, handler=self.factory(), parallel_group=self.parallel_group)


class NodePluginSystem:
    """Registry and discovery for node plugins."""

    def __init__(self):
        self._plugins: Dict[str, NodePlugin] = {}

    def register(self, plugin: NodePlugin) -> None:
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Optional[NodePlugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> Iterable[str]:
        return list(self._plugins.keys())


class HighLevelGraphAPI:
    """Convenience facade for building graphs per query."""

    def __init__(
        self,
        state_schema: type,
        config: Optional[GraphConfig] = None,
        *,
        mcp_manager: Optional[MCPIntegrationManager] = None,
        llm_manager: Optional[LLMManager] = None,
        intent_prompt_builder: Optional[Callable[[str], List[Message]]] = None,
        intent_parser: Optional[Callable[[str], Dict[str, Any]]] = None,
        parameter_prompt_builder: Optional[Callable[[str, Intent], List[Message]]] = None,
        parameter_parser: Optional[Callable[[str, Intent], Dict[str, Any]]] = None,
    ):
        self.state_schema = state_schema
        self.intent_analyzer = IntentAnalyzer(
            llm_manager=llm_manager,
            prompt_builder=intent_prompt_builder,
            parser=intent_parser,
        )
        self.parameter_inference = ParameterInferenceEngine(
            llm_manager=llm_manager,
            prompt_builder=parameter_prompt_builder,
            parser=parameter_parser,
        )
        self.state_builder = AdaptiveStateBuilder(self.parameter_inference)
        self.plugin_system = NodePluginSystem()
        self.mcp_manager = mcp_manager or MCPIntegrationManager()
        self.config = config or GraphConfig()

    def register_plugin(self, plugin: NodePlugin) -> None:
        self.plugin_system.register(plugin)

    def register_mcp_tool(self, *, intent_category: str, spec: MCPToolSpec, config: Optional[Dict[str, object]] = None) -> None:
        self.mcp_manager.register_tool(intent_category=intent_category, spec=spec, config=config)

    async def build_initial_state(self, query: str, user_name: str = "User") -> Tuple[Intent, Dict[str, Any]]:
        intent = await self.intent_analyzer.analyze(query)
        state = await self.state_builder.build_state(query, user_name, intent)
        return intent, state

    def ensure_mcp_for_intent(self, intent: Intent) -> None:
        self.mcp_manager.ensure_tools_for_intent(intent.category)

    def build_graph(self, template: GraphTemplate) -> StateGraph:
        builder = DeclarativeGraphBuilder(self.state_schema, template.config or self.config)
        return builder.build(template)

    def create_mcp_tool(self, tool_name: str) -> Optional[MCPTool]:
        return self.mcp_manager.get_tool(tool_name)
