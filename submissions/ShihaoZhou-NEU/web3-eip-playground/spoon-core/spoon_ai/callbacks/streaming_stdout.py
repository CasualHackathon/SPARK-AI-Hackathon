import sys
from typing import Any
from uuid import UUID

from spoon_ai.callbacks.base import BaseCallbackHandler


class StreamingStdOutCallbackHandler(BaseCallbackHandler):
    """Callback handler that streams tokens to standard output."""
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Print token to stdout immediately.
            Args:
            token: The new token to print
            **kwargs: Additional context (ignored)
        """
        sys.stdout.write(token)
        sys.stdout.flush()
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Print newline after LLM completes.
        
        Args:
            response: The complete LLM response (ignored)
            **kwargs: Additional context (ignored)
        """
        sys.stdout.write("\n")
        sys.stdout.flush()




