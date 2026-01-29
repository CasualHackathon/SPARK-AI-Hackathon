"""Configuration primitives for the SpoonAI graph engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Router configuration
# ---------------------------------------------------------------------------


@dataclass
class RouterConfig:
    """Controls how the graph chooses the next node after each execution step."""

    allow_llm: bool = False
    allowed_targets: Optional[Sequence[str]] = None
    default_target: Optional[str] = None
    llm_timeout: float = 8.0
    enable_fallback_to_default: bool = True


# ---------------------------------------------------------------------------
# Parallel execution configuration
# ---------------------------------------------------------------------------


@dataclass
class ParallelRetryPolicy:
    """Retry policy for individual nodes inside a parallel group."""

    max_retries: int = 0
    backoff_initial: float = 0.5
    backoff_multiplier: float = 2.0
    backoff_max: float = 10.0

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            self.max_retries = 0
        if self.backoff_initial <= 0:
            self.backoff_initial = 0.5
        if self.backoff_multiplier < 1:
            self.backoff_multiplier = 1.5
        if self.backoff_max <= 0:
            self.backoff_max = 10.0


@dataclass
class ParallelGroupConfig:
    """Controls how a parallel group executes and aggregates results."""

    # Join strategy: "all" → all nodes must complete, "any" → first completes,
    # "quorum" → stop after quorum requirement is satisfied.
    join_strategy: str = "all"
    quorum: Optional[float] = None  # floats in (0, 1] treated as ratio, ints as absolute
    timeout: Optional[float] = None
    error_strategy: str = "fail_fast"  # fail_fast, collect_errors, ignore_errors
    retry_policy: ParallelRetryPolicy = field(default_factory=ParallelRetryPolicy)
    join_condition: Optional[Callable[[Dict[str, Any], List[str]], bool]] = None

    # Resource controls
    max_in_flight: Optional[int] = None
    rate_limit_per_second: Optional[float] = None

    # Circuit breaker: if failure count reaches threshold the group is disabled
    circuit_breaker_threshold: Optional[int] = None
    circuit_breaker_cooldown: float = 30.0

    def __post_init__(self) -> None:
        js = (self.join_strategy or "all").lower()
        if js in {"all_complete", "all"}:
            js = "all"
        elif js in {"any_first", "first", "any"}:
            js = "any"
        elif js.startswith("quorum_"):
            suffix = js.split("_", 1)[1]
            try:
                value = float(suffix)
            except ValueError:
                value = 0.5
            js = "quorum"
            self.quorum = value
        elif js != "quorum":
            js = "all"
        self.join_strategy = js

        if self.join_strategy == "quorum" and self.quorum is None:
            self.quorum = 0.5
        if isinstance(self.quorum, (int, float)):
            if self.quorum <= 0:
                self.quorum = None
        if self.max_in_flight is not None and self.max_in_flight < 1:
            self.max_in_flight = 1
        if self.rate_limit_per_second is not None and self.rate_limit_per_second <= 0:
            self.rate_limit_per_second = None
        if self.circuit_breaker_threshold is not None and self.circuit_breaker_threshold < 1:
            self.circuit_breaker_threshold = None
        if self.circuit_breaker_cooldown < 0:
            self.circuit_breaker_cooldown = 30.0


# ---------------------------------------------------------------------------
# Graph-wide configuration
# ---------------------------------------------------------------------------


Validator = Callable[[Dict[str, Any]], None]


@dataclass
class GraphConfig:
    """Top-level configuration applied to an entire graph instance."""

    max_iterations: int = 100
    router: RouterConfig = field(default_factory=RouterConfig)
    state_validators: List[Validator] = field(default_factory=list)
    parallel_groups: Dict[str, ParallelGroupConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_iterations <= 0:
            self.max_iterations = 1


