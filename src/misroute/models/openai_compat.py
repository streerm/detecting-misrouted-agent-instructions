"""Any OpenAI-compatible chat endpoint: Ollama, vLLM, LM Studio, llama.cpp server, Together, Groq, OpenAI.

This is how Llama, Qwen, Mistral, DeepSeek etc. plug in: set base_url and model in configs/models.yaml.
Native tool calling where the server supports it; set `tool_mode: json` for models/servers that don't.
"""
from __future__ import annotations

import json
import os

from ..tools.types import ToolCall, ToolSpec, Turn
from .base import Message, flatten


def to_openai(messages: list[Message], system: str | None) -> list[dict]:
    out: list[dict] = [{"role": "system", "content": system}] if system else []
    for m in messages:
        if m["role"] == "tool":
            out.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
        elif m["role"] == "assistant" and m.get("tool_calls"):
            out.append({"role": "assistant", "content": m.get("content") or None, "tool_calls": [
                {"id": c["id"], "type": "function",
                 "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
                for c in m["tool_calls"]]})
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


class OpenAICompatModel:
    def __init__(self, name: str, model: str, base_url: str | None = None,
                 api_key_env: str | None = None, max_tokens: int = 2048,
                 tool_mode: str | None = None, **_: object):
        from openai import OpenAI  # lazy: optional dependency

        key = os.environ.get(api_key_env) if api_key_env else None
        self.name, self.model, self.max_tokens, self.tool_mode = name, model, max_tokens, tool_mode
        self._client = OpenAI(base_url=base_url, api_key=key or "not-needed")

    def complete(self, messages: list[Message], *, system: str | None = None,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        return self.complete_turn(flatten(messages), system=system, tools=[],
                                  temperature=temperature, max_tokens=max_tokens).text

    def complete_turn(self, messages: list[Message], *, system: str | None = None,
                      tools: list[ToolSpec], temperature: float = 0.0, max_tokens: int | None = None) -> Turn:
        kw = {"tools": [{"type": "function", "function": {"name": t.name, "description": t.description[:1024],
                                                          "parameters": t.input_schema}} for t in tools]} if tools else {}
        resp = self._client.chat.completions.create(model=self.model, messages=to_openai(messages, system),
                                                    temperature=temperature,
                                                    max_tokens=max_tokens or self.max_tokens, **kw)
        msg = resp.choices[0].message
        calls = []
        for c in msg.tool_calls or []:
            try:
                args = json.loads(c.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": c.function.arguments}
            calls.append(ToolCall(c.id, c.function.name, args if isinstance(args, dict) else {"value": args}))
        return Turn(msg.content or "", calls)
