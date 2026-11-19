"""Any OpenAI-compatible chat endpoint: Ollama, vLLM, LM Studio, llama.cpp server, Together, Groq, OpenAI.

This is how Llama, Qwen, Mistral, DeepSeek etc. plug in: set base_url and model in configs/models.yaml.
"""
from __future__ import annotations

import os

from .base import Message


class OpenAICompatModel:
    def __init__(self, name: str, model: str, base_url: str | None = None,
                 api_key_env: str | None = None, max_tokens: int = 2048, **_: object):
        from openai import OpenAI  # lazy: optional dependency

        key = os.environ.get(api_key_env) if api_key_env else None
        self.name, self.model, self.max_tokens = name, model, max_tokens
        self._client = OpenAI(base_url=base_url, api_key=key or "not-needed")

    def complete(self, messages: list[Message], *, system: str | None = None,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
        resp = self._client.chat.completions.create(
            model=self.model, messages=msgs, temperature=temperature,
            max_tokens=max_tokens or self.max_tokens,
        )
        return resp.choices[0].message.content or ""
