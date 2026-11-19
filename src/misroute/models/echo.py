"""Offline, deterministic model for tests and demos. Costs nothing, needs no network."""
from __future__ import annotations

from .base import Message


class EchoModel:
    def __init__(self, name: str = "echo", **_: object):
        self.name = name

    def complete(self, messages: list[Message], *, system: str | None = None,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        agent = "unknown"
        if system and "(id: " in system:
            agent = system.split("(id: ", 1)[1].split(")", 1)[0]
        return f"[{agent}] handled: {messages[-1]['content']}"
