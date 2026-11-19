"""Start the MCP servers in .mcp.json, list their tools, and optionally make one real call.

  python scripts/check_tools.py                 # all servers
  python scripts/check_tools.py fred --smoke    # also fetch a real series / filing
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from misroute.tools.mcp_hub import ToolHub, load_mcp_config

SMOKE = {  # one cheap, read-only call per server: (tool name contains, arguments)
    "fred": ("search", {"search_text": "consumer price index"}),
    "edgartools": ("company", {"identifier": "AAPL"}),
    "alphavantage": ("tool_call", {"tool_name": "GLOBAL_QUOTE", "arguments": {"symbol": "IBM"}}),
    "catalogue": ("find_source", {"keyword": "filings"}),
    "dbnomics": ("get_series", {"provider": "ECB", "dataset": "ICP", "series": "M.U2.N.000000.4.ANR", "last_n": 3}),
    "arxiv": ("get_paper", {"arxiv_id": "2503.13657"}),
    "sanctions": ("list_status", {}),
    "companies_house": ("search_companies", {"query": "Tesco", "limit": 2}),
    "backtest": ("list_backtests", {}),
    "news": ("company_news", {"symbol": "NKE", "days": 7, "limit": 3}),
    "finnhub": ("stock_market_data", {"operation": "get_quote", "symbol": "AAPL"}),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("servers", nargs="*")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    cfg = load_mcp_config()
    names = args.servers or list(cfg)
    with ToolHub(cfg) as hub:
        hub.start(names)
        for n in names:
            if n in hub.errors:
                print(f"✗ {n}: {hub.errors[n]}")
                continue
            specs = hub.specs([n])
            print(f"✓ {n}: {len(specs)} tools")
            for s in specs:
                print(f"    {s.name:48} {s.description.splitlines()[0][:70] if s.description else ''}")
            if args.smoke and n in SMOKE:
                hint, a = SMOKE[n]
                spec = next((s for s in specs if hint in s.tool.lower()), None)
                if spec:
                    props = spec.input_schema.get("properties", {})
                    a = {k: v for k, v in a.items() if k in props} or a
                    print(f"  smoke {spec.name}({a}):\n    " + hub.call(spec.name, a)[:400].replace("\n", "\n    "))


if __name__ == "__main__":
    main()
