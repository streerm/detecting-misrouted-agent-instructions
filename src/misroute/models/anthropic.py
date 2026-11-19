"""Claude via the Anthropic SDK (pip install -e '.[anthropic]'). Native tool use."""
from __future__ import annotations

import os

from ..tools.types import ToolCall, ToolSpec, Turn
from .base import Message, flatten


def to_anthropic(messages: list[Message]) -> list[dict]:
    out: list[dict] = []
    for m in messages:
        if m["role"] == "tool":
            block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif m["role"] == "assistant" and m.get("tool_calls"):
            blocks = ([{"type": "text", "text": m["content"]}] if m.get("content") else []) + [
                {"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["arguments"]}
                for c in m["tool_calls"]]
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


class AnthropicModel:
    def __init__(self, name: str, model: str, api_key_env: str = "ANTHROPIC_API_KEY",
                 max_tokens: int = 2048, tool_mode: str | None = None, **_: object):
        import anthropic  # lazy: optional dependency

        self.name, self.model, self.max_tokens, self.tool_mode = name, model, max_tokens, tool_mode
        self._client = anthropic.Anthropic(api_key=os.environ.get(api_key_env))

    def complete(self, messages: list[Message], *, system: str | None = None,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        return self.complete_turn(flatten(messages), system=system, tools=[],
                                  temperature=temperature, max_tokens=max_tokens).text

    def complete_turn(self, messages: list[Message], *, system: str | None = None,
                      tools: list[ToolSpec], temperature: float = 0.0, max_tokens: int | None = None) -> Turn:
        kw = {"tools": [{"name": t.name, "description": t.description[:1024], "input_schema": t.input_schema}
                        for t in tools]} if tools else {}
        resp = self._client.messages.create(model=self.model, system=system or "",
                                            messages=to_anthropic(messages), temperature=temperature,
                                            max_tokens=max_tokens or self.max_tokens, **kw)
        text = "".join(b.text for b in resp.content if b.type == "text")
        calls = [ToolCall(b.id, b.name, dict(b.input or {})) for b in resp.content if b.type == "tool_use"]
        return Turn(text, calls)
