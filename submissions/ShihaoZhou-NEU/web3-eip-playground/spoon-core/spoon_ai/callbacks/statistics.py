from __future__ import annotations

import time
from typing import Any, Callable, Optional
from uuid import UUID

from spoon_ai.callbacks.base import BaseCallbackHandler, LLMManagerMixin
from spoon_ai.schema import LLMResponse, LLMResponseChunk


class StreamingStatisticsCallback(BaseCallbackHandler, LLMManagerMixin):
    """Collect simple throughput statistics during streaming runs.

    By default, the callback prints summary metrics when the LLM finishes.
    Consumers can provide a custom ``print_fn`` to redirect output, or disable
    printing entirely and read the public attributes after execution.
    """

    def __init__(
        self,
        *,
        auto_print: bool = True,
        print_fn: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__()
        self.auto_print = auto_print
        self._print = print_fn or print
        self.reset()

    def reset(self) -> None:
        self.model: Optional[str] = None
        self.provider: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.token_count: int = 0
        self.chunk_count: int = 0
        self.last_response: Optional[LLMResponse] = None

    async def on_llm_start(
        self,
        run_id: UUID,
        messages: list[Any],
        *,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **_: Any,
    ) -> None:
        self.reset()
        self.model = model
        self.provider = provider
        self.start_time = time.perf_counter()
        if self.auto_print:
            self._print(
                f"\n Streaming started with {model or 'unknown model'}"
                f" ({provider or 'provider n/a'})"
            )

    async def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Optional[LLMResponseChunk] = None,
        run_id: Optional[UUID] = None,
        **_: Any,
    ) -> None:
        self.token_count += 1
        self.chunk_count += 1

    async def on_llm_end(
        self,
        response: LLMResponse,
        *,
        run_id: UUID,
        **_: Any,
    ) -> None:
        self.end_time = time.perf_counter()
        self.last_response = response
        if not self.auto_print:
            return

        duration = (self.end_time - self.start_time) if self.start_time else 0.0
        tokens_per_second = (
            (self.token_count / duration) if duration > 0 else float("inf")
        )

        self._print("\n\n Statistics:")
        self._print(f"   Total chunks: {self.chunk_count}")
        self._print(f"   Total tokens: {self.token_count}")
        self._print(f"   Duration: {duration:.2f}s")
        self._print(f"   Tokens/second: {tokens_per_second:.1f}")

        usage = response.usage or {}
        if usage:
            self._print(f"   Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            self._print(
                f"   Completion tokens: {usage.get('completion_tokens', 'N/A')}"
            )
            self._print(f"   Total tokens: {usage.get('total_tokens', 'N/A')}")

    async def on_llm_error(
        self,
        error: Exception,
        *,
        run_id: UUID,
        **_: Any,
    ) -> None:
        self.end_time = time.perf_counter()
        if self.auto_print:
            self._print(f"\n Streaming error: {error}")
