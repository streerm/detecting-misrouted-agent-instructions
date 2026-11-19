"""Data catalogue: what data the desk has, how it is reached, and which agent may use it.
Reads configs/data_sources.yaml and agents/cards/*.yaml. No network."""
from __future__ import annotations

import yaml
from mcp.server.fastmcp import FastMCP

from _common import ROOT, out

mcp = FastMCP("catalogue")


def load() -> tuple[dict, dict]:
    sources = yaml.safe_load((ROOT / "configs/data_sources.yaml").read_text()) or {}
    cards = {p.stem: yaml.safe_load(p.read_text()) for p in sorted((ROOT / "agents/cards").glob("*.yaml"))}
    return sources, cards


def agents_for(source: str, cards: dict) -> list[str]:
    return [c["id"] for c in cards.values() if source in (c.get("context_scope") or {}).get("data_sources", [])]


@mcp.tool()
def list_sources() -> str:
    """List every data source the desk has, what it gives, and which agents are scoped to it."""
    sources, cards = load()
    return out("configs/data_sources.yaml", [
        {"id": k, "gives": v.get("gives"), "cost": v.get("cost"), "agents": agents_for(k, cards)}
        for k, v in sources.items()])


@mcp.tool()
def describe_source(source_id: str) -> str:
    """Full entry for one data source: what it gives, how it is connected, cost, and scoped agents."""
    sources, cards = load()
    if source_id not in sources:
        return out("configs/data_sources.yaml", {"error": f"unknown source {source_id}", "known": sorted(sources)})
    return out("configs/data_sources.yaml", {"id": source_id, **sources[source_id], "agents": agents_for(source_id, cards)})


@mcp.tool()
def find_source(keyword: str) -> str:
    """Find data sources whose description mentions a keyword, e.g. 'officers', 'CPI', 'filings'."""
    sources, cards = load()
    k = keyword.lower()
    hits = [{"id": i, "gives": v.get("gives"), "agents": agents_for(i, cards)}
            for i, v in sources.items() if k in i.lower() or k in str(v.get("gives", "")).lower()]
    return out("configs/data_sources.yaml", hits)


if __name__ == "__main__":
    mcp.run()
