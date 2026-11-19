"""Shared helpers for the small local MCP servers in this folder. Standard library only."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path.home() / ".cache" / "misroute-mcp"
UA = "misroute-research-desk/0.1 (student research project)"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def fetch(url: str, params: dict | None = None, headers: dict | None = None, timeout: int = 30) -> bytes:
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (fixed https hosts only)
        return r.read()


def fetch_json(url: str, params: dict | None = None, headers: dict | None = None) -> dict:
    return json.loads(fetch(url, params, headers))


def out(source: str, data) -> str:
    """Every result carries its source and retrieval time (see skills/finance-research-rules)."""
    return json.dumps({"source": source, "retrieved_at": now(), "data": data}, ensure_ascii=False, default=str)
