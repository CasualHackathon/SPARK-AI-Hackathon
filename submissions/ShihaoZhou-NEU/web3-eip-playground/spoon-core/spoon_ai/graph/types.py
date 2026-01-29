"""
Typed structures for the graph package.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class NodeContext:
    node_name: str
    iteration: int
    thread_id: str
    execution_time: float = 0.0
    start_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_context: Optional['NodeContext'] = None
    execution_path: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()


@dataclass
class NodeResult:
    updates: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    goto: Optional[str] = None
    error: Optional[str] = None
    confidence: float = 1.0
    reasoning: Optional[str] = None


@dataclass
class RouterResult:
    next_node: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    alternative_paths: List[Tuple[str, float]] = field(default_factory=list)


@dataclass
class ParallelBranchConfig:
    branch_name: str
    nodes: List[str]
    join_strategy: str = "all_complete"
    timeout: Optional[float] = None
    join_condition: Optional[callable] = None
    error_strategy: str = "fail_fast"


@dataclass
class Command:
    update: Optional[Dict[str, Any]] = None
    goto: Optional[str] = None
    resume: Optional[Any] = None


@dataclass
class StateSnapshot:
    values: Dict[str, Any]
    next: Tuple[str, ...]
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    parent_config: Optional[Dict[str, Any]] = None
    tasks: Tuple[Any, ...] = field(default_factory=tuple)


@dataclass
class CheckpointTuple:
    config: Dict[str, Any]
    checkpoint: Dict[str, Any]
    metadata: Dict[str, Any]
    parent_config: Optional[Dict[str, Any]]
    pending_writes: List[Any] = field(default_factory=list)
