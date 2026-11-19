"""News and management commentary: company news and earnings call transcripts.
Wraps two REST endpoints the desk already has keys for, so the news agent gets these tools
without also getting price and fundamentals tools:
  Finnhub company-news (FINNHUB_API_KEY) and Alpha Vantage EARNINGS_CALL_TRANSCRIPT
  (ALPHAVANTAGE_API_KEY; free key allows 25 requests a day and 1 a second).
Alpha Vantage NEWS_SENTIMENT is a premium endpoint (checked 19 Nov 2026), so there is no sentiment tool.
Read-only. Errors never include the request URL, because Alpha Vantage takes its key in the URL."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP

from _common import fetch_json, out

mcp = FastMCP("news")


def safe(source: str, fn):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001  (never echo the URL: it can hold a key)
        return out(source, {"error": type(e).__name__, "detail": getattr(e, "reason", None) or getattr(e, "code", None)})


def av(function: str, **params) -> dict:
    d = fetch_json("https://www.alphavantage.co/query",
                   {"function": function, "apikey": os.environ["ALPHAVANTAGE_API_KEY"], **params})
    for k in ("Information", "Note", "Error Message"):          # rate limit or bad request, sent as HTTP 200
        if k in d:
            return {"error": "alpha_vantage", "detail": str(d[k]).split("apikey")[0][:200]}
    return d


def shape_finnhub(items: list[dict], limit: int) -> list[dict]:
    rows = [{"date": datetime.fromtimestamp(i.get("datetime", 0), timezone.utc).strftime("%Y-%m-%d"),
             "headline": i.get("headline"), "source": i.get("source"), "url": i.get("url"),
             "summary": (i.get("summary") or "")[:300]} for i in items]
    return sorted(rows, key=lambda r: r["date"], reverse=True)[:limit]


def shape_transcript(d: dict, contains: str, max_chars: int) -> dict:
    turns = d.get("transcript") or []
    if contains:
        turns = [t for t in turns if contains.lower() in (t.get("content") or "").lower()]
    rows, used = [], 0
    for t in turns:
        text = t.get("content") or ""
        room = max_chars - used
        if room <= 0:
            break
        cut = len(text) > room
        used += min(len(text), room)
        rows.append({"speaker": t.get("speaker"), "title": t.get("title"),
                     "text": text[:room] + (" …[cut]" if cut else "")})
        if cut:
            break
    return {"symbol": d.get("symbol"), "quarter": d.get("quarter"), "turns_matching": len(turns),
            "turns_returned": len(rows), "truncated": len(rows) < len(turns) or any(r["text"].endswith("…[cut]") for r in rows),
            "turns": rows}


@mcp.tool()
def company_news(symbol: str, days: int = 30, limit: int = 20) -> str:
    """Dated, linked news headlines for one US-listed company over the last N days (Finnhub)."""
    def run():
        to, frm = date.today(), date.today() - timedelta(days=max(1, min(days, 365)))
        items = fetch_json("https://finnhub.io/api/v1/company-news", {"symbol": symbol.upper(), "from": frm, "to": to},
                           {"X-Finnhub-Token": os.environ["FINNHUB_API_KEY"]})
        return out("Finnhub company-news", {"symbol": symbol.upper(), "from": str(frm), "to": str(to),
                                            "items": shape_finnhub(items, min(limit, 50))})
    return safe("Finnhub company-news", run)


@mcp.tool()
def earnings_call_transcript(symbol: str, quarter: str, contains: str = "", max_chars: int = 12000) -> str:
    """Earnings call transcript for one fiscal quarter, speaker by speaker (Alpha Vantage).
    quarter is like '2026Q1' (the company's fiscal quarter). contains keeps only turns mentioning a word,
    e.g. 'margin' or 'guidance'. Text is verbatim; long calls are cut at max_chars and marked truncated."""
    def run():
        d = av("EARNINGS_CALL_TRANSCRIPT", symbol=symbol.upper(), quarter=quarter.upper())
        if "error" in d:
            return out("Alpha Vantage EARNINGS_CALL_TRANSCRIPT", d)
        return out("Alpha Vantage EARNINGS_CALL_TRANSCRIPT", shape_transcript(d, contains, max(1000, min(max_chars, 40000))))
    return safe("Alpha Vantage EARNINGS_CALL_TRANSCRIPT", run)


if __name__ == "__main__":
    mcp.run()
