"""The interface every model adapter implements. Nothing else in the framework knows vendors.

Neutral transcript format (adapters translate it):
  {"role": "user", "content": str}
  {"role": "assistant", "content": str, "tool_calls": [{"id", "name", "arguments"}]}   # tool_calls optional
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any, Protocol, runtime_checkable

from ..tools.types import ToolCall, ToolSpec, Turn

Message = dict[str, Any]


@runtime_checkable
class ChatModel(Protocol):
    name: str

    def complete(self, messages: list[Message], *, system: str | None = None,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        """Plain text in, text out. Required."""
        ...


def turn(model: ChatModel, messages: list[Message], *, system: str | None = None,
         tools: list[ToolSpec] | None = None, tool_mode: str | None = None) -> Turn:
    """One model step that may request tools.

    tool_mode: "native" uses the vendor's tool API (model.complete_turn);
               "json" uses a prompt protocol that works with ANY model, including small local ones.
    Default: native if the adapter supports it, else json.
    """
    if not tools:
        return Turn(text=model.complete(flatten(messages), system=system))
    mode = tool_mode or getattr(model, "tool_mode", None) or ("native" if hasattr(model, "complete_turn") else "json")
    if mode == "native":
        return model.complete_turn(messages, system=system, tools=tools)
    return _json_turn(model, messages, system, tools)


# ---- JSON fallback protocol ------------------------------------------------------------------
JSON_TOOL_INSTRUCTIONS = """
## Tools
You can call tools. To call one, reply with ONLY a JSON object on a single line:
{{"tool": "<tool name>", "arguments": {{...}}}}
You will then receive the result and may call another tool or give your final answer.
When you have the answer, reply in plain text (no JSON object).

Available tools:
{catalogue}
""".strip()


def tool_catalogue(tools: list[ToolSpec]) -> str:
    lines = []
    for t in tools:
        props = t.input_schema.get("properties", {})
        req = set(t.input_schema.get("required", []))
        args = ", ".join(f"{k}{'' if k in req else '?'}: {v.get('type', 'any')}" for k, v in props.items())
        lines.append(f"- {t.name}({args}): {t.description[:300]}")
    return "\n".join(lines)


def flatten(messages: list[Message]) -> list[Message]:
    """Neutral transcript -> plain alternating user/assistant text (for json mode and complete())."""
    out: list[Message] = []
    for m in messages:
        if m["role"] == "tool":
            role, text = "user", f"TOOL RESULT ({m['name']}):\n{m['content']}"
        elif m["role"] == "assistant" and m.get("tool_calls"):
            c = m["tool_calls"][0]
            role, text = "assistant", json.dumps({"tool": c["name"], "arguments": c["arguments"]})
        else:
            role, text = m["role"], m["content"]
        if out and out[-1]["role"] == role:
            out[-1] = {"role": role, "content": out[-1]["content"] + "\n\n" + text}
        else:
            out.append({"role": role, "content": text})
    return out


def parse_json_tool_call(text: str, tools: list[ToolSpec]) -> ToolCall | None:
    names = {t.name for t in tools}
    for m in re.finditer(r"\{.*\}", text, re.S):
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("tool") in names:
            args = data.get("arguments") or {}
            return ToolCall(f"call_{uuid.uuid4().hex[:8]}", data["tool"], args if isinstance(args, dict) else {})
    return None


def _json_turn(model, messages, system, tools) -> Turn:
    sys = ((system or "") + "\n\n" + JSON_TOOL_INSTRUCTIONS.format(catalogue=tool_catalogue(tools))).strip()
    text = model.complete(flatten(messages), system=sys)
    call = parse_json_tool_call(text, tools)
    return Turn(text="" if call else text, tool_calls=[call] if call else [])
