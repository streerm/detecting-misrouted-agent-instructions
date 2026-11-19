"""Minimal stdio MCP server for tests: no network, deterministic."""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fake")


@mcp.tool()
def get_series(series_id: str) -> str:
    """Return a fake macro series."""
    return f"{series_id}: 2026-09=3.1, 2026-10=3.0"


@mcp.tool()
def fail() -> str:
    """Always errors."""
    raise ValueError("boom")


if __name__ == "__main__":
    mcp.run()
