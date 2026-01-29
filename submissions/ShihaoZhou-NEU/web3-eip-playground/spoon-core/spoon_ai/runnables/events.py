from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict
from uuid import UUID


class StreamEventType(str, Enum):
    ON_CHAIN_START = "on_chain_start"
    ON_CHAIN_STREAM = "on_chain_stream"
    ON_CHAIN_END = "on_chain_end"
    ON_CHAIN_ERROR = "on_chain_error"
    ON_LLM_START = "on_llm_start"
    ON_LLM_STREAM = "on_llm_stream"
    ON_LLM_END = "on_llm_end"
    ON_LLM_ERROR = "on_llm_error"
    ON_CHAT_MODEL_START = "on_chat_model_start"
    ON_CHAT_MODEL_STREAM = "on_chat_model_stream"
    ON_CHAT_MODEL_END = "on_chat_model_end"
    ON_CHAT_MODEL_ERROR = "on_chat_model_error"
    ON_TOOL_START = "on_tool_start"
    ON_TOOL_END = "on_tool_end"
    ON_TOOL_ERROR = "on_tool_error"
    ON_RETRIEVER_START = "on_retriever_start"
    ON_RETRIEVER_END = "on_retriever_end"
    ON_PROMPT_START = "on_prompt_start"
    ON_PROMPT_END = "on_prompt_end"
    ON_CUSTOM_EVENT = "on_custom_event"


class StreamEvent(TypedDict, total=False):
    event: str
    name: str
    run_id: str
    parent_ids: List[str]
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    tags: List[str]
    timestamp: str


class StreamEventBuilder:
    @staticmethod
    def chain_start(
        run_id: UUID,
        name: str,
        inputs: Any,
        **kwargs: Any,
    ) -> StreamEvent:
        """Build chain start event."""
        return StreamEvent(
            event=StreamEventType.ON_CHAIN_START.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={"inputs": inputs},
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat(),
        )
    
    @staticmethod
    def chain_stream(
        run_id: UUID,
        name: str,
        chunk: Any,
        **kwargs: Any,
    ) -> StreamEvent:
        """Build chain stream event."""
        return StreamEvent(
            event=StreamEventType.ON_CHAIN_STREAM.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={"chunk": chunk},
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat(),
        )
    
    @staticmethod
    def chain_end(
        run_id: UUID,
        name: str,
        output: Any,
        **kwargs: Any,
    ) -> StreamEvent:
        """Build chain end event."""
        return StreamEvent(
            event=StreamEventType.ON_CHAIN_END.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={"output": output},
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat(),
        )
    
    @staticmethod
    def chain_error(
        run_id: UUID,
        name: str,
        error: Exception,
        **kwargs: Any,
    ) -> StreamEvent:
        """Build chain error event."""
        return StreamEvent(
            event=StreamEventType.ON_CHAIN_ERROR.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={
                "error": str(error),
                "error_type": type(error).__name__,
            },
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat(),
        )
    
    @staticmethod
    def llm_start(
        run_id: UUID,
        name: str,
        messages: List[Any],
        **kwargs: Any
    ) -> StreamEvent:
        return StreamEvent(
            event=StreamEventType.ON_LLM_START.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={
                "messages": messages,
                **kwargs
            },
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def llm_stream(
        run_id: UUID,
        name: str,
        token: str,
        chunk: Optional[Any] = None,
        **kwargs: Any
    ) -> StreamEvent:
        """Build LLM stream event."""
        data = {"token": token}
        if chunk is not None:
            data["chunk"] = chunk
        data.update(kwargs)
        
        return StreamEvent(
            event=StreamEventType.ON_LLM_STREAM.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data=data,
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def llm_end(
        run_id: UUID,
        name: str,
        response: Any,
        **kwargs: Any
    ) -> StreamEvent:
        return StreamEvent(
            event=StreamEventType.ON_LLM_END.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={
                "response": response,
                **kwargs
            },
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def tool_start(
        run_id: UUID,
        name: str,
        tool_input: Dict[str, Any],
        **kwargs: Any
    ) -> StreamEvent:
        return StreamEvent(
            event=StreamEventType.ON_TOOL_START.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={
                "input": tool_input,
                **kwargs
            },
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def tool_end(
        run_id: UUID,
        name: str,
        tool_output: Any,
        **kwargs: Any
    ) -> StreamEvent:
        return StreamEvent(
            event=StreamEventType.ON_TOOL_END.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={
                "output": tool_output,
                **kwargs
            },
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat()
        )

    @staticmethod
    def retriever_start(
        run_id: UUID,
        name: str,
        query: Any,
        **kwargs: Any,
    ) -> StreamEvent:
        return StreamEvent(
            event=StreamEventType.ON_RETRIEVER_START.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={"input": query, **kwargs},
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat(),
        )

    @staticmethod
    def retriever_end(
        run_id: UUID,
        name: str,
        documents: Any,
        **kwargs: Any,
    ) -> StreamEvent:
        return StreamEvent(
            event=StreamEventType.ON_RETRIEVER_END.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={"output": documents, **kwargs},
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat(),
        )

    @staticmethod
    def prompt_start(
        run_id: UUID,
        name: str,
        inputs: Any,
        **kwargs: Any,
    ) -> StreamEvent:
        return StreamEvent(
            event=StreamEventType.ON_PROMPT_START.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={"input": inputs, **kwargs},
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat(),
        )

    @staticmethod
    def prompt_end(
        run_id: UUID,
        name: str,
        output: Any,
        **kwargs: Any,
    ) -> StreamEvent:
        return StreamEvent(
            event=StreamEventType.ON_PROMPT_END.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={"output": output, **kwargs},
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat(),
        )
    
    @staticmethod
    def error(
        event_type: StreamEventType,
        run_id: UUID,
        name: str,
        error: Exception,
        **kwargs: Any
    ) -> StreamEvent:
        return StreamEvent(
            event=event_type.value,
            name=name,
            run_id=str(run_id),
            parent_ids=_get_parent_ids(kwargs),
            data={
                "error": str(error),
                "error_type": type(error).__name__,
                **kwargs
            },
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", []),
            timestamp=datetime.now().isoformat()
        )


def _get_parent_ids(kwargs: Dict[str, Any]) -> List[str]:
    """Normalize parent identifiers to a list of strings."""
    parent_ids = kwargs.get("parent_ids")
    if parent_ids is None:
        parent = kwargs.get("parent_run_id")
        if parent is None:
            return []
        parent_ids = [parent]
    if isinstance(parent_ids, (UUID, str)):
        parent_ids = [parent_ids]
    normalized: List[str] = []
    for pid in parent_ids:
        if pid is None:
            continue
        if isinstance(pid, UUID):
            normalized.append(str(pid))
        else:
            normalized.append(str(pid))
    return normalized
