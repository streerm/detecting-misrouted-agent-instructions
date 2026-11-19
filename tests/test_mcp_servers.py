"""Offline tests for the local MCP servers in mcp_servers/ (pure logic only; no network)."""
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp_servers"))


def test_backtest_trades_on_next_day_and_validates(tmp_path, monkeypatch):
    import backtest
    monkeypatch.setattr(backtest, "DIR", tmp_path)
    up = [100 + i for i in range(40)]
    res = backtest.run(up, 2, 5, 252)
    # in a steady uptrend the strategy is long throughout the scored window, so it equals buy-and-hold
    assert res["strategy"]["total_return"] == res["buy_and_hold"]["total_return"] > 0
    assert backtest.run(up[::-1], 2, 5, 252)["strategy"]["total_return"] == 0      # downtrend: stays flat
    dates = [f"2026-01-{d:02d}" for d in range(1, 29)] + [f"2026-02-{d:02d}" for d in range(1, 13)]
    saved = json.loads(backtest.run_sma_crossover("abc", dates, up, 2, 5, data_source="test"))["data"]
    assert saved["window"] == {"first": "2026-01-01", "last": "2026-02-12", "prices": 40}
    assert json.loads(backtest.get_backtest(saved["id"]))["data"]["ticker"] == "ABC"
    assert "error" in json.loads(backtest.run_sma_crossover("abc", dates[::-1], up, 2, 5))["data"]
    assert "error" in json.loads(backtest.get_backtest("../../.env"))["data"]


def test_arxiv_parse():
    import arxiv
    xml = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2503.13657v3</id>
    <title>Why Do Multi-Agent
      LLM Systems Fail?</title><summary>  We study failures. </summary><published>2025-03-17T00:00:00Z</published>
    <updated>2025-10-26T00:00:00Z</updated><author><name>A. One</name></author></entry></feed>"""
    assert arxiv.parse(xml, 400) == [{"id": "2503.13657v3", "title": "Why Do Multi-Agent LLM Systems Fail?",
                                      "authors": ["A. One"], "published": "2025-03-17", "updated": "2025-10-26",
                                      "abstract": "We study failures.", "url": "http://arxiv.org/abs/2503.13657v3"}]


def test_sanctions_match_needs_every_word():
    import sanctions
    table = [["1", "EXAMPLE TRADING COMPANY LIMITED", "-0- ", "SDGT"], ["2", "DOE, John", "individual", "CYBER2"]]
    assert [h["uid"] for h in sanctions.match("example trading", table, 10)] == ["1"]
    assert sanctions.match("John Doe", table, 10)[0]["type"] == "individual"
    assert sanctions.match("example shipping", table, 10) == [] and sanctions.match("", table, 10) == []


def test_catalogue_links_sources_to_agents():
    import catalogue
    rows = {r["id"]: r for r in json.loads(catalogue.list_sources())["data"]}
    assert rows["sec_edgar"]["agents"] == ["filings"] and "macro" in rows["dbnomics"]["agents"]
    assert "known" in json.loads(catalogue.describe_source("nope"))["data"]


def test_news_shapes():
    import news
    items = [{"datetime": 1795000000, "headline": "B", "source": "s", "url": "u", "summary": "x" * 400},
             {"datetime": 1795090000, "headline": "A", "source": "s", "url": "u", "summary": None}]
    rows = news.shape_finnhub(items, 5)
    assert [r["headline"] for r in rows] == ["A", "B"] and len(rows[1]["summary"]) == 300 and rows[0]["date"] == "2026-11-19"
    call = {"symbol": "X", "quarter": "2026Q4", "transcript": [
        {"speaker": "CFO", "title": "CFO", "content": "Gross margin rose. " * 10},
        {"speaker": "CEO", "title": "CEO", "content": "Demand was steady."},
        {"speaker": "CFO", "title": "CFO", "content": "We expect margin pressure."}]}
    got = news.shape_transcript(call, "margin", 60)
    assert got["turns_matching"] == 2 and got["turns_returned"] == 1 and got["truncated"]
    assert got["turns"][0]["text"].endswith("…[cut]") and len(got["turns"][0]["text"]) < 70
    full = news.shape_transcript(call, "", 10000)
    assert full["turns_returned"] == 3 and not full["truncated"]
