"""Backtest runner: simple, transparent strategy backtests on a price series the caller supplies.
No network and no data of its own: prices must come from a data agent, with their dates, so the
log shows exactly which data a backtest saw (this is where lookahead bias would show up).
Results are saved under runs/backtests/ so they can be listed and re-read."""
from __future__ import annotations

import json
import math
import time

from mcp.server.fastmcp import FastMCP

from _common import ROOT, out

DIR = ROOT / "runs" / "backtests"
mcp = FastMCP("backtest")


def sma(xs: list[float], n: int, i: int) -> float | None:
    return sum(xs[i - n + 1:i + 1]) / n if i >= n - 1 else None


def stats(returns: list[float], periods_per_year: int) -> dict:
    if not returns:
        return {"periods": 0}
    equity, peak, max_dd = 1.0, 1.0, 0.0
    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        max_dd = max(max_dd, 1 - equity / peak)
    mean = sum(returns) / len(returns)
    sd = math.sqrt(sum((r - mean) ** 2 for r in returns) / max(len(returns) - 1, 1))
    return {"periods": len(returns), "total_return": round(equity - 1, 6),
            "annualised_return": round(equity ** (periods_per_year / len(returns)) - 1, 6),
            "annualised_volatility": round(sd * math.sqrt(periods_per_year), 6),
            "sharpe_zero_rf": round(mean / sd * math.sqrt(periods_per_year), 4) if sd else None,
            "max_drawdown": round(max_dd, 6)}


def run(closes: list[float], fast: int, slow: int, periods_per_year: int) -> dict:
    """Long when the fast average is above the slow one, flat otherwise. The signal from day t is
    traded on day t+1, so no return uses information from its own day."""
    strat, hold, position = [], [], 0
    for i in range(1, len(closes)):
        r = closes[i] / closes[i - 1] - 1
        hold.append(r)
        strat.append(r * position)
        f, s = sma(closes, fast, i), sma(closes, slow, i)
        position = int(f is not None and s is not None and f > s)
    return {"strategy": stats(strat[slow:], periods_per_year), "buy_and_hold": stats(hold[slow:], periods_per_year)}


@mcp.tool()
def run_sma_crossover(ticker: str, dates: list[str], closes: list[float], fast: int = 20, slow: int = 50,
                      periods_per_year: int = 252, data_source: str = "") -> str:
    """Backtest a moving-average crossover on supplied closing prices (oldest first, one date per price).
    Compares it with buy-and-hold over the same window. Ignores costs, slippage and dividends unless
    the prices are adjusted. data_source should say where the prices came from and their as-of date."""
    if len(dates) != len(closes) or len(closes) <= slow + 1 or not 0 < fast < slow:
        return out("backtest", {"error": "need one date per close, more than slow+1 prices, and 0 < fast < slow"})
    if dates != sorted(dates):
        return out("backtest", {"error": "dates must be oldest first"})
    result = {"id": f"{ticker.upper()}-sma{fast}-{slow}-{int(time.time())}", "ticker": ticker.upper(),
              "params": {"fast": fast, "slow": slow, "periods_per_year": periods_per_year},
              "window": {"first": dates[0], "last": dates[-1], "prices": len(closes)},
              "data_source": data_source or "not stated", **run(closes, fast, slow, periods_per_year),
              "caveats": ["no costs or slippage", "one asset, long or flat", "past results only"]}
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{result['id']}.json").write_text(json.dumps(result, indent=2))
    return out("backtest (local calculation)", result)


@mcp.tool()
def list_backtests() -> str:
    """List saved backtests, newest first."""
    files = sorted(DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if DIR.exists() else []
    rows = []
    for p in files[:50]:
        d = json.loads(p.read_text())
        rows.append({"id": d["id"], "window": d["window"], "total_return": d["strategy"].get("total_return")})
    return out("runs/backtests", rows)


@mcp.tool()
def get_backtest(backtest_id: str) -> str:
    """Full saved result for one backtest id from list_backtests."""
    p = DIR / f"{backtest_id}.json"
    if p.resolve().parent != DIR.resolve() or not p.exists():
        return out("runs/backtests", {"error": f"no backtest {backtest_id}"})
    return out("runs/backtests", json.loads(p.read_text()))


if __name__ == "__main__":
    mcp.run()
