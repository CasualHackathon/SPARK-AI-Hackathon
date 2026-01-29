"""
In-memory checkpointer for the graph package.
"""
from typing import Any, Dict, Iterable, List, Optional
from datetime import datetime
from .types import StateSnapshot, CheckpointTuple
from .exceptions import CheckpointError


class InMemoryCheckpointer:
    def __init__(self, max_checkpoints_per_thread: int = 100, *, max_threads: int | None = None, ttl_seconds: int | None = None):
        self.checkpoints: Dict[str, List[StateSnapshot]] = {}
        self.max_checkpoints_per_thread = max_checkpoints_per_thread
        self.max_threads = max_threads
        self.ttl_seconds = ttl_seconds
        self.last_access: Dict[str, datetime] = {}

    def _gc(self) -> None:
        # TTL-based cleanup
        if self.ttl_seconds is not None:
            cutoff = datetime.now().timestamp() - self.ttl_seconds
            remove_keys = []
            for tid, snaps in self.checkpoints.items():
                # remove snapshots older than TTL
                kept = [s for s in snaps if s.created_at.timestamp() >= cutoff]
                if kept:
                    self.checkpoints[tid] = kept[-self.max_checkpoints_per_thread:]
                else:
                    remove_keys.append(tid)
            for tid in remove_keys:
                self.checkpoints.pop(tid, None)
                self.last_access.pop(tid, None)
        # Global thread limit
        if self.max_threads is not None and len(self.checkpoints) > self.max_threads:
            # evict least recently used threads by last_access
            sorted_threads = sorted(self.last_access.items(), key=lambda kv: kv[1])
            to_evict = len(self.checkpoints) - self.max_threads
            for tid, _ in sorted_threads[:to_evict]:
                self.checkpoints.pop(tid, None)
                self.last_access.pop(tid, None)

    @staticmethod
    def _checkpoint_id(snapshot: StateSnapshot) -> str:
        return snapshot.metadata.get("checkpoint_id") or str(snapshot.created_at.timestamp())

    @staticmethod
    def _snapshot_to_tuple(snapshot: StateSnapshot) -> CheckpointTuple:
        checkpoint_id = snapshot.metadata.get("checkpoint_id") or str(snapshot.created_at.timestamp())
        checkpoint_payload: Dict[str, Any] = {
            "id": checkpoint_id,
            "ts": snapshot.created_at.isoformat(),
            "values": snapshot.values,
            "next": list(snapshot.next),
        }
        return CheckpointTuple(
            config=snapshot.config or {},
            checkpoint=checkpoint_payload,
            metadata=snapshot.metadata,
            parent_config=snapshot.parent_config,
            pending_writes=[],
        )

    def save_checkpoint(self, thread_id: str, snapshot: StateSnapshot) -> None:
        try:
            if not thread_id:
                raise CheckpointError("Thread ID cannot be empty", operation="save")
            # update access time and run GC
            self.last_access[thread_id] = datetime.now()
            if thread_id not in self.checkpoints:
                self.checkpoints[thread_id] = []
            self.checkpoints[thread_id].append(snapshot)
            if len(self.checkpoints[thread_id]) > self.max_checkpoints_per_thread:
                self.checkpoints[thread_id] = self.checkpoints[thread_id][-self.max_checkpoints_per_thread:]
            self._gc()
        except Exception as e:
            raise CheckpointError(f"Failed to save checkpoint: {str(e)}", thread_id=thread_id, operation="save") from e

    def get_checkpoint(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[StateSnapshot]:
        try:
            if not thread_id:
                raise CheckpointError("Thread ID cannot be empty", operation="get")
            if thread_id not in self.checkpoints:
                return None
            self.last_access[thread_id] = datetime.now()
            checkpoints = self.checkpoints[thread_id]
            if not checkpoints:
                return None
            if checkpoint_id:
                for checkpoint in checkpoints:
                    if self._checkpoint_id(checkpoint) == checkpoint_id:
                        return checkpoint
                return None
            return checkpoints[-1]
        except Exception as e:
            raise CheckpointError(
                f"Failed to get checkpoint: {str(e)}",
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                operation="get",
            ) from e

    def get_checkpoint_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        if not isinstance(config, dict):
            raise CheckpointError("config must be a dictionary", operation="get_tuple")

        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id")
        checkpoint_id = configurable.get("checkpoint_id")

        if not thread_id:
            raise CheckpointError("thread_id is required", operation="get_tuple")

        snapshot = self.get_checkpoint(thread_id, checkpoint_id)
        if not snapshot:
            return None

        return self._snapshot_to_tuple(snapshot)

    def list_checkpoints(self, thread_id: str) -> List[StateSnapshot]:
        try:
            if not thread_id:
                raise CheckpointError("Thread ID cannot be empty", operation="list")
            self.last_access[thread_id] = datetime.now()
            return self.checkpoints.get(thread_id, [])
        except Exception as e:
            raise CheckpointError(f"Failed to list checkpoints: {str(e)}", thread_id=thread_id, operation="list") from e

    def iter_checkpoint_history(self, config: Dict[str, Any]) -> Iterable[CheckpointTuple]:
        """Return checkpoint tuples for the specified thread, newest last."""
        if not isinstance(config, dict):
            raise CheckpointError("config must be a dictionary", operation="history_tuple")

        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id")
        if not thread_id:
            raise CheckpointError("thread_id is required", operation="history_tuple")

        snapshots = self.list_checkpoints(thread_id)
        return [self._snapshot_to_tuple(snapshot) for snapshot in snapshots]

    def clear_thread(self, thread_id: str) -> None:
        if thread_id in self.checkpoints:
            del self.checkpoints[thread_id]
        if thread_id in self.last_access:
            del self.last_access[thread_id]
