"""
Comprehensive tests for the graph system.

Tests cover:
- Basic graph execution
- State management with reducers
- Error handling and recovery
- Human-in-the-loop patterns
- Streaming capabilities
- Checkpointing and persistence
- Multi-agent coordination patterns
"""

import pytest
import asyncio
from typing import List, Dict, Any, Annotated, TypedDict, Literal
from unittest.mock import Mock, AsyncMock, patch
import operator

from spoon_ai.graph import (
    StateGraph, 
    CompiledGraph,
    InMemoryCheckpointer,
    Command,
    StateSnapshot,
    interrupt,
    add_messages,
    GraphExecutionError,
    NodeExecutionError,
    InterruptError,
    GraphConfigurationError,
    StateValidationError,
    CheckpointError
)


# Test state schemas
class BasicState(TypedDict):
    counter: int
    messages: Annotated[List[str], add_messages]
    data: Dict[str, Any]


class AgentState(TypedDict):
    messages: Annotated[List[Dict[str, str]], add_messages]
    current_agent: str
    task_completed: bool


class TestStateGraph:
    """Test the state graph functionality."""

    def test_graph_initialization(self):
        """Test basic graph initialization."""
        graph = StateGraph(BasicState)
        
        assert graph.state_schema == BasicState
        assert isinstance(graph.checkpointer, InMemoryCheckpointer)
        assert graph.nodes == {}
        assert graph.edges == {}
        assert graph.entry_point is None
        assert not graph._compiled

    def test_add_node(self):
        """Test adding nodes to the graph."""
        graph = StateGraph(BasicState)
        
        def test_node(state):
            return {"counter": state["counter"] + 1}
        
        result = graph.add_node("test_node", test_node)
        
        assert result is graph  # Method chaining
        assert "test_node" in graph.nodes
        assert graph.nodes["test_node"] == test_node

    def test_add_duplicate_node_raises_error(self):
        """Test that adding duplicate nodes raises an error."""
        graph = StateGraph(BasicState)
        
        def test_node(state):
            return {"counter": 1}
        
        graph.add_node("test_node", test_node)
        
        with pytest.raises(GraphConfigurationError, match="Node 'test_node' already exists"):
            graph.add_node("test_node", test_node)

    def test_add_edge(self):
        """Test adding edges between nodes."""
        graph = StateGraph(BasicState)
        
        def node_a(state):
            return {"counter": 1}
        
        def node_b(state):
            return {"counter": 2}
        
        graph.add_node("node_a", node_a)
        graph.add_node("node_b", node_b)
        
        result = graph.add_edge("node_a", "node_b")
        
        assert result is graph  # Method chaining
        assert "node_a" in graph.edges
        
        # Test the edge function
        edge_func = graph.edges["node_a"]
        assert callable(edge_func)
        assert edge_func({}) == "node_b"

    def test_add_conditional_edges(self):
        """Test adding conditional edges."""
        graph = StateGraph(BasicState)
        
        def node_a(state):
            return {"counter": 1}
        
        def node_b(state):
            return {"counter": 2}
        
        def node_c(state):
            return {"counter": 3}
        
        def condition(state):
            return "b" if state["counter"] < 5 else "c"
        
        graph.add_node("node_a", node_a)
        graph.add_node("node_b", node_b)
        graph.add_node("node_c", node_c)
        
        path_map = {"b": "node_b", "c": "node_c"}
        result = graph.add_conditional_edges("node_a", condition, path_map)
        
        assert result is graph
        assert "node_a" in graph.edges
        
        # Test the conditional edge
        edge_data = graph.edges["node_a"]
        assert isinstance(edge_data, tuple)
        condition_func, stored_path_map = edge_data
        assert condition_func == condition
        assert stored_path_map == path_map

    def test_set_entry_point(self):
        """Test setting the entry point."""
        graph = StateGraph(BasicState)
        
        def test_node(state):
            return {"counter": 1}
        
        graph.add_node("test_node", test_node)
        result = graph.set_entry_point("test_node")
        
        assert result is graph
        assert graph.entry_point == "test_node"

    def test_set_invalid_entry_point_raises_error(self):
        """Test that setting invalid entry point raises error."""
        graph = StateGraph(BasicState)
        
        with pytest.raises(GraphConfigurationError, match="Entry point node 'nonexistent' does not exist"):
            graph.set_entry_point("nonexistent")

    def test_compile_graph(self):
        """Test compiling the graph."""
        graph = StateGraph(BasicState)
        
        def test_node(state):
            return {"counter": 1}
        
        graph.add_node("test_node", test_node)
        graph.set_entry_point("test_node")
        
        compiled_graph = graph.compile()
        
        assert isinstance(compiled_graph, CompiledGraph)
        assert compiled_graph.graph is graph
        assert graph._compiled

    def test_compile_without_entry_point_raises_error(self):
        """Test that compiling without entry point raises error."""
        graph = StateGraph(BasicState)
        
        def test_node(state):
            return {"counter": 1}
        
        graph.add_node("test_node", test_node)
        
        with pytest.raises(GraphConfigurationError, match="Graph must have an entry point"):
            graph.compile()

    def test_compile_without_nodes_raises_error(self):
        """Test that compiling without nodes raises error."""
        graph = StateGraph(BasicState)
        
        with pytest.raises(GraphConfigurationError, match="Graph must have at least one node"):
            graph.compile()


