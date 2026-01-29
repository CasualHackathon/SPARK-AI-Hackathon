import asyncio
import logging
import queue
import threading
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime
from typing import (Any,AsyncIterator,Dict,Generic,Iterator,List,Optional,TypedDict,TypeVar,cast,)
from uuid import uuid4

from spoon_ai.callbacks.base import BaseCallbackHandler
from spoon_ai.callbacks.manager import CallbackManager
from spoon_ai.runnables.events import StreamEventBuilder

logger = logging.getLogger(__name__)

Input = TypeVar("Input")
Output = TypeVar("Output")


class RunnableConfig(TypedDict, total=False):
    callbacks: List[BaseCallbackHandler]
    tags: List[str]
    metadata: Dict[str, Any]
    run_name: str


class RunLogState(TypedDict, total=False):
    run_id: str
    name: str
    type: str
    status: str
    start_time: str
    end_time: Optional[str]
    metadata: Dict[str, Any]
    tags: List[str]
    parent_ids: List[str]
    inputs: Any
    last_chunk: Any
    final_output: Any
    streamed_output: List[Any]
    error: Dict[str, Any]
    history: List[Dict[str, Any]]


class RunLogPatch(TypedDict, total=False):
    run_id: str
    event: str
    timestamp: str
    delta: Dict[str, Any]
    state: RunLogState


def _infer_event_type(event_name: str) -> str:
    if not event_name:
        return "chain"
    lowered = event_name.lower()
    if "llm" in lowered:
        return "llm"
    if "chat_model" in lowered:
        return "chat_model"
    if "prompt" in lowered:
        return "prompt"
    if "tool" in lowered:
        return "tool"
    if "retriever" in lowered:
        return "retriever"
    return "chain"


def _infer_event_phase(event_name: str) -> str:
    if not event_name:
        return "update"
    if event_name.endswith("_start"):
        return "start"
    if event_name.endswith("_stream"):
        return "stream"
    if event_name.endswith("_end"):
        return "end"
    if event_name.endswith("_error"):
        return "error"
    return "update"


async def log_patches_from_events(
    event_iter: AsyncIterator[Dict[str, Any]],
    *,
    diff: bool = True,
) -> AsyncIterator[RunLogPatch]:
    """Convert a stream of events into run log patches."""

    def annotate_entry(event: Dict[str, Any]) -> RunLogState:
        run_id = event["run_id"]
        entry = logs.setdefault(
            run_id,
            RunLogState(
                run_id=run_id,
                name=event.get("name"),
                type=_infer_event_type(event.get("event", "")),
                status="pending",
                metadata=event.get("metadata", {}) or {},
                tags=list(event.get("tags", []) or []),
                parent_ids=list(event.get("parent_ids", []) or []),
                history=[],
            ),
        )
        entry["name"] = entry.get("name") or event.get("name")
        entry["type"] = entry.get("type") or _infer_event_type(event.get("event", ""))
        entry.setdefault("metadata", {}).update(event.get("metadata", {}) or {})
        if event.get("tags"):
            merged_tags = set(entry.get("tags", []))
            for tag in event["tags"]:
                merged_tags.add(tag)
            entry["tags"] = list(merged_tags)
        if event.get("parent_ids"):
            entry["parent_ids"] = list({*entry.get("parent_ids", []), *event["parent_ids"]})
        return entry

    def apply_event(entry: RunLogState, event: Dict[str, Any]) -> None:
        phase = _infer_event_phase(event.get("event", ""))
        data = event.get("data", {})
        entry_history = entry.setdefault("history", [])
        entry_history.append(
            {
                "event": event.get("event"),
                "timestamp": event.get("timestamp"),
                "data": data,
            }
        )
        if phase == "start":
            entry["status"] = "running"
            entry["start_time"] = event.get("timestamp")
            entry["inputs"] = data
            entry.pop("error", None)
            entry.pop("final_output", None)
        elif phase == "stream":
            entry["status"] = "running"
            chunk_value = data.get("chunk") or data.get("token")
            if chunk_value is not None:
                entry["last_chunk"] = chunk_value
                stream_list = entry.setdefault("streamed_output", [])
                stream_list.append(chunk_value)
        elif phase == "end":
            entry["status"] = "completed"
            entry["end_time"] = event.get("timestamp")
            entry["final_output"] = data.get("output") or data.get("response")
        elif phase == "error":
            entry["status"] = "error"
            entry["end_time"] = event.get("timestamp")
            entry["error"] = {
                "message": data.get("error"),
                "type": data.get("error_type"),
            }

    def snapshot(entry: RunLogState) -> RunLogState:
        captured = dict(entry)
        captured["metadata"] = deepcopy(entry.get("metadata", {}))
        captured["tags"] = list(entry.get("tags", []))
        captured["parent_ids"] = list(entry.get("parent_ids", []))
        if "streamed_output" in entry:
            captured["streamed_output"] = list(entry.get("streamed_output", []))
        captured["history"] = list(entry.get("history", []))
        return cast(RunLogState, captured)

    logs: Dict[str, RunLogState] = {}
    async for event in event_iter:
        entry = annotate_entry(event)
        apply_event(entry, event)
        patch_base: RunLogPatch = {
            "run_id": entry["run_id"],
            "event": event.get("event", "log"),
            "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
        }
        entry_snapshot = snapshot(entry)
        if diff:
            patch_base["delta"] = {
                "run_id": entry["run_id"],
                "event": event.get("event"),
                "status": entry.get("status"),
                "data": event.get("data"),
                "snapshot": entry_snapshot,
            }
        else:
            patch_base["state"] = entry_snapshot
        yield patch_base


