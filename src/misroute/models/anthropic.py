"""Claude via the Anthropic SDK (pip install -e '.[anthropic]')."""
from __future__ import annotations

import os

from .base import Message


class AnthropicModel:
    def __init__(self, name: str, model: str, api_key_env: str = "ANTHROPIC_API_KEY",
                 max_tokens: int = 2048, **_: object):
        import anthropic  # lazy: optional dependency

        self.name, self.model, self.max_tokens = name, model, max_tokens
        self._client = anthropic.Anthropic(api_key=os.environ.get(api_key_env))

    def complete(self, messages: list[Message], *, system: str | None = None,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        resp = self._client.messages.create(
            model=self.model, system=system or "", messages=messages,
            temperature=temperature, max_tokens=max_tokens or self.max_tokens,
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
