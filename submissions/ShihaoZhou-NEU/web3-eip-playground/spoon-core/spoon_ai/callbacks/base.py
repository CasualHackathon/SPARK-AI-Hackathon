from __future__ import annotations

from abc import ABC
from typing import Any, List, Optional
from uuid import UUID

from spoon_ai.schema import LLMResponse, LLMResponseChunk, Message


class RetrieverManagerMixin:
    """Mixin providing retriever callback hooks."""

    def on_retriever_start(
        self,
        run_id: UUID,
        query: Any,
        **kwargs: Any,
    ) -> Any:
        """Run when a retriever begins execution."""

    def on_retriever_end(
        self,
        run_id: UUID,
        documents: Any,
        **kwargs: Any,
    ) -> Any:
        """Run when a retriever finishes successfully."""

    def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        """Run when a retriever raises an error."""


class LLMManagerMixin:
    """Mixin providing large language model callback hooks."""

    def on_llm_start(
        self,
        run_id: UUID,
        messages: List[Message],
        **kwargs: Any,
    ) -> Any:
        """Run when an LLM or chat model begins execution."""

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Optional[LLMResponseChunk] = None,
        run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Run for each streamed token emitted by an LLM."""

    def on_llm_end(
        self,
        response: LLMResponse,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        """Run when an LLM finishes successfully."""

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        """Run when an LLM raises an error."""


class ChainManagerMixin:
    """Mixin providing chain-level callback hooks."""

    def on_chain_start(
        self,
        run_id: UUID,
        inputs: Any,
        **kwargs: Any,
    ) -> Any:
        """Run when a chain (Runnable) starts executing."""

    def on_chain_end(
        self,
        run_id: UUID,
        outputs: Any,
        **kwargs: Any,
    ) -> Any:
        """Run when a chain finishes successfully."""

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        """Run when a chain raises an error."""


class ToolManagerMixin:
    """Mixin providing tool callback hooks."""

    def on_tool_start(
        self,
        tool_name: str,
        tool_input: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        """Run when a tool invocation begins."""

    def on_tool_end(
        self,
        tool_name: str,
        tool_output: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        """Run when a tool invocation succeeds."""

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        tool_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when a tool invocation raises an error."""


class PromptManagerMixin:
    """Mixin providing prompt template callback hooks."""

    def on_prompt_start(
        self,
        run_id: UUID,
        inputs: Any,
        **kwargs: Any,
    ) -> Any:
        """Run when a prompt template begins formatting."""

    def on_prompt_end(
        self,
        run_id: UUID,
        output: Any,
        **kwargs: Any,
    ) -> Any:
        """Run when a prompt template finishes formatting."""

    def on_prompt_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        """Run when prompt formatting raises an error."""


class BaseCallbackHandler(
    LLMManagerMixin,
    ChainManagerMixin,
    ToolManagerMixin,
    RetrieverManagerMixin,
    PromptManagerMixin,
    ABC,
):
    """Base class for SpoonAI callback handlers."""

    raise_error: bool = False
    """Whether to re-raise exceptions originating from callbacks."""

    run_inline: bool = False
    """Whether the callback prefers to run on the caller's event loop."""

    @property
    def ignore_llm(self) -> bool:
        """Return True to skip LLM callbacks."""
        return False

    @property
    def ignore_chain(self) -> bool:
        """Return True to skip chain callbacks."""
        return False

    @property
    def ignore_tool(self) -> bool:
        """Return True to skip tool callbacks."""
        return False

    @property
    def ignore_retriever(self) -> bool:
        """Return True to skip retriever callbacks."""
        return False

    @property
    def ignore_prompt(self) -> bool:
        """Return True to skip prompt callbacks."""
        return False


class AsyncCallbackHandler(BaseCallbackHandler):
    """Async version of the callback handler base class."""

    async def on_llm_start(
        self,
        run_id: UUID,
        messages: List[Message],
        **kwargs: Any,
    ) -> None:
        return None

    async def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Optional[LLMResponseChunk] = None,
        run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_llm_end(
        self,
        response: LLMResponse,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_tool_start(
        self,
        tool_name: str,
        tool_input: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_tool_end(
        self,
        tool_name: str,
        tool_output: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        tool_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_retriever_start(
        self,
        run_id: UUID,
        query: Any,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_retriever_end(
        self,
        run_id: UUID,
        documents: Any,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_prompt_start(
        self,
        run_id: UUID,
        inputs: Any,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_prompt_end(
        self,
        run_id: UUID,
        output: Any,
        **kwargs: Any,
    ) -> None:
        return None

    async def on_prompt_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        return None


CallbackHandlerLike = BaseCallbackHandler
