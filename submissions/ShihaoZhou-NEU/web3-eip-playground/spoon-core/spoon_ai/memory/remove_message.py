"""Helpers for emitting message-removal directives."""

from typing import Any, Dict, Literal

from pydantic import BaseModel, Field, ConfigDict, model_validator


REMOVE_ALL_MESSAGES = "__remove_all_messages__"


class RemoveMessage(BaseModel):
    """Lightweight message that signals another message should be removed."""

    type: Literal["remove"] = Field(default="remove", init=False)
    target_id: str = Field(
        ...,
        alias="id",
        description="Identifier of the message to remove.",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _ensure_no_content(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "content" in values and values["content"] not in (None, "", []):
            raise ValueError("RemoveMessage does not support 'content'.")
        return values

    model_config = ConfigDict(populate_by_name=True, extra="allow")

