"""
Runnable interface and utilities for composable AI components.

This module provides the foundational Runnable interface that all Spoon AI
components implement, enabling streaming, composition, and standardized execution.
"""

from spoon_ai.runnables.base import (Runnable,RunnableConfig,RunLogPatch,RunLogState,log_patches_from_events)
from spoon_ai.runnables.events import (
    StreamEvent,
    StreamEventType,
    StreamEventBuilder,
)

__all__ = [
    "Runnable",
    "RunnableConfig",
    "RunLogPatch",
    "RunLogState",
    "log_patches_from_events",
    "StreamEvent",
    "StreamEventType",
    "StreamEventBuilder",
]

