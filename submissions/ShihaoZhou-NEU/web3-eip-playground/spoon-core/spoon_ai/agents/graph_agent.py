"""
Graph-based agent implementation for SpoonOS.

This module provides the GraphAgent class that executes StateGraph workflows,
integrating the graph execution system with the existing agent architecture.
"""

import logging
from typing import Optional, Dict, Any
from pydantic import Field, validator

from spoon_ai.agents.base import BaseAgent
from spoon_ai.graph import StateGraph, CompiledGraph, GraphExecutionError
from spoon_ai.schema import AgentState

logger = logging.getLogger(__name__)


class GraphAgent(BaseAgent):
    """
    An agent that executes StateGraph workflows.

    This agent provides a bridge between the existing SpoonOS agent architecture
    and the new graph-based execution system. It allows complex, stateful workflows
    to be defined as graphs and executed with proper state management.

    Key Features:
    - Executes StateGraph workflows
    - Maintains compatibility with existing agent interfaces
    - Provides detailed execution logging and error handling
    - Supports both sync and async node functions
    """

    graph: StateGraph = Field(..., description="The StateGraph to execute")
    compiled_graph: Optional[CompiledGraph] = Field(None, description="Compiled graph instance")
    initial_state: Dict[str, Any] = Field(default_factory=dict, description="Initial state for graph execution")
    preserve_state: bool = Field(default=False, description="Whether to preserve state between runs")
    execution_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata from last execution")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        """
        Initialize the GraphAgent.

        Args:
            graph: StateGraph instance to execute
            **kwargs: Additional arguments passed to BaseAgent

        Raises:
            ValueError: If no graph is provided
        """
        if "graph" not in kwargs:
            raise ValueError("A StateGraph instance must be provided via 'graph' parameter")

        super().__init__(**kwargs)

        # Compile the graph during initialization
        try:
            self.compiled_graph = self.graph.compile()
            logger.info(f"GraphAgent '{self.name}' initialized with compiled graph")
        except Exception as e:
            logger.error(f"Failed to compile graph for agent '{self.name}': {str(e)}")
            raise ValueError(f"Graph compilation failed: {str(e)}") from e

    @validator('graph')
    def validate_graph(cls, v):
        """Validate that the provided graph is a StateGraph instance."""
        if not isinstance(v, StateGraph):
            raise ValueError("graph must be a StateGraph instance")
        return v

    async def run(self, request: Optional[str] = None) -> str:
        """
        Execute the graph workflow.

        This method overrides the base run method to invoke the compiled graph
        instead of the traditional step-based execution loop.

        Args:
            request: Optional input request to include in initial state

        Returns:
            String representation of the execution result

        Raises:
            RuntimeError: If agent is not in IDLE state
            GraphExecutionError: If graph execution fails
        """
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Agent {self.name} is not in the IDLE state")

        logger.info(f"GraphAgent '{self.name}' starting execution")

        # Prepare initial state
        execution_state = {}

        # Start with preserved state if enabled
        if self.preserve_state and hasattr(self, '_last_state'):
            execution_state.update(self._last_state)

        # Add configured initial state
        execution_state.update(self.initial_state)

        # Add request to state if provided
        if request is not None:
            execution_state["input"] = request
            execution_state["request"] = request
            # Also add to agent memory for compatibility
            self.add_message("user", request)

        # Add messages from memory to state
        execution_state["messages"] = [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": getattr(msg, 'tool_calls', None),
                "tool_call_id": getattr(msg, 'tool_call_id', None)
            }
            for msg in self.memory.get_messages()
        ]

        # Add agent context to state
        execution_state["agent_name"] = self.name
        execution_state["agent_description"] = self.description
        execution_state["system_prompt"] = self.system_prompt

        try:
            async with self.state_context(AgentState.RUNNING):
                # Execute the compiled graph
                final_state = await self.compiled_graph.invoke(execution_state)

                # Store execution metadata
                self.execution_metadata = {
                    "execution_history": self.compiled_graph.get_execution_history(),
                    "final_state_keys": list(final_state.keys()),
                    "execution_successful": True
                }

                # Preserve state if enabled
                if self.preserve_state:
                    self._last_state = final_state.copy()

                # Extract output from final state
                output = self._extract_output(final_state)

                # Add assistant response to memory
                if output:
                    self.add_message("assistant", output)

                logger.info(f"GraphAgent '{self.name}' execution completed successfully")
                return output

        except GraphExecutionError as e:
            logger.error(f"Graph execution failed for agent '{self.name}': {str(e)}")
            self.execution_metadata = {
                "execution_history": self.compiled_graph.get_execution_history() if self.compiled_graph else [],
                "error": str(e),
                "execution_successful": False
            }
            raise RuntimeError(f"Graph execution failed: {str(e)}") from e

        except Exception as e:
            logger.error(f"Unexpected error during graph execution for agent '{self.name}': {str(e)}")
            self.execution_metadata = {
                "error": str(e),
                "execution_successful": False
            }
            raise RuntimeError(f"Graph agent execution failed: {str(e)}") from e

    async def step(self) -> str:
        """
        Step method for compatibility with BaseAgent.

        Since GraphAgent uses graph execution instead of step-based execution,
        this method is not used in normal operation but is required by the
        BaseAgent interface.

        Returns:
            Status message indicating graph-based execution
        """
        return "GraphAgent uses graph-based execution, not step-based execution"

    def _extract_output(self, final_state: Dict[str, Any]) -> str:
        """
        Extract the output message from the final graph state.

        Args:
            final_state: The final state after graph execution

        Returns:
            String output for the user
        """
        # Try different common output keys
        output_keys = ["output", "result", "response", "answer", "final_output"]

        for key in output_keys:
            if key in final_state and final_state[key]:
                output = final_state[key]
                if isinstance(output, str):
                    return output
                else:
                    return str(output)

        # If no specific output key found, try to construct a meaningful response
        if "messages" in final_state and final_state["messages"]:
            # Get the last assistant message
            for msg in reversed(final_state["messages"]):
                if msg.get("role") == "assistant" and msg.get("content"):
                    return msg["content"]

        # Fallback to a generic completion message
        return "Graph execution completed successfully."

    def get_execution_history(self) -> list:
        """
        Get the execution history from the last graph run.

        Returns:
            List of execution steps with metadata
        """
        if self.compiled_graph:
            return self.compiled_graph.get_execution_history()
        return []

    def get_execution_metadata(self) -> Dict[str, Any]:
        """
        Get metadata from the last execution.

        Returns:
            Dictionary containing execution metadata
        """
        return self.execution_metadata.copy()

    def clear_state(self):
        """Clear preserved state and execution history."""
        if hasattr(self, '_last_state'):
            delattr(self, '_last_state')
        self.execution_metadata = {}
        if self.compiled_graph:
            self.compiled_graph.execution_history = []
        logger.debug(f"Cleared state for GraphAgent '{self.name}'")

    def update_initial_state(self, updates: Dict[str, Any]):
        """
        Update the initial state for future executions.

        Args:
            updates: Dictionary of state updates to merge
        """
        self.initial_state.update(updates)
        logger.debug(f"Updated initial state for GraphAgent '{self.name}' with keys: {list(updates.keys())}")

    def set_preserve_state(self, preserve: bool):
        """
        Enable or disable state preservation between runs.

        Args:
            preserve: Whether to preserve state between runs
        """
        self.preserve_state = preserve
        if not preserve and hasattr(self, '_last_state'):
            delattr(self, '_last_state')
        logger.debug(f"Set preserve_state={preserve} for GraphAgent '{self.name}'")