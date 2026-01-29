import asyncio
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from spoon_ai.callbacks.base import BaseCallbackHandler
from spoon_ai.schema import Message


class CallbackManager:
    """Lightweight dispatcher for callback handlers."""

    def __init__(self, handlers: Optional[List[BaseCallbackHandler]] = None):
        self.handlers: List[BaseCallbackHandler] = list(handlers or [])

    @classmethod
    def from_callbacks(cls,callbacks: Union[None,BaseCallbackHandler,List[BaseCallbackHandler],"CallbackManager",],
    ) -> "CallbackManager":
        if callbacks is None:
            return cls()
        if isinstance(callbacks, cls):
            return cls(callbacks.handlers)
        if isinstance(callbacks, BaseCallbackHandler):
            return cls([callbacks])
        if isinstance(callbacks, list):
            valid = [handler for handler in callbacks if isinstance(handler, BaseCallbackHandler)]
            return cls(valid)
        return cls()

    def merge(self,other: Union[BaseCallbackHandler,List[BaseCallbackHandler],"CallbackManager",],
    ) -> "CallbackManager":
        merged = CallbackManager.from_callbacks(other)
        return CallbackManager(self.handlers + merged.handlers)

    async def _dispatch(self, event: str, **kwargs: Any) -> None:
        if not self.handlers:
            return
        tasks = [self._invoke(handler, event, **kwargs) for handler in self.handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    async def _invoke(handler: BaseCallbackHandler, event: str, **kwargs: Any) -> None:
        callback = getattr(handler, event, None)
        if callback is None:
            return
        if asyncio.iscoroutinefunction(callback):
            await callback(**kwargs)
            return
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: callback(**kwargs))

    async def on_llm_start(self,run_id: UUID,messages: List[Message],**kwargs: Any,) -> None:
        await self._dispatch("on_llm_start", run_id=run_id, messages=messages, **kwargs)

    async def on_llm_new_token(self,token: str,*,chunk: Optional[Any] = None,run_id: UUID = None,**kwargs: Any,) -> None:
        await self._dispatch("on_llm_new_token",token=token,chunk=chunk,run_id=run_id,**kwargs,)

    async def on_llm_end(self,response: Any,*,run_id: UUID,**kwargs: Any,) -> None:
        await self._dispatch("on_llm_end", response=response, run_id=run_id, **kwargs)

    async def on_llm_error(self,error: Exception,*,run_id: UUID,**kwargs: Any,) -> None:
        await self._dispatch("on_llm_error", error=error, run_id=run_id, **kwargs)

    async def on_tool_start(self,tool_name: str,tool_input: Dict[str, Any],*,run_id: UUID,**kwargs: Any,) -> None:
        await self._dispatch("on_tool_start",tool_name=tool_name,tool_input=tool_input,run_id=run_id,**kwargs,)

    async def on_tool_end(self,tool_name: str,tool_output: Any,*,run_id: UUID,**kwargs: Any,) -> None:
        await self._dispatch("on_tool_end",tool_name=tool_name,tool_output=tool_output,run_id=run_id,**kwargs,)

    async def on_tool_error(self,error: Exception,*,run_id: UUID,**kwargs: Any,) -> None:
        await self._dispatch("on_tool_error", error=error, run_id=run_id, **kwargs)

    async def on_retriever_start(self,run_id: UUID,query: Any,**kwargs: Any,) -> None:
        await self._dispatch("on_retriever_start", run_id=run_id, query=query, **kwargs)

    async def on_retriever_end(self,run_id: UUID,documents: Any,**kwargs: Any,) -> None:
        await self._dispatch("on_retriever_end", run_id=run_id, documents=documents, **kwargs)

    async def on_prompt_start(self,run_id: UUID,inputs: Any,**kwargs: Any,) -> None:
        await self._dispatch("on_prompt_start", run_id=run_id, inputs=inputs, **kwargs)

    async def on_prompt_end(self,run_id: UUID,output: Any,**kwargs: Any,) -> None:
        await self._dispatch("on_prompt_end", run_id=run_id, output=output, **kwargs)

AsyncCallbackManager = CallbackManager