class Runnable(ABC, Generic[Input, Output]):
    @abstractmethod
    async def ainvoke(self,input: Input,config: Optional[RunnableConfig] = None) -> Output:
        pass
    
    async def astream(self,input: Input,config: Optional[RunnableConfig] = None) -> AsyncIterator[Output]:
        # Default implementation - subclasses should override
        result = await self.ainvoke(input, config)
        yield result
    
    async def astream_log(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        *,
        diff: bool = True,
    ) -> AsyncIterator[RunLogPatch]:
        """Asynchronously stream structured log patches derived from execution events."""
        event_iter = self.astream_events(input, config)
        async for patch in log_patches_from_events(event_iter, diff=diff):
            yield patch
    
    async def astream_events(self,input: Input,config: Optional[RunnableConfig] = None) -> AsyncIterator[Dict[str, Any]]:
        """Asynchronously stream structured execution events."""
        merged_config: Dict[str, Any] = dict(config or {})
        tags = merged_config.get("tags", []) or []
        metadata = merged_config.get("metadata", {}) or {}
        
        run_id = uuid4()
        component_name = getattr(self, "name", self.__class__.__name__)

        event_queue: "asyncio.Queue[Optional[Dict[str, Any]]]" = asyncio.Queue()
        from spoon_ai.callbacks.stream_event import StreamEventCallbackHandler

        stream_handler = StreamEventCallbackHandler(
            event_queue,
            root_run_id=run_id,
            tags=tags,
            metadata=metadata,
        )

        callbacks: List[BaseCallbackHandler] = list(merged_config.get("callbacks", []) or [])
        callbacks.append(stream_handler)
        config_with_handler = dict(merged_config)
        config_with_handler["callbacks"] = callbacks
        
        def _serialize(value: Any) -> Any:
            if hasattr(value, "model_dump"):
                try:
                    return value.model_dump()
                except Exception:
                    return value
            return value

        async def consume_stream() -> None:
            last_chunk: Any = None
            try:
                async for chunk in self.astream(input, config_with_handler):
                    last_chunk = chunk
                    await event_queue.put(
                        StreamEventBuilder.chain_stream(
                            run_id,
                            component_name,
                            _serialize(chunk),
                            tags=tags,
                            metadata=metadata,
                        )
                    )
                await event_queue.put(
                    StreamEventBuilder.chain_end(
                        run_id,
                        component_name,
                        _serialize(last_chunk),
                        tags=tags,
                        metadata=metadata,
                    )
                )
            except Exception as error:
                exception_holder.append(error)
                await event_queue.put(
                    StreamEventBuilder.chain_error(
                        run_id,
                        component_name,
                        error,
                        tags=tags,
                        metadata=metadata,
                    )
                )
            finally:
                await event_queue.put(None)

        exception_holder: List[Exception] = []
        consumer_task = asyncio.create_task(consume_stream())

        yield StreamEventBuilder.chain_start(
            run_id,
            component_name,
            inputs={"input": _serialize(input)},
            tags=tags,
            metadata=metadata,
        )
        
        while True:
            event = await event_queue.get()
            if event is None:
                break
            yield event

        await consumer_task
        if exception_holder:
            raise exception_holder[0]
         
    def invoke(self,input: Input,config: Optional[RunnableConfig] = None) -> Output:
        return self._run_async(self.ainvoke(input, config))
    
    def stream(self,input: Input,config: Optional[RunnableConfig] = None) -> Iterator[Output]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            yield from self._stream_with_new_loop(input, config)
        else:
            yield from self._stream_in_thread(input, config)

    def _stream_with_new_loop(self,input: Input,config: Optional[RunnableConfig],) -> Iterator[Output]:
        async def run() -> List[Output]:
            return [chunk async for chunk in self.astream(input, config)]

        for chunk in asyncio.run(run()):
            yield chunk
    
    def _stream_in_thread(
        self,
        input: Input,
        config: Optional[RunnableConfig]
    ) -> Iterator[Output]:
        """Stream using a background thread (for nested loop scenarios)."""
        result_queue: queue.Queue = queue.Queue()
        exception_holder: List[Exception] = []
        
        def run_async_stream():
            """Run async stream in new thread with new event loop."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def _astream():
                    try:
                        async for chunk in self.astream(input, config):
                            result_queue.put(("chunk", chunk))
                    except Exception as e:
                        exception_holder.append(e)
                        result_queue.put(("error", e))
                    finally:
                        result_queue.put(("done", None))
                
                loop.run_until_complete(_astream())
                loop.close()
                
            except Exception as e:
                exception_holder.append(e)
                result_queue.put(("error", e))
        
        # Start background thread
        thread = threading.Thread(target=run_async_stream, daemon=True)
        thread.start()
        
        # Yield results from queue
        while True:
            msg_type, data = result_queue.get()
            
            if msg_type == "chunk":
                yield data
            elif msg_type == "done":
                break
            elif msg_type == "error":
                raise data
        
        thread.join(timeout=1.0)
        
        # Check for exceptions
        if exception_holder:
            raise exception_holder[0]
    
    def _run_async(self, coro):
        """Run async coroutine, handling nested event loops."""
        try:
            loop = asyncio.get_running_loop()
            # Already in event loop - need to use different approach
            logger.warning(
                "Calling synchronous invoke() from within an async context. "
                "Consider using ainvoke() instead."
            )
            
            # Use thread to run in separate loop
            result_holder = []
            exception_holder = []
            
            def run_in_thread():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(coro)
                    result_holder.append(result)
                    loop.close()
                except Exception as e:
                    exception_holder.append(e)
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
            if exception_holder:
                raise exception_holder[0]
            return result_holder[0]
            
        except RuntimeError:
            return asyncio.run(coro)
    
    def _get_callbacks(self,config: Optional[RunnableConfig] = None) -> CallbackManager:
        # Get instance-level callbacks
        instance_callbacks = getattr(self, 'callbacks', [])
        # Get config-level callbacks
        config_callbacks = []
        if config and 'callbacks' in config:
            config_callbacks = config['callbacks']
        # Merge using CallbackManager
        manager = CallbackManager.from_callbacks(instance_callbacks)
        if config_callbacks:
            manager = manager.merge(config_callbacks)
        
        return manager