class TestCompiledGraph:
    """Test the compiled graph execution."""

    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """Test basic graph execution."""
        graph = StateGraph(BasicState)
        
        def increment_node(state):
            return {"counter": state["counter"] + 1}
        
        graph.add_node("increment", increment_node)
        graph.set_entry_point("increment")
        
        compiled = graph.compile()
        result = await compiled.invoke({"counter": 0, "messages": [], "data": {}})
        
        assert result["counter"] == 1
        assert result["messages"] == []
        assert result["data"] == {}

    @pytest.mark.asyncio
    async def test_multi_node_execution(self):
        """Test execution with multiple nodes."""
        graph = StateGraph(BasicState)
        
        def node_a(state):
            return {"counter": state["counter"] + 1}
        
        def node_b(state):
            return {"counter": state["counter"] * 2}
        
        graph.add_node("node_a", node_a)
        graph.add_node("node_b", node_b)
        graph.add_edge("node_a", "node_b")
        graph.add_edge("node_b", "END")
        graph.set_entry_point("node_a")
        
        compiled = graph.compile()
        result = await compiled.invoke({"counter": 5, "messages": [], "data": {}})
        
        # (5 + 1) * 2 = 12
        assert result["counter"] == 12

    @pytest.mark.asyncio
    async def test_conditional_execution(self):
        """Test execution with conditional edges."""
        graph = StateGraph(BasicState)
        
        def start_node(state):
            return {"counter": state["counter"] + 1}
        
        def even_node(state):
            return {"messages": ["even"]}
        
        def odd_node(state):
            return {"messages": ["odd"]}
        
        def condition(state):
            return "even" if state["counter"] % 2 == 0 else "odd"
        
        graph.add_node("start", start_node)
        graph.add_node("even", even_node)
        graph.add_node("odd", odd_node)
        
        graph.add_conditional_edges("start", condition, {
            "even": "even",
            "odd": "odd"
        })
        graph.add_edge("even", "END")
        graph.add_edge("odd", "END")
        graph.set_entry_point("start")
        
        compiled = graph.compile()
        
        # Test even path
        result = await compiled.invoke({"counter": 1, "messages": [], "data": {}})
        assert result["counter"] == 2  # 1 + 1 = 2 (even)
        assert "even" in result["messages"]
        
        # Test odd path
        result = await compiled.invoke({"counter": 2, "messages": [], "data": {}})
        assert result["counter"] == 3  # 2 + 1 = 3 (odd)
        assert "odd" in result["messages"]

    @pytest.mark.asyncio
    async def test_command_execution(self):
        """Test execution with Command objects."""
        graph = StateGraph(BasicState)
        
        def command_node(state):
            return Command(
                update={"counter": state["counter"] + 10},
                goto="END"
            )
        
        graph.add_node("command", command_node)
        graph.set_entry_point("command")
        
        compiled = graph.compile()
        result = await compiled.invoke({"counter": 5, "messages": [], "data": {}})
        
        assert result["counter"] == 15

    @pytest.mark.asyncio
    async def test_interrupt_handling(self):
        """Test human-in-the-loop interrupt handling."""
        graph = StateGraph(BasicState)
        
        def interrupt_node(state):
            # This will raise an InterruptError
            user_input = interrupt({"message": "Please provide input", "current_state": state})
            return {"data": {"user_input": user_input}}
        
        graph.add_node("interrupt", interrupt_node)
        graph.set_entry_point("interrupt")
        
        compiled = graph.compile()
        config = {"configurable": {"thread_id": "test_thread"}}
        
        # First invocation should return with interrupt
        result = await compiled.invoke({"counter": 0, "messages": [], "data": {}}, config)
        
        assert "__interrupt__" in result
        assert len(result["__interrupt__"]) == 1
        interrupt_info = result["__interrupt__"][0]
        assert "interrupt_id" in interrupt_info
        assert interrupt_info["value"]["message"] == "Please provide input"

    @pytest.mark.asyncio
    async def test_streaming_values_mode(self):
        """Test streaming in values mode."""
        graph = StateGraph(BasicState)
        
        def node_a(state):
            return {"counter": state["counter"] + 1}
        
        def node_b(state):
            return {"counter": state["counter"] * 2}
        
        graph.add_node("node_a", node_a)
        graph.add_node("node_b", node_b)
        graph.add_edge("node_a", "node_b")
        graph.add_edge("node_b", "END")
        graph.set_entry_point("node_a")
        
        compiled = graph.compile()
        
        states = []
        async for chunk in compiled.stream(
            {"counter": 5, "messages": [], "data": {}}, 
            stream_mode="values"
        ):
            states.append(chunk)
        
        # Should have states after each node execution
        assert len(states) >= 2
        assert states[0]["counter"] == 6  # After node_a: 5 + 1
        assert states[1]["counter"] == 12  # After node_b: 6 * 2

    def test_checkpointer_functionality(self):
        """Test the in-memory checkpointer."""
        checkpointer = InMemoryCheckpointer()
        
        from datetime import datetime
        snapshot = StateSnapshot(
            values={"counter": 5},
            next=("node_a",),
            config={"thread_id": "test"},
            metadata={"iteration": 1},
            created_at=datetime.now()
        )
        
        # Save checkpoint
        checkpointer.save_checkpoint("test_thread", snapshot)
        
        # Retrieve checkpoint
        retrieved = checkpointer.get_checkpoint("test_thread")
        assert retrieved is not None
        assert retrieved.values == {"counter": 5}
        assert retrieved.next == ("node_a",)
        
        # List checkpoints
        checkpoints = checkpointer.list_checkpoints("test_thread")
        assert len(checkpoints) == 1
        assert checkpoints[0] == snapshot


if __name__ == "__main__":
    pytest.main([__file__, "-v"])