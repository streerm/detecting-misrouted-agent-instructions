"""Build models by name from configs/models.yaml. Add a provider = one class + one line here."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..cards import load_yaml
from .base import ChatModel
from .echo import EchoModel


def _anthropic(**cfg):
    from .anthropic import AnthropicModel
    return AnthropicModel(**cfg)


def _openai_compat(**cfg):
    from .openai_compat import OpenAICompatModel
    return OpenAICompatModel(**cfg)


PROVIDERS: dict[str, Callable[..., ChatModel]] = {
    "echo": EchoModel,
    "anthropic": _anthropic,
    "openai_compat": _openai_compat,
}


class ModelRegistry:
    def __init__(self, config_path: str | Path):
        cfg = load_yaml(config_path)
        self.default: str = cfg.get("default", "echo")
        self.specs: dict[str, dict] = cfg.get("models", {})
        self._cache: dict[str, ChatModel] = {}

    def resolve(self, name: str) -> str:
        return self.default if name in (None, "", "default") else name

    def get(self, name: str = "default") -> ChatModel:
        name = self.resolve(name)
        if name not in self._cache:
            if name not in self.specs:
                raise KeyError(f"model '{name}' not in registry; known: {sorted(self.specs)}")
            spec = dict(self.specs[name])
            provider = spec.pop("provider")
            if provider not in PROVIDERS:
                raise KeyError(f"unknown provider '{provider}'; known: {sorted(PROVIDERS)}")
            self._cache[name] = PROVIDERS[provider](name=name, **spec)
        return self._cache[name]
