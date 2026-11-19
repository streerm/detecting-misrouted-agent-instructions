"""Vendor-neutral tool types. Adapters translate these to Anthropic / OpenAI formats."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    name: str                      # qualified: "<server>__<tool>", safe for every vendor
    description: str
    input_schema: dict[str, Any]
    server: str = ""
    tool: str = ""                 # the server's own tool name


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class Turn:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
