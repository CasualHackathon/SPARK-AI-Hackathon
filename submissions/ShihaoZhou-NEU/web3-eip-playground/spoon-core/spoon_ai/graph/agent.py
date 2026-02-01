"""
GraphAgent implementation for the graph package.
"""
import asyncio
import time
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from .engine import StateGraph


@dataclass
class AgentStateCheckpoint:
    messages: List[Any]
    current_step: int
    agent_state: str
    preserved_state: Optional[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class Memory:
    """Memory implementation with persistent storage"""

    def __init__(self, storage_path: Optional[str] = None, session_id: Optional[str] = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.storage_path = Path(storage_path) if storage_path else Path.home() / ".spoon_ai" / "memory"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.session_file = self.storage_path / f"{self.session_id}.json"

        # Load existing data
        self.messages = []
        self.metadata = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Load memory data from disk"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = data.get('messages', [])
                    self.metadata = data.get('metadata', {})
        except Exception as e:
            print(f"Warning: Failed to load memory from disk: {e}")
            self.messages = []
            self.metadata = {}

    def _save_to_disk(self):
        """Save memory data to disk"""
        try:
            data = {
                'messages': self.messages,
                'metadata': self.metadata,
                'last_updated': datetime.now().isoformat(),
                'session_id': self.session_id
            }
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save memory to disk: {e}")

    def clear(self):
        """Clear all messages and reset memory"""
        self.messages = []
        self.metadata = {}
        self._save_to_disk()

    def add_message(self, msg):
        """Add a message to memory"""
        # Convert message to dict if it's an object
        if hasattr(msg, '__dict__'):
            msg_dict = msg.__dict__.copy()
        elif isinstance(msg, dict):
            msg_dict = msg.copy()
        else:
            msg_dict = {'content': str(msg)}

        # Add timestamp if not present
        if 'timestamp' not in msg_dict:
            msg_dict['timestamp'] = datetime.now().isoformat()

        self.messages.append(msg_dict)
        self._save_to_disk()

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages from memory"""
        if limit and len(self.messages) > limit:
            return self.messages[-limit:]
        return self.messages.copy()

    def get_recent_messages(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get messages from the last N hours"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_messages = []

        for msg in self.messages:
            if 'timestamp' in msg:
                try:
                    msg_time = datetime.fromisoformat(msg['timestamp']).timestamp()
                    if msg_time >= cutoff_time:
                        recent_messages.append(msg)
                except:
                    recent_messages.append(msg)
            else:
                recent_messages.append(msg)

        return recent_messages

    def search_messages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search messages containing the query"""
        query_lower = query.lower()
        matching_messages = []

        for msg in reversed(self.messages):  # Search from most recent
            content = str(msg.get('content', '')).lower()
            if query_lower in content:
                matching_messages.append(msg)
                if len(matching_messages) >= limit:
                    break

        return matching_messages

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'total_messages': len(self.messages),
            'session_id': self.session_id,
            'storage_path': str(self.storage_path),
            'last_updated': self.metadata.get('last_updated'),
            'file_size': self.session_file.stat().st_size if self.session_file.exists() else 0
        }

    def set_metadata(self, key: str, value: Any):
        """Set metadata"""
        self.metadata[key] = value
        self._save_to_disk()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata"""
        return self.metadata.get(key, default)


# Backward compatibility alias
class MockMemory(Memory):
    """Alias for backward compatibility - now uses persistent memory"""
    pass


class GraphAgent:
    def __init__(self, name: str, graph: StateGraph, preserve_state: bool = False, **kwargs):
        self.name = name
        self.graph = graph.compile()
        self.preserve_state = preserve_state
        self.memory = kwargs.get('memory')
        self.current_step = 0
        self.state = "IDLE"
        self._state_lock = asyncio.Lock()
        self._max_metadata_size = kwargs.get('max_metadata_size', 1024)
        self._last_state = None
        self.execution_metadata: Dict[str, Any] = {}

        # Initialize memory if none provided
        if self.memory is None:
            memory_path = kwargs.get('memory_path')
            session_id = kwargs.get('session_id', f"{name}_{int(time.time())}")
            self.memory = Memory(storage_path=memory_path, session_id=session_id)

    async def run(self, request: Optional[str] = None) -> str:
        async with self._state_lock:
            checkpoint = self._create_checkpoint()
            try:
                initial_state = {"input": request} if request else {}
                if self.preserve_state and self._last_state:
                    if self._validate_preserved_state(self._last_state):
                        initial_state.update(self._last_state)
                    else:
                        self._last_state = None
                result = await self.graph.invoke(initial_state)
                if self.preserve_state:
                    self._last_state = self._sanitize_preserved_state(result)
                self.execution_metadata = {
                    "execution_successful": True,
                    "execution_time": time.time(),
                    "last_request": request[:100] if request else None,
                }
                return str(result.get("output", result))
            except Exception as error:
                await self._handle_execution_error(error, checkpoint)
                raise

    def _create_checkpoint(self) -> AgentStateCheckpoint:
        messages = []
        if self.memory and hasattr(self.memory, 'get_messages'):
            try:
                messages = [m for m in self.memory.get_messages() if self._validate_message(m)]
            except Exception:
                messages = []
        return AgentStateCheckpoint(messages=messages, current_step=self.current_step, agent_state=self.state, preserved_state=self._last_state.copy() if self._last_state else None)

    async def _handle_execution_error(self, error: Exception, checkpoint: AgentStateCheckpoint):
        try:
            self._restore_from_checkpoint(checkpoint)
            self.execution_metadata = {
                "error": str(error)[:500],
                "error_type": type(error).__name__,
                "execution_successful": False,
                "execution_time": time.time(),
                "recovery_attempted": True,
            }
        except Exception:
            self._emergency_reset()
        self._safe_clear_preserved_state()

    def _restore_from_checkpoint(self, checkpoint: AgentStateCheckpoint):
        if not self.memory:
            return
        try:
            self.memory.clear()
            valid = []
            for msg in checkpoint.messages:
                if self._validate_message(msg):
                    valid.append(msg)
            for msg in valid:
                self.memory.add_message(msg)
            self.current_step = checkpoint.current_step
            self.state = checkpoint.agent_state
            if checkpoint.preserved_state and self._validate_preserved_state(checkpoint.preserved_state):
                self._last_state = checkpoint.preserved_state.copy()
            else:
                self._last_state = None
        except Exception:
            self._emergency_reset()

    def _validate_message(self, msg) -> bool:
        try:
            if not hasattr(msg, 'role') or not hasattr(msg, 'content'):
                return False
            if getattr(msg, 'role') not in ['user', 'assistant', 'tool', 'system']:
                return False
            if not isinstance(getattr(msg, 'content', None), (str, type(None))):
                return False
            return True
        except Exception:
            return False

    def _validate_preserved_state(self, state: Any) -> bool:
        try:
            if not isinstance(state, dict):
                return False
            if len(str(state)) > 10000:
                return False
            return True
        except Exception:
            return False

    def _sanitize_preserved_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not isinstance(state, dict):
                return {}
            sanitized: Dict[str, Any] = {}
            for k, v in state.items():
                if str(k).startswith('__'):
                    continue
                if isinstance(v, (str, int, float, bool, type(None))):
                    sanitized[k] = v
                elif isinstance(v, (list, dict)) and len(str(v)) <= 1000:
                    sanitized[k] = v
            return sanitized
        except Exception:
            return {}

    def _safe_clear_preserved_state(self):
        try:
            if self._last_state and not self._validate_preserved_state(self._last_state):
                self._last_state = None
        except Exception:
            self._last_state = None

    def _emergency_reset(self):
        try:
            if self.memory and hasattr(self.memory, 'clear'):
                self.memory.clear()
            self.current_step = 0
            self.state = "IDLE"
            self._last_state = None
            self.execution_metadata = {"emergency_reset": True, "timestamp": time.time()}
        except Exception:
            pass

    # Convenience APIs used by examples
    def clear_state(self):
        try:
            if self.memory and hasattr(self.memory, 'clear'):
                self.memory.clear()
        except Exception:
            pass
        self._last_state = None
        self.current_step = 0
        self.execution_metadata = {}

    def get_execution_metadata(self) -> Dict[str, Any]:
        try:
            return dict(self.execution_metadata) if isinstance(self.execution_metadata, dict) else {}
        except Exception:
            return {}

    def get_execution_history(self) -> List[Dict[str, Any]]:
        try:
            if hasattr(self.graph, 'execution_history'):
                return list(self.graph.execution_history)
        except Exception:
            pass
        return []

    # Enhanced memory methods using RealMemory features
    def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory for messages containing the query"""
        if hasattr(self.memory, 'search_messages'):
            return self.memory.search_messages(query, limit)
        return []

    def get_recent_memory(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent messages from memory"""
        if hasattr(self.memory, 'get_recent_messages'):
            return self.memory.get_recent_messages(hours)
        return []

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        if hasattr(self.memory, 'get_statistics'):
            return self.memory.get_statistics()
        return {}

    def set_memory_metadata(self, key: str, value: Any):
        """Set memory metadata"""
        if hasattr(self.memory, 'set_metadata'):
            self.memory.set_metadata(key, value)

    def get_memory_metadata(self, key: str, default: Any = None) -> Any:
        """Get memory metadata"""
        if hasattr(self.memory, 'get_metadata'):
            return self.memory.get_metadata(key, default)
        return default

    def save_session(self):
        """Manually save current session"""
        if hasattr(self.memory, '_save_to_disk'):
            self.memory._save_to_disk()

    def load_session(self, session_id: str):
        """Load a specific session"""
        if hasattr(self.memory, '__class__'):
            # Create new memory instance with the session
            memory_class = self.memory.__class__
            if memory_class == Memory or memory_class == MockMemory:
                old_session = self.memory.session_id
                storage_path = getattr(self.memory, "storage_path", None)
                new_memory = memory_class(
                    storage_path=str(storage_path) if storage_path else None,
                    session_id=session_id,
                )
                self.memory = new_memory
                print(f"Switched from session '{old_session}' to '{session_id}'")
            else:
                print(f"Memory type {memory_class} doesn't support session switching")

