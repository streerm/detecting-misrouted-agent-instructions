"""OFAC sanctions screening against the US Treasury SDN list. No key.
Downloads the public SDN CSV once a day to ~/.cache/misroute-mcp. A name match is a lead to
check by hand, not a legal determination; no match is not clearance."""
from __future__ import annotations

import csv
import io
import re
import time

from mcp.server.fastmcp import FastMCP

from _common import CACHE, fetch, out

URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
FILE = CACHE / "sdn.csv"
mcp = FastMCP("sanctions")


def rows() -> tuple[list[list[str]], str]:
    if not FILE.exists() or time.time() - FILE.stat().st_mtime > 86400:
        CACHE.mkdir(parents=True, exist_ok=True)
        FILE.write_bytes(fetch(URL, timeout=120))
    as_of = time.strftime("%Y-%m-%d", time.gmtime(FILE.stat().st_mtime))
    return list(csv.reader(io.StringIO(FILE.read_text(encoding="latin-1")))), as_of


def tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def match(name: str, table: list[list[str]], limit: int) -> list[dict]:
    want = tokens(name)
    hits = []
    for r in table:
        if len(r) > 3 and want and want <= tokens(r[1]):
            hits.append({"uid": r[0], "name": r[1], "type": r[2].strip("- ") or "entity", "programs": r[3]})
    return hits[:limit]


@mcp.tool()
def screen_name(name: str, limit: int = 10) -> str:
    """Check a person or company name against the OFAC SDN list. Matches when every word of the
    name appears in a listed name. Returns list entries with their sanctions programmes."""
    table, as_of = rows()
    hits = match(name, table, min(limit, 50))
    return out(f"OFAC SDN list (downloaded {as_of})",
               {"query": name, "matches": hits, "note": "name match only; verify identity before relying on it"})


@mcp.tool()
def list_status() -> str:
    """How many entries the cached SDN list has and when it was downloaded."""
    table, as_of = rows()
    return out("OFAC SDN list", {"entries": len(table), "downloaded": as_of, "url": URL})


if __name__ == "__main__":
    mcp.run()
