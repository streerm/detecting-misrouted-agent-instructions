"""The one interface every model adapter implements. Nothing else in the framework knows vendors."""
from __future__ import annotations

from typing import Literal, Protocol, TypedDict, runtime_checkable


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


@runtime_checkable
class ChatModel(Protocol):
    name: str

    def complete(self, messages: list[Message], *, system: str | None = None,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        """Return the assistant's text reply."""
        ...
