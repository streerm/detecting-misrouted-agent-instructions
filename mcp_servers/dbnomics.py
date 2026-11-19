"""DBnomics: macro series from ECB, Eurostat, BoE, OECD, IMF and ~90 other providers. No key.
API: https://api.db.nomics.world/v22 (docs: https://db.nomics.world/docs/web-api/)."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from _common import fetch_json, out

API = "https://api.db.nomics.world/v22"
mcp = FastMCP("dbnomics")


@mcp.tool()
def search_datasets(query: str, limit: int = 10) -> str:
    """Search datasets across all providers, e.g. 'euro area HICP'. Returns provider and dataset codes."""
    docs = fetch_json(f"{API}/search", {"q": query, "limit": min(limit, 25)})["results"]["docs"]
    return out("DBnomics", [{"provider": d["provider_code"], "dataset": d["code"], "name": d["name"],
                             "series": d.get("nb_series"), "updated_at": d.get("updated_at")} for d in docs])


@mcp.tool()
def search_series(provider: str, dataset: str, query: str = "", limit: int = 10) -> str:
    """Search the series inside one dataset, e.g. provider 'ECB', dataset 'ICP', query 'overall index annual rate'."""
    docs = fetch_json(f"{API}/series/{provider}/{dataset}", {"q": query or None, "limit": min(limit, 25)})["series"]["docs"]
    return out("DBnomics", [{"series": d["series_code"], "name": d["series_name"]} for d in docs])


@mcp.tool()
def get_series(provider: str, dataset: str, series: str, last_n: int = 24) -> str:
    """Observations for one series, most recent last. Example: ECB / ICP / M.U2.N.000000.4.ANR (euro-area HICP, annual rate)."""
    d = fetch_json(f"{API}/series/{provider}/{dataset}/{series}", {"observations": 1})["series"]["docs"][0]
    n = max(1, min(last_n, 600))
    obs = [{"period": p, "value": v} for p, v in zip(d["period"], d["value"])][-n:]
    return out(f"DBnomics {provider}/{dataset}/{series}",
               {"name": d["series_name"], "frequency": d.get("@frequency"), "indexed_at": d.get("indexed_at"),
                "last_period": obs[-1]["period"] if obs else None, "observations": obs})


if __name__ == "__main__":
    mcp.run()
