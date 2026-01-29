"""
Decorators and executor for the graph package.
"""
import asyncio
import functools
import time
from datetime import datetime
from typing import Any, Callable, Dict

from .types import NodeContext, NodeResult


def node_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    async def async_wrapper(state: Dict[str, Any], context: NodeContext = None) -> NodeResult:
        return await _execute_node_with_context(func, state, context, is_async=True)

    @functools.wraps(func)
    def sync_wrapper(state: Dict[str, Any], context: NodeContext = None) -> NodeResult:
        return _execute_node_with_context(func, state, context, is_async=False)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def router_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    async def async_wrapper(state: Dict[str, Any], context: NodeContext = None):
        if asyncio.iscoroutinefunction(func):
            return await func(state, context)
        else:
            return func(state, context)

    @functools.wraps(func)
    def sync_wrapper(state: Dict[str, Any], context: NodeContext = None):
        return func(state, context)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


async def _execute_node_with_context(func: Callable, state: Dict[str, Any], context: NodeContext, is_async: bool) -> NodeResult:
    start_time = time.time()
    try:
        if context:
            context.start_time = datetime.now()
        result = await func(state, context) if is_async else func(state, context)
        execution_time = time.time() - start_time
        if isinstance(result, NodeResult):
            result.metadata.setdefault("execution_time", execution_time)
            return result
        elif isinstance(result, dict):
            return NodeResult(
                updates=result,
                metadata={"execution_time": execution_time},
                logs=[f"Node executed successfully in {execution_time:.3f}s"],
            )
        else:
            return NodeResult(
                updates={"result": result},
                metadata={"execution_time": execution_time},
                logs=[f"Node executed successfully in {execution_time:.3f}s"],
            )
    except Exception as e:
        execution_time = time.time() - start_time
        return NodeResult(
            error=str(e),
            metadata={"execution_time": execution_time, "error_type": type(e).__name__},
            logs=[f"Node execution failed after {execution_time:.3f}s: {str(e)}"],
        )

