import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID

from spoon_ai.callbacks.base import BaseCallbackHandler
from spoon_ai.runnables.events import StreamEvent, StreamEventBuilder, StreamEventType
from spoon_ai.utils.streaming import message_to_dict


class StreamEventCallbackHandler(BaseCallbackHandler):
    """Translate callback invocations into standardized stream events."""

    def __init__(
        self,
        event_queue: "asyncio.Queue[StreamEvent]",
        *,
        root_run_id: UUID,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._queue = event_queue
        self._root_run_id = root_run_id
        self._default_tags = list(tags or [])
        self._default_metadata = dict(metadata or {})

    async def on_llm_start(
        self,
        run_id: UUID,
        messages: List[Any],
        **kwargs: Any,
    ) -> None:
        name = self._resolve_name(kwargs.get("model"), kwargs.get("provider"), fallback="llm")
        serialized_messages = [message_to_dict(m) for m in messages]
        metadata = self._build_metadata(model=kwargs.get("model"), provider=kwargs.get("provider"))
        event = StreamEventBuilder.llm_start(
            run_id,
            name,
            serialized_messages,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Optional[Any] = None,
        run_id: UUID = None,
        **kwargs: Any,
    ) -> None:
        if run_id is None:
            return
        name = self._resolve_name(kwargs.get("model"), kwargs.get("provider"), fallback="llm")
        chunk_payload = chunk.model_dump() if hasattr(chunk, "model_dump") else chunk
        metadata = self._build_metadata(model=kwargs.get("model"), provider=kwargs.get("provider"))
        event = StreamEventBuilder.llm_stream(
            run_id,
            name,
            token=token,
            chunk=chunk_payload,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        name = self._resolve_name(kwargs.get("model"), kwargs.get("provider"), fallback="llm")
        metadata = self._build_metadata(model=kwargs.get("model"), provider=kwargs.get("provider"))
        payload = response.model_dump() if hasattr(response, "model_dump") else response
        event = StreamEventBuilder.llm_end(
            run_id,
            name,
            response=payload,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_llm_error(
        self,
        error: Exception,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        name = self._resolve_name(kwargs.get("model"), kwargs.get("provider"), fallback="llm")
        metadata = self._build_metadata(model=kwargs.get("model"), provider=kwargs.get("provider"))
        event = StreamEventBuilder.error(
            StreamEventType.ON_LLM_ERROR,
            run_id,
            name,
            error,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_tool_start(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        metadata = self._build_metadata(tool_name=tool_name)
        event = StreamEventBuilder.tool_start(
            run_id,
            tool_name,
            tool_input,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_tool_end(
        self,
        tool_name: str,
        tool_output: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        metadata = self._build_metadata(tool_name=tool_name)
        event = StreamEventBuilder.tool_end(
            run_id,
            tool_name,
            tool_output,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_tool_error(
        self,
        error: Exception,
        *,
        run_id: UUID,
        tool_name: str,
        **kwargs: Any,
    ) -> None:
        metadata = self._build_metadata(tool_name=tool_name)
        event = StreamEventBuilder.error(
            StreamEventType.ON_TOOL_ERROR,
            run_id,
            tool_name,
            error,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_retriever_start(
        self,
        run_id: UUID,
        query: Any,
        **kwargs: Any,
    ) -> None:
        name = kwargs.get("retriever_name") or "retriever"
        metadata = self._build_metadata(retriever=name)
        event = StreamEventBuilder.retriever_start(
            run_id,
            name,
            query=query,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_retriever_end(
        self,
        run_id: UUID,
        documents: Any,
        **kwargs: Any,
    ) -> None:
        name = kwargs.get("retriever_name") or "retriever"
        metadata = self._build_metadata(retriever=name)
        event = StreamEventBuilder.retriever_end(
            run_id,
            name,
            documents=documents,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_prompt_start(
        self,
        run_id: UUID,
        inputs: Any,
        **kwargs: Any,
    ) -> None:
        name = kwargs.get("prompt_name") or "prompt"
        metadata = self._build_metadata(prompt=name)
        event = StreamEventBuilder.prompt_start(
            run_id,
            name,
            inputs=inputs,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    async def on_prompt_end(
        self,
        run_id: UUID,
        output: Any,
        **kwargs: Any,
    ) -> None:
        name = kwargs.get("prompt_name") or "prompt"
        metadata = self._build_metadata(prompt=name)
        event = StreamEventBuilder.prompt_end(
            run_id,
            name,
            output=output,
            parent_ids=self._parent_ids(kwargs),
            metadata=metadata,
            tags=self._default_tags,
        )
        await self._queue.put(event)

    def _build_metadata(self, **overrides: Any) -> Dict[str, Any]:
        metadata = dict(self._default_metadata)
        for key, value in overrides.items():
            if value is None:
                continue
            if isinstance(value, dict):
                existing = metadata.get(key, {})
                if isinstance(existing, dict):
                    merged = dict(existing)
                    merged.update(value)
                    metadata[key] = merged
                else:
                    metadata[key] = value
            else:
                metadata.setdefault(key, value)
        return metadata

    def _parent_ids(self, kwargs: Dict[str, Any]) -> List[str]:
        parent_ids = kwargs.get("parent_ids")
        if parent_ids:
            return [str(pid) for pid in parent_ids]
        parent_run_id = kwargs.get("parent_run_id")
        if parent_run_id:
            return [str(parent_run_id)]
        return [str(self._root_run_id)]

    @staticmethod
    def _resolve_name(*candidates: Optional[str], fallback: str) -> str:
        for candidate in candidates:
            if candidate:
                return str(candidate)
        return fallback
