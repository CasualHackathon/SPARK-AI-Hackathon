"""
Memory helpers shared across Mem0 demos and utilities.
"""

from typing import Any, List, Optional

__all__ = ["extract_memories", "extract_first_memory_id"]


def _unwrap_output(result: Any) -> Any:
    """Extract the underlying payload from a ToolResult-like object or raw response."""
    if hasattr(result, "output"):
        return getattr(result, "output")
    return result


def extract_memories(result: Any) -> List[str]:
    """
    Normalize Mem0 search/get responses into a list of memory strings.
    Supports common shapes: {"memories": [...]}, {"results": [...]}, {"data": [...]}, list, or scalar.
    """
    data = _unwrap_output(result)
    if not data:
        return []

    if isinstance(data, dict):
        if isinstance(data.get("memories"), list):
            items = data.get("memories", [])
        elif isinstance(data.get("results"), list):
            items = data.get("results", [])
        elif isinstance(data.get("data"), list):
            items = data.get("data", [])
        else:
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]

    extracted: List[str] = []
    for item in items:
        if isinstance(item, str):
            extracted.append(item)
        elif isinstance(item, dict):
            text = item.get("memory") or item.get("text") or item.get("content") or item.get("value")
            if text:
                extracted.append(str(text))
    return extracted


def extract_first_memory_id(result: Any) -> Optional[str]:
    """
    Pull the first memory id from Mem0 responses.
    Supports common id fields: id, _id, memory_id, uuid.
    """
    data = _unwrap_output(result)
    if not data:
        return None

    candidates = []
    if isinstance(data, dict):
        if isinstance(data.get("results"), list):
            candidates = data["results"]
        elif isinstance(data.get("memories"), list):
            candidates = data["memories"]
        elif isinstance(data.get("data"), list):
            candidates = data["data"]
    elif isinstance(data, list):
        candidates = data

    for item in candidates:
        if isinstance(item, dict):
            mem_id = item.get("id") or item.get("_id") or item.get("memory_id") or item.get("uuid")
            if mem_id:
                return str(mem_id)
    return None
