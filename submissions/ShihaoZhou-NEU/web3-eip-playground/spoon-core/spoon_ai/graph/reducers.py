"""Reducers and validators for the graph package."""

from datetime import datetime
from typing import Any, Dict, List, Set, Union

from spoon_ai.memory.remove_message import RemoveMessage, REMOVE_ALL_MESSAGES
from spoon_ai.schema import Message


def add_messages(existing: List[Any], new: List[Any]) -> List[Any]:
    if existing is None:
        existing = []
    if not new:
        return existing

    result: List[Any] = list(existing)
    for item in new:
        remove_id = _extract_remove_id(item)
        if remove_id is None:
            result.append(item)
            continue
        if remove_id == REMOVE_ALL_MESSAGES:
            result = []
            continue
        result = [msg for msg in result if _message_identifier(msg) != remove_id]
    return result


def _extract_remove_id(item: Any) -> Union[str, None]:
    if isinstance(item, RemoveMessage):
        return item.target_id
    if isinstance(item, dict) and item.get("type") == "remove":
        return item.get("target_id") or item.get("id")
    return None


def _message_identifier(message: Any) -> Union[str, None]:
    if isinstance(message, Message):
        return getattr(message, "id", None)
    if isinstance(message, dict):
        return message.get("id")
    return None


def merge_dicts(existing: Dict, new: Dict) -> Dict:
    if existing is None:
        return new or {}
    if new is None:
        return existing
    result = existing.copy()
    for key, value in new.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def append_history(existing: List, new: Dict) -> List:
    if existing is None:
        existing = []
    if new is None:
        return existing
    entry = {"timestamp": datetime.now().isoformat(), **new}
    return existing + [entry]


def union_sets(existing: Set, new: Set) -> Set:
    if existing is None:
        existing = set()
    if new is None:
        return existing
    return existing | new


def validate_range(min_val: float, max_val: float):
    def validator(value: float) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError(f"Value must be numeric, got {type(value)}")
        if not min_val <= value <= max_val:
            raise ValueError(f"Value {value} not in range [{min_val}, {max_val}]")
        return float(value)
    return validator


def validate_enum(allowed_values: List[Any]):
    def validator(value: Any) -> Any:
        if value not in allowed_values:
            raise ValueError(f"Value {value} not in allowed values: {allowed_values}")
        return value
    return validator

