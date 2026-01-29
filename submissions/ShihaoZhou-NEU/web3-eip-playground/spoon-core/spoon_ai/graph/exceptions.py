"""
Graph engine exception definitions (public within graph package).
"""
from typing import Any, Dict, List, Optional
import uuid


class GraphExecutionError(Exception):
    def __init__(self, message: str, node: str = None, iteration: int = None, context: Dict[str, Any] = None):
        self.node = node
        self.iteration = iteration
        self.context = context or {}
        super().__init__(message)


class NodeExecutionError(Exception):
    def __init__(self, message: str, node_name: str, original_error: Exception = None, state: Dict[str, Any] = None):
        self.node_name = node_name
        self.original_error = original_error
        self.state = state
        super().__init__(message)


class StateValidationError(Exception):
    def __init__(self, message: str, field: str = None, expected_type: type = None, actual_value: Any = None):
        self.field = field
        self.expected_type = expected_type
        self.actual_value = actual_value
        super().__init__(message)


class CheckpointError(Exception):
    def __init__(self, message: str, thread_id: str = None, checkpoint_id: str = None, operation: str = None):
        self.thread_id = thread_id
        self.checkpoint_id = checkpoint_id
        self.operation = operation
        super().__init__(message)


class GraphConfigurationError(Exception):
    def __init__(self, message: str, component: str = None, details: Dict[str, Any] = None):
        self.component = component
        self.details = details or {}
        super().__init__(message)


class EdgeRoutingError(Exception):
    def __init__(self, message: str, source_node: str, condition_result: Any = None, available_paths: List[str] = None):
        self.source_node = source_node
        self.condition_result = condition_result
        self.available_paths = available_paths or []
        super().__init__(message)


class InterruptError(Exception):
    def __init__(self, interrupt_data: Dict[str, Any], interrupt_id: str = None, node: str = None):
        self.interrupt_data = interrupt_data
        self.interrupt_id = interrupt_id or str(uuid.uuid4())
        self.node = node
        super().__init__(f"Graph interrupted at node '{node}': {interrupt_data}")

