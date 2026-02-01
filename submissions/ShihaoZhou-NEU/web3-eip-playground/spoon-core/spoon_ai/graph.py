"""
Graph-based execution system for SpoonOS agents.

This module provides a LangGraph-inspired framework with advanced features:
- State management with TypedDict and reducers
- LLM Manager integration
- Error handling and recovery
- Human-in-the-loop patterns
- Multi-agent coordination
- Comprehensive testing support
- Checkpointing and persistence
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, Any, Callable, Union, Optional, Tuple, List, Annotated, TypedDict, Literal
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import operator

from spoon_ai.schema import Message
from spoon_ai.llm.manager import get_llm_manager

logger = logging.getLogger(__name__)


class GraphExecutionError(Exception):
    """Raised when graph execution encounters an error."""
    
    def __init__(self, message: str, node: str = None, iteration: int = None, context: Dict[str, Any] = None):
        self.node = node
        self.iteration = iteration
        self.context = context or {}
        super().__init__(message)


class NodeExecutionError(Exception):
    """Raised when a node fails to execute."""
    
    def __init__(self, message: str, node_name: str, original_error: Exception = None, state: Dict[str, Any] = None):
        self.node_name = node_name
        self.original_error = original_error
        self.state = state
        super().__init__(message)


class StateValidationError(Exception):
    """Raised when state validation fails."""
    
    def __init__(self, message: str, field: str = None, expected_type: type = None, actual_value: Any = None):
        self.field = field
        self.expected_type = expected_type
        self.actual_value = actual_value
        super().__init__(message)


class CheckpointError(Exception):
    """Raised when checkpoint operations fail."""
    
    def __init__(self, message: str, thread_id: str = None, checkpoint_id: str = None, operation: str = None):
        self.thread_id = thread_id
        self.checkpoint_id = checkpoint_id
        self.operation = operation
        super().__init__(message)


class GraphConfigurationError(Exception):
    """Raised when graph configuration is invalid."""
    
    def __init__(self, message: str, component: str = None, details: Dict[str, Any] = None):
        self.component = component
        self.details = details or {}
        super().__init__(message)


class EdgeRoutingError(Exception):
    """Raised when edge routing fails."""
    
    def __init__(self, message: str, source_node: str, condition_result: Any = None, available_paths: List[str] = None):
        self.source_node = source_node
        self.condition_result = condition_result
        self.available_paths = available_paths or []
        super().__init__(message)


class InterruptError(Exception):
    """Raised when graph execution is interrupted for human input."""
    
    def __init__(self, interrupt_data: Dict[str, Any], interrupt_id: str = None, node: str = None):
        self.interrupt_data = interrupt_data
        self.interrupt_id = interrupt_id or str(uuid.uuid4())
        self.node = node
        super().__init__(f"Graph interrupted at node '{node}': {interrupt_data}")


@dataclass
class Command:
    """Command object for controlling graph flow and state updates."""
    update: Optional[Dict[str, Any]] = None
    goto: Optional[str] = None
    resume: Optional[Any] = None


@dataclass
class StateSnapshot:
    """Snapshot of graph state at a specific point in time."""
    values: Dict[str, Any]
    next: Tuple[str, ...]
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    parent_config: Optional[Dict[str, Any]] = None
    tasks: Tuple[Any, ...] = field(default_factory=tuple)


class InMemoryCheckpointer:
    """
    Simple in-memory checkpointer for development and testing.
    
    This checkpointer stores state snapshots in memory and provides
    basic checkpoint management functionality. For production use,
    consider using persistent checkpointers like Redis or PostgreSQL.
    """
    
    def __init__(self, max_checkpoints_per_thread: int = 100):
        """
        Initialize the in-memory checkpointer.
        
        Args:
            max_checkpoints_per_thread: Maximum number of checkpoints to keep per thread
        """
        self.checkpoints: Dict[str, List[StateSnapshot]] = {}
        self.max_checkpoints_per_thread = max_checkpoints_per_thread
    
    def save_checkpoint(self, thread_id: str, snapshot: StateSnapshot) -> None:
        """
        Save a checkpoint for a thread.
        
        Args:
            thread_id: Unique identifier for the thread
            snapshot: State snapshot to save
            
        Raises:
            CheckpointError: If checkpoint saving fails
        """
        try:
            if not thread_id:
                raise CheckpointError("Thread ID cannot be empty", operation="save")
            
            if thread_id not in self.checkpoints:
                self.checkpoints[thread_id] = []
            
            self.checkpoints[thread_id].append(snapshot)
            
            # Limit the number of checkpoints per thread
            if len(self.checkpoints[thread_id]) > self.max_checkpoints_per_thread:
                self.checkpoints[thread_id] = self.checkpoints[thread_id][-self.max_checkpoints_per_thread:]
                
            logger.debug(f"Saved checkpoint for thread {thread_id} (total: {len(self.checkpoints[thread_id])})")
            
        except Exception as e:
            raise CheckpointError(
                f"Failed to save checkpoint: {str(e)}", 
                thread_id=thread_id, 
                operation="save"
            ) from e
    
    def get_checkpoint(self, thread_id: str, checkpoint_id: str = None) -> Optional[StateSnapshot]:
        """
        Get a specific checkpoint or the latest one.
        
        Args:
            thread_id: Unique identifier for the thread
            checkpoint_id: Optional specific checkpoint ID
            
        Returns:
            StateSnapshot or None if not found
            
        Raises:
            CheckpointError: If checkpoint retrieval fails
        """
        try:
            if not thread_id:
                raise CheckpointError("Thread ID cannot be empty", operation="get")
                
            if thread_id not in self.checkpoints:
                return None
            
            checkpoints = self.checkpoints[thread_id]
            if not checkpoints:
                return None
                
            if checkpoint_id:
                # Find specific checkpoint by ID (using created_at as ID for simplicity)
                for checkpoint in checkpoints:
                    if str(checkpoint.created_at.timestamp()) == checkpoint_id:
                        return checkpoint
                return None
            
            return checkpoints[-1]  # Return latest
            
        except Exception as e:
            raise CheckpointError(
                f"Failed to get checkpoint: {str(e)}", 
                thread_id=thread_id, 
                checkpoint_id=checkpoint_id,
                operation="get"
            ) from e
    
    def list_checkpoints(self, thread_id: str) -> List[StateSnapshot]:
        """
        List all checkpoints for a thread.
        
        Args:
            thread_id: Unique identifier for the thread
            
        Returns:
            List of state snapshots
            
        Raises:
            CheckpointError: If checkpoint listing fails
        """
        try:
            if not thread_id:
                raise CheckpointError("Thread ID cannot be empty", operation="list")
                
            return self.checkpoints.get(thread_id, [])
            
        except Exception as e:
            raise CheckpointError(
                f"Failed to list checkpoints: {str(e)}", 
                thread_id=thread_id,
                operation="list"
            ) from e
    
    def clear_thread(self, thread_id: str) -> None:
        """
        Clear all checkpoints for a thread.
        
        Args:
            thread_id: Unique identifier for the thread
        """
        if thread_id in self.checkpoints:
            del self.checkpoints[thread_id]
            logger.debug(f"Cleared all checkpoints for thread {thread_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get checkpointer statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_checkpoints = sum(len(checkpoints) for checkpoints in self.checkpoints.values())
        return {
            "total_threads": len(self.checkpoints),
            "total_checkpoints": total_checkpoints,
            "max_checkpoints_per_thread": self.max_checkpoints_per_thread,
            "threads": {
                thread_id: len(checkpoints) 
                for thread_id, checkpoints in self.checkpoints.items()
            }
        }


def add_messages(existing: List[Any], new: List[Any]) -> List[Any]:
    """Reducer function for adding messages to a list."""
    if existing is None:
        existing = []
    if new is None:
        return existing
    return existing + new


def interrupt(data: Dict[str, Any]) -> Any:
    """Interrupt execution and wait for human input."""
    raise InterruptError(data)


class StateGraph:
    """
    Enhanced StateGraph with LangGraph-inspired features and SpoonOS integration.
    
    Features:
    - TypedDict state management with reducers
    - LLM Manager integration
    - Error handling and recovery
    - Human-in-the-loop patterns
    - Checkpointing and persistence
    - Multi-agent coordination support
    """

    def __init__(self, state_schema: type, checkpointer: InMemoryCheckpointer = None):
        """
        Initialize the enhanced state graph.

        Args:
            state_schema: TypedDict class defining the state structure
            checkpointer: Optional checkpointer for state persistence
        """
        self.state_schema = state_schema
        self.checkpointer = checkpointer or InMemoryCheckpointer()
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, Union[Callable, Tuple[Callable, Dict[str, str]]]] = {}
        self.entry_point: Optional[str] = None
        self._compiled = False
        self.interrupts: Dict[str, InterruptError] = {}
        self.llm_manager = get_llm_manager()

    def add_node(self, name: str, action: Callable) -> "StateGraph":
        """
        Add a node to the graph.
        
        Args:
            name: Unique identifier for the node
            action: Function or coroutine that processes the state
                   Should accept state dict and return dict of updates or Command
        
        Returns:
            Self for method chaining
            
        Raises:
            GraphConfigurationError: If node name already exists or is invalid
        """
        if not name or not isinstance(name, str):
            raise GraphConfigurationError(
                "Node name must be a non-empty string", 
                component="node",
                details={"name": name}
            )
            
        if name in ["START", "END"]:
            raise GraphConfigurationError(
                f"Node name '{name}' is reserved", 
                component="node",
                details={"name": name, "reserved_names": ["START", "END"]}
            )
            
        if name in self.nodes:
            raise GraphConfigurationError(
                f"Node '{name}' already exists in the graph", 
                component="node",
                details={"name": name, "existing_nodes": list(self.nodes.keys())}
            )
            
        if not callable(action):
            raise GraphConfigurationError(
                f"Node action must be callable", 
                component="node",
                details={"name": name, "action_type": type(action)}
            )

        self.nodes[name] = action
        logger.debug(f"Added node '{name}' to graph")
        return self
    
    def add_llm_node(self, 
                     name: str,
                     system_prompt: str,
                     provider: Optional[str] = None,
                     model_params: Optional[Dict[str, Any]] = None) -> "StateGraph":
        """
        Add an LLM-powered node to the graph.
        
        Args:
            name: Unique identifier for the node
            system_prompt: System prompt for the LLM
            provider: Specific LLM provider to use
            model_params: Parameters for the LLM call
            
        Returns:
            Self for method chaining
        """
        async def llm_action(state: Dict[str, Any]) -> Dict[str, Any]:
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=str(state.get("input", state)))
            ]
            
            params = model_params or {}
            response = await self.llm_manager.chat(messages, provider=provider, **params)
            
            return {
                "llm_response": response.content,
                "llm_metadata": {
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage
                }
            }
        
        return self.add_node(name, llm_action)

    def add_edge(self, start_node: str, end_node: str) -> "StateGraph":
        """
        Add a direct, unconditional edge between two nodes.
        
        Args:
            start_node: Name of the source node (or "START")
            end_node: Name of the destination node (or "END")
        
        Returns:
            Self for method chaining
            
        Raises:
            GraphConfigurationError: If nodes don't exist or edge is invalid
        """
        if start_node != "START" and start_node not in self.nodes:
            raise GraphConfigurationError(
                f"Start node '{start_node}' does not exist", 
                component="edge",
                details={
                    "start_node": start_node, 
                    "end_node": end_node,
                    "available_nodes": list(self.nodes.keys())
                }
            )
            
        if end_node != "END" and end_node not in self.nodes:
            raise GraphConfigurationError(
                f"End node '{end_node}' does not exist", 
                component="edge",
                details={
                    "start_node": start_node, 
                    "end_node": end_node,
                    "available_nodes": list(self.nodes.keys())
                }
            )

        self.edges[start_node] = lambda state: end_node
        logger.debug(f"Added edge from '{start_node}' to '{end_node}'")
        return self

    def add_conditional_edges(
        self,
        start_node: str,
        condition: Callable[[Dict[str, Any]], str],
        path_map: Dict[str, str]
    ) -> "StateGraph":
        """
        Add conditional edges that route to different nodes based on state.
        
        Args:
            start_node: Name of the source node
            condition: Function that takes state and returns a key from path_map
            path_map: Mapping from condition results to destination node names
        
        Returns:
            Self for method chaining
            
        Raises:
            GraphConfigurationError: If configuration is invalid
        """
        if start_node not in self.nodes:
            raise GraphConfigurationError(
                f"Start node '{start_node}' does not exist", 
                component="conditional_edge",
                details={
                    "start_node": start_node,
                    "available_nodes": list(self.nodes.keys())
                }
            )
            
        if not callable(condition):
            raise GraphConfigurationError(
                "Condition function must be callable", 
                component="conditional_edge",
                details={"start_node": start_node, "condition_type": type(condition)}
            )
            
        if not path_map:
            raise GraphConfigurationError(
                "Path map cannot be empty", 
                component="conditional_edge",
                details={"start_node": start_node}
            )

        # Validate all destination nodes exist
        invalid_nodes = []
        for path_key, dest_node in path_map.items():
            if dest_node != "END" and dest_node not in self.nodes:
                invalid_nodes.append(dest_node)
                
        if invalid_nodes:
            raise GraphConfigurationError(
                f"Destination nodes do not exist: {invalid_nodes}", 
                component="conditional_edge",
                details={
                    "start_node": start_node,
                    "invalid_nodes": invalid_nodes,
                    "available_nodes": list(self.nodes.keys()),
                    "path_map": path_map
                }
            )

        self.edges[start_node] = (condition, path_map)
        logger.debug(f"Added conditional edges from '{start_node}' with {len(path_map)} paths")
        return self

    def set_entry_point(self, node_name: str) -> "StateGraph":
        """
        Set the starting node for graph execution.
        
        Args:
            node_name: Name of the node to start execution from
        
        Returns:
            Self for method chaining
            
        Raises:
            GraphConfigurationError: If entry point node doesn't exist
        """
        if node_name not in self.nodes:
            raise GraphConfigurationError(
                f"Entry point node '{node_name}' does not exist", 
                component="entry_point",
                details={
                    "node_name": node_name,
                    "available_nodes": list(self.nodes.keys())
                }
            )

        self.entry_point = node_name
        logger.debug(f"Set entry point to '{node_name}'")
        return self

    def compile(self) -> "CompiledGraph":
        """
        Compile the graph into an executable form.
        
        Returns:
            CompiledGraph instance ready for execution
        
        Raises:
            GraphConfigurationError: If graph configuration is invalid
        """
        # Validate graph configuration
        validation_errors = []
        
        if not self.entry_point:
            validation_errors.append("Graph must have an entry point set before compilation")

        if not self.nodes:
            validation_errors.append("Graph must have at least one node")
            
        # Check for unreachable nodes
        reachable_nodes = set()
        if self.entry_point:
            self._find_reachable_nodes(self.entry_point, reachable_nodes)
            
        unreachable_nodes = set(self.nodes.keys()) - reachable_nodes
        if unreachable_nodes:
            logger.warning(f"Unreachable nodes detected: {unreachable_nodes}")
            
        # Check for nodes without outgoing edges (potential dead ends)
        dead_end_nodes = []
        for node_name in self.nodes.keys():
            if node_name not in self.edges:
                dead_end_nodes.append(node_name)
                
        if dead_end_nodes:
            logger.warning(f"Nodes without outgoing edges (potential dead ends): {dead_end_nodes}")
        
        if validation_errors:
            raise GraphConfigurationError(
                f"Graph compilation failed: {'; '.join(validation_errors)}", 
                component="compilation",
                details={
                    "errors": validation_errors,
                    "nodes": list(self.nodes.keys()),
                    "entry_point": self.entry_point,
                    "unreachable_nodes": list(unreachable_nodes),
                    "dead_end_nodes": dead_end_nodes
                }
            )

        self._compiled = True
        logger.info(f"Compiled graph with {len(self.nodes)} nodes and entry point '{self.entry_point}'")
        return CompiledGraph(self)
    
    def _find_reachable_nodes(self, current_node: str, reachable: set, visited: set = None) -> None:
        """Find all nodes reachable from the current node."""
        if visited is None:
            visited = set()
            
        if current_node in visited or current_node == "END":
            return
            
        visited.add(current_node)
        reachable.add(current_node)
        
        if current_node in self.edges:
            edge = self.edges[current_node]
            
            if isinstance(edge, tuple):
                # Conditional edges
                _, path_map = edge
                for dest_node in path_map.values():
                    if dest_node != "END":
                        self._find_reachable_nodes(dest_node, reachable, visited)
            elif callable(edge):
                # This is more complex for dynamic edges, skip for now
                pass


class CompiledGraph:
    """
    Executable version of a StateGraph with advanced features.
    """

    def __init__(self, graph: StateGraph):
        """Initialize with a compiled StateGraph."""
        self.graph = graph
        self.execution_history: List[Dict[str, Any]] = []

    async def invoke(self, initial_state: Optional[Dict[str, Any]] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the graph from the entry point."""
        config = config or {}
        thread_id = config.get("configurable", {}).get("thread_id", str(uuid.uuid4()))
        
        # Initialize state
        state = self._initialize_state(initial_state)
        
        # Check for resume command
        if isinstance(initial_state, Command) and initial_state.resume is not None:
            return await self._resume_execution(initial_state, config, thread_id)

        current_node = self.graph.entry_point
        execution_path = []
        max_iterations = 100
        iteration = 0

        logger.info(f"Starting graph execution from '{current_node}' (thread: {thread_id})")

        try:
            while current_node and iteration < max_iterations:
                iteration += 1
                execution_path.append(current_node)

                logger.debug(f"Executing node '{current_node}' (iteration {iteration})")

                # Save checkpoint before execution
                try:
                    snapshot = StateSnapshot(
                        values=state.copy(),
                        next=(current_node,),
                        config=config,
                        metadata={"iteration": iteration, "node": current_node},
                        created_at=datetime.now()
                    )
                    self.graph.checkpointer.save_checkpoint(thread_id, snapshot)
                except CheckpointError as e:
                    logger.warning(f"Failed to save checkpoint before node execution: {e}")
                    # Continue execution even if checkpoint fails
                except Exception as e:
                    logger.warning(f"Unexpected error saving checkpoint: {e}")
                    # Continue execution even if checkpoint fails

                # Execute the current node
                try:
                    result = await self._execute_node(current_node, state)
                    
                    # Handle Command objects
                    if isinstance(result, Command):
                        if result.update:
                            self._update_state_with_reducers(state, result.update)
                        if result.goto:
                            current_node = result.goto
                            # Special handling for END
                            if current_node == "END":
                                logger.info("Graph execution completed via Command")
                                break
                            continue
                    elif isinstance(result, dict):
                        self._update_state_with_reducers(state, result)

                except InterruptError as e:
                    # Handle human-in-the-loop interrupts
                    e.node = current_node  # Set the node where interrupt occurred
                    logger.info(f"Graph interrupted at node '{current_node}': {e.interrupt_data}")
                    self.graph.interrupts[e.interrupt_id] = e
                    
                    try:
                        # Save interrupt state
                        interrupt_snapshot = StateSnapshot(
                            values=state.copy(),
                            next=(current_node,),
                            config=config,
                            metadata={
                                "iteration": iteration,
                                "node": current_node,
                                "interrupt_id": e.interrupt_id,
                                "interrupt_data": e.interrupt_data,
                                "status": "interrupted"
                            },
                            created_at=datetime.now()
                        )
                        self.graph.checkpointer.save_checkpoint(thread_id, interrupt_snapshot)
                    except CheckpointError as checkpoint_error:
                        logger.error(f"Failed to save interrupt checkpoint: {checkpoint_error}")
                        # Continue with interrupt handling even if checkpoint fails
                    
                    # Return state with interrupt information
                    return {
                        **state,
                        "__interrupt__": [{
                            "interrupt_id": e.interrupt_id,
                            "value": e.interrupt_data,
                            "node": current_node,
                            "iteration": iteration
                        }]
                    }

                # Record execution step
                self.execution_history.append({
                    "node": current_node,
                    "iteration": iteration,
                    "state_before": state.copy(),
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })

                # Determine next node
                next_node = await self._get_next_node(current_node, state)

                if next_node == current_node:
                    logger.warning(f"Node '{current_node}' routes to itself, stopping execution")
                    break

                current_node = next_node

                # Special handling for END node
                if current_node == "END" or current_node is None:
                    logger.info("Graph execution completed")
                    break

            if iteration >= max_iterations:
                raise GraphExecutionError(
                    f"Graph execution exceeded maximum iterations ({max_iterations})",
                    node=current_node,
                    iteration=iteration,
                    context={
                        "execution_path": execution_path,
                        "thread_id": thread_id,
                        "max_iterations": max_iterations
                    }
                )

            # Save final checkpoint
            try:
                final_snapshot = StateSnapshot(
                    values=state.copy(),
                    next=(),
                    config=config,
                    metadata={
                        "iteration": iteration, 
                        "status": "completed",
                        "execution_path": execution_path
                    },
                    created_at=datetime.now()
                )
                self.graph.checkpointer.save_checkpoint(thread_id, final_snapshot)
            except CheckpointError as e:
                logger.warning(f"Failed to save final checkpoint: {e}")
                # Don't fail the execution for checkpoint errors

            logger.info(f"Graph execution completed in {iteration} steps: {' -> '.join(execution_path)}")
            return state

        except GraphExecutionError:
            # Re-raise graph execution errors as-is
            raise
        except Exception as e:
            logger.error(f"Graph execution failed: {str(e)}")
            raise GraphExecutionError(
                f"Graph execution failed: {str(e)}",
                node=current_node,
                iteration=iteration,
                context={
                    "execution_path": execution_path,
                    "thread_id": thread_id,
                    "original_error": str(e)
                }
            ) from e

    async def stream(self, initial_state: Optional[Dict[str, Any]] = None, config: Optional[Dict[str, Any]] = None, stream_mode: str = "values"):
        """Stream graph execution with different modes."""
        config = config or {}
        thread_id = config.get("configurable", {}).get("thread_id", str(uuid.uuid4()))
        
        state = self._initialize_state(initial_state)
        current_node = self.graph.entry_point
        iteration = 0
        max_iterations = 100

        logger.info(f"Starting graph streaming from '{current_node}' (mode: {stream_mode})")

        try:
            while current_node and iteration < max_iterations:
                iteration += 1
                
                if stream_mode == "debug":
                    yield {
                        "type": "debug",
                        "node": current_node,
                        "iteration": iteration,
                        "state": state.copy()
                    }

                # Execute node
                try:
                    result = await self._execute_node(current_node, state)
                    
                    if isinstance(result, Command):
                        if result.update:
                            old_state = state.copy()
                            self._update_state_with_reducers(state, result.update)
                            
                            if stream_mode == "updates":
                                yield {current_node: result.update}
                            elif stream_mode == "values":
                                yield state.copy()
                        
                        if result.goto:
                            current_node = result.goto
                            continue
                    elif isinstance(result, dict):
                        old_state = state.copy()
                        self._update_state_with_reducers(state, result)
                        
                        if stream_mode == "updates":
                            yield {current_node: result}
                        elif stream_mode == "values":
                            yield state.copy()

                except InterruptError as e:
                    logger.info(f"Graph interrupted during streaming at node '{current_node}'")
                    yield {
                        "type": "interrupt",
                        "node": current_node,
                        "interrupt_id": e.interrupt_id,
                        "interrupt_data": e.interrupt_data,
                        "state": state.copy()
                    }
                    return

                # Determine next node
                next_node = await self._get_next_node(current_node, state)
                
                if next_node == "END" or next_node is None:
                    if stream_mode == "values":
                        yield state.copy()
                    break
                    
                current_node = next_node

        except Exception as e:
            logger.error(f"Graph streaming failed: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "state": state.copy()
            }

    async def _resume_execution(self, command: Command, config: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        """Resume execution after an interrupt."""
        # Get the latest checkpoint
        latest_checkpoint = self.graph.checkpointer.get_checkpoint(thread_id)
        if not latest_checkpoint:
            raise GraphExecutionError("No checkpoint found for resumption")

        # Check if there's an interrupt to resume
        interrupt_id = latest_checkpoint.metadata.get("interrupt_id")
        if not interrupt_id or interrupt_id not in self.graph.interrupts:
            raise GraphExecutionError("No interrupt found for resumption")

        # Get the interrupt and resume data
        interrupt_error = self.graph.interrupts[interrupt_id]
        resume_data = command.resume

        # Clear the interrupt
        del self.graph.interrupts[interrupt_id]

        # Resume from the interrupted state
        state = latest_checkpoint.values.copy()
        current_node = latest_checkpoint.metadata.get("node")
        
        logger.info(f"Resuming execution at node '{current_node}' with data: {resume_data}")

        # Continue execution with the resume data
        # For simplicity, we'll inject the resume data into the state
        state["__resume_data__"] = resume_data
        
        # Continue normal execution
        return await self.invoke(state, config)

    def _initialize_state(self, initial_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Initialize state with schema defaults."""
        state = {}
        
        # Initialize with schema defaults if available
        if hasattr(self.graph.state_schema, '__annotations__'):
            for field_name, field_type in self.graph.state_schema.__annotations__.items():
                # Handle Annotated types (for reducers)
                if hasattr(field_type, '__origin__') and field_type.__origin__ is Annotated:
                    # Initialize with empty list for list types
                    if 'list' in str(field_type) or 'List' in str(field_type):
                        state[field_name] = []
                    else:
                        state[field_name] = None
                else:
                    state[field_name] = None

        if initial_state and not isinstance(initial_state, Command):
            state.update(initial_state)
        
        return state

    async def _execute_node(self, node_name: str, state: Dict[str, Any]) -> Any:
        """Execute a node with error handling."""
        node_action = self.graph.nodes[node_name]
        
        try:
            if asyncio.iscoroutinefunction(node_action):
                result = await node_action(state)
            else:
                result = node_action(state)
            return result
        except InterruptError:
            # Re-raise interrupt errors
            raise
        except Exception as e:
            logger.error(f"Node '{node_name}' execution failed: {str(e)}")
            raise NodeExecutionError(
                f"Node '{node_name}' failed: {str(e)}", 
                node_name=node_name,
                original_error=e,
                state=state
            ) from e

    async def _get_next_node(self, current_node: str, state: Dict[str, Any]) -> Optional[str]:
        """
        Determine the next node to execute based on edges and state.
        
        Args:
            current_node: Current node name
            state: Current state
            
        Returns:
            Next node name or None if execution should stop
            
        Raises:
            EdgeRoutingError: If edge routing fails
            NodeExecutionError: If edge function execution fails
        """
        if current_node not in self.graph.edges:
            return None

        edge = self.graph.edges[current_node]

        # Handle conditional edges
        if isinstance(edge, tuple):
            condition_func, path_map = edge
            try:
                if asyncio.iscoroutinefunction(condition_func):
                    condition_result = await condition_func(state)
                else:
                    condition_result = condition_func(state)

                if condition_result in path_map:
                    next_node = path_map[condition_result]
                    logger.debug(f"Conditional edge from '{current_node}': {condition_result} -> '{next_node}'")
                    return next_node
                else:
                    available_paths = list(path_map.keys())
                    raise EdgeRoutingError(
                        f"Condition result '{condition_result}' not found in path map for node '{current_node}'. Available paths: {available_paths}",
                        source_node=current_node,
                        condition_result=condition_result,
                        available_paths=available_paths
                    )

            except EdgeRoutingError:
                # Re-raise edge routing errors as-is
                raise
            except Exception as e:
                logger.error(f"Condition function failed for node '{current_node}': {str(e)}")
                raise NodeExecutionError(
                    f"Condition function failed: {str(e)}", 
                    node_name=current_node,
                    original_error=e,
                    state=state
                ) from e

        # Handle simple edges
        elif callable(edge):
            try:
                if asyncio.iscoroutinefunction(edge):
                    next_node = await edge(state)
                else:
                    next_node = edge(state)

                logger.debug(f"Edge from '{current_node}' -> '{next_node}'")
                return next_node

            except Exception as e:
                logger.error(f"Edge function failed for node '{current_node}': {str(e)}")
                raise NodeExecutionError(
                    f"Edge function failed: {str(e)}", 
                    node_name=current_node,
                    original_error=e,
                    state=state
                ) from e

        return None

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history for debugging and analysis."""
        return self.execution_history.copy()

    def get_state(self, config: Dict[str, Any]) -> Optional[StateSnapshot]:
        """Get the current state snapshot for a thread."""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None
        return self.graph.checkpointer.get_checkpoint(thread_id)

    def _update_state_with_reducers(self, state: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """
        Update state using reducer functions where applicable.
        
        Args:
            state: Current state dictionary
            updates: Updates to apply to the state
            
        Raises:
            StateValidationError: If state validation fails
        """
        try:
            for key, value in updates.items():
                if key in state and hasattr(self.graph.state_schema, '__annotations__'):
                    field_type = self.graph.state_schema.__annotations__.get(key)
                    
                    # Check if this field has a reducer (Annotated type)
                    if hasattr(field_type, '__origin__') and field_type.__origin__ is Annotated:
                        # Get the reducer function from the annotation
                        if len(field_type.__args__) > 1:
                            reducer = field_type.__args__[1]
                            if callable(reducer):
                                try:
                                    # Apply the reducer
                                    state[key] = reducer(state[key], value)
                                    continue
                                except Exception as e:
                                    raise StateValidationError(
                                        f"Reducer function failed for field '{key}': {str(e)}",
                                        field=key,
                                        actual_value=value
                                    ) from e
                
                # Default behavior - direct assignment
                state[key] = value
                
        except StateValidationError:
            # Re-raise state validation errors as-is
            raise
        except Exception as e:
            raise StateValidationError(
                f"State update failed: {str(e)}",
                actual_value=updates
            ) from e