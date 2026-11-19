"""Run MCP servers from .mcp.json and expose their tools to ANY model.

Claude Code reads the same .mcp.json, so humans-with-Claude and our experimental agents
(Llama, Qwen, ...) use identical servers. Each agent only sees the servers in its card's `tools:`.

Needs the optional extra:  pip install -e ".[mcp]"
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import threading
from pathlib import Path

from .. import REPO_ROOT
from ..env import expand, load_dotenv, missing_vars
from .types import ToolSpec

SEP = "__"


def load_mcp_config(path: str | Path = REPO_ROOT / ".mcp.json") -> dict[str, dict]:
    return json.loads(Path(path).read_text()).get("mcpServers", {})


def qualify(server: str, tool: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_-]", "_", f"{server}{SEP}{tool}")
    return name[:64]


class ToolHub:
    """Starts stdio MCP servers on a background event loop; call() is synchronous."""

    def __init__(self, config: dict[str, dict] | None = None, *, start_timeout: float = 180,
                 call_timeout: float = 120, max_result_chars: int = 20_000):
        load_dotenv()
        self.config = config if config is not None else load_mcp_config()
        self.start_timeout, self.call_timeout, self.max_chars = start_timeout, call_timeout, max_result_chars
        self._sessions: dict[str, object] = {}
        self._specs: dict[str, list[ToolSpec]] = {}
        self._by_name: dict[str, ToolSpec] = {}
        self.errors: dict[str, str] = {}
        self._loop = asyncio.new_event_loop()
        self._stop: asyncio.Event | None = None
        self._tasks: list[asyncio.Future] = []
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._run(self._init_stop())

    async def _init_stop(self):
        self._stop = asyncio.Event()

    def _run(self, coro, timeout=None):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)

    # ---- lifecycle -------------------------------------------------------------------------
    def start(self, servers: list[str]) -> dict[str, list[ToolSpec]]:
        """Start the named servers (idempotent). Failures are recorded in .errors, not raised."""
        for name in servers:
            if name in self._sessions or name in self.errors:
                continue
            if name not in self.config:
                self.errors[name] = "not in .mcp.json"
                continue
            cfg = self.config[name]
            missing = [v for x in cfg.get("env", {}).values() for v in missing_vars(str(x))]
            if missing:
                self.errors[name] = f"missing env vars {missing} (set them in .env)"
                continue
            ready: asyncio.Future = self._loop.create_future()
            self._tasks.append(asyncio.run_coroutine_threadsafe(self._serve(name, cfg, ready), self._loop))
            try:
                self._run(asyncio.wait_for(asyncio.shield(ready), self.start_timeout), self.start_timeout + 5)
            except Exception as e:  # noqa: BLE001
                self.errors[name] = f"failed to start: {type(e).__name__}: {e}"
        return {n: self._specs[n] for n in servers if n in self._specs}

    async def _serve(self, name: str, cfg: dict, ready: asyncio.Future):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        env = {**os.environ, **{k: expand(str(v)) for k, v in cfg.get("env", {}).items()}}
        params = StdioServerParameters(command=cfg["command"], args=[expand(a) for a in cfg.get("args", [])],
                                       env=env, cwd=cfg.get("cwd") or str(REPO_ROOT))
        try:
            async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
                await session.initialize()
                listed = await session.list_tools()
                specs = [ToolSpec(qualify(name, t.name), (t.description or "").strip(),
                                  t.inputSchema or {"type": "object", "properties": {}}, name, t.name)
                         for t in listed.tools]
                self._sessions[name], self._specs[name] = session, specs
                self._by_name.update({s.name: s for s in specs})
                if not ready.done():
                    ready.set_result(True)
                await self._stop.wait()
        except BaseException as e:  # noqa: BLE001
            if not ready.done():
                ready.set_exception(e if isinstance(e, Exception) else RuntimeError(repr(e)))

    def close(self) -> None:
        if self._stop is None or not self._loop.is_running():
            return
        self._loop.call_soon_threadsafe(self._stop.set)
        for t in self._tasks:
            try:
                t.result(10)
            except Exception:  # noqa: BLE001
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(5)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ---- use -------------------------------------------------------------------------------
    def specs(self, servers: list[str]) -> list[ToolSpec]:
        self.start(servers)
        return [s for n in servers for s in self._specs.get(n, [])]

    def call(self, qualified_name: str, arguments: dict) -> str:
        spec = self._by_name.get(qualified_name)
        if spec is None:
            return f"ERROR: unknown tool {qualified_name}"
        session = self._sessions[spec.server]
        try:
            res = self._run(session.call_tool(spec.tool, arguments or {}), self.call_timeout)
        except Exception as e:  # noqa: BLE001
            return f"ERROR: {type(e).__name__}: {e}"
        parts = []
        for c in res.content:
            parts.append(c.text if getattr(c, "type", "") == "text" else json.dumps(c.model_dump(), default=str))
        if getattr(res, "structuredContent", None) and not parts:
            parts.append(json.dumps(res.structuredContent, default=str))
        text = "\n".join(parts)
        if res.isError:
            text = "ERROR: " + text
        return text if len(text) <= self.max_chars else text[: self.max_chars] + "\n…[truncated]"
