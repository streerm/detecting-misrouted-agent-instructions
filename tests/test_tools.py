import json
import sys
from pathlib import Path

import pytest

from misroute.env import expand, missing_vars
from misroute.models import flatten, parse_json_tool_call, turn
from misroute.models.anthropic import to_anthropic
from misroute.models.openai_compat import to_openai
from misroute.tools import ToolCall, ToolSpec, Turn

HERE = Path(__file__).parent
SPEC = ToolSpec("fake__get_series", "Return a fake macro series.",
                {"type": "object", "properties": {"series_id": {"type": "string"}}, "required": ["series_id"]},
                "fake", "get_series")
TRANSCRIPT = [
    {"role": "user", "content": "CPI?"},
    {"role": "assistant", "content": "", "tool_calls": [{"id": "c1", "name": SPEC.name, "arguments": {"series_id": "CPIAUCSL"}}]},
    {"role": "tool", "tool_call_id": "c1", "name": SPEC.name, "content": "CPIAUCSL: 3.0"},
]


def test_env_expansion(monkeypatch):
    monkeypatch.setenv("A_KEY", "x")
    monkeypatch.delenv("NOPE", raising=False)
    assert expand("${A_KEY}-${NOPE:-dflt}") == "x-dflt"
    assert missing_vars("${NOPE}") == ["NOPE"] and missing_vars("${NOPE:-d}") == []


def test_vendor_translations():
    a = to_anthropic(TRANSCRIPT)
    assert a[1]["content"][0]["type"] == "tool_use" and a[2]["content"][0]["type"] == "tool_result"
    o = to_openai(TRANSCRIPT, "sys")
    assert o[0]["role"] == "system" and o[2]["tool_calls"][0]["function"]["name"] == SPEC.name
    assert o[3] == {"role": "tool", "tool_call_id": "c1", "content": "CPIAUCSL: 3.0"}
    f = flatten(TRANSCRIPT)
    assert [m["role"] for m in f] == ["user", "assistant", "user"]


def test_json_protocol_parses_only_known_tools():
    assert parse_json_tool_call('{"tool": "fake__get_series", "arguments": {"series_id": "GDP"}}', [SPEC]).arguments == {"series_id": "GDP"}
    assert parse_json_tool_call('{"tool": "rm_rf", "arguments": {}}', [SPEC]) is None


class ScriptedModel:
    """Text-only model (like a small local Llama) that follows the JSON tool protocol."""
    name = "scripted"

    def __init__(self):
        self.calls = 0

    def complete(self, messages, *, system=None, **_):
        self.calls += 1
        assert "fake__get_series" in (system or "")
        if not any("TOOL RESULT" in m["content"] for m in messages):
            return json.dumps({"tool": "fake__get_series", "arguments": {"series_id": "CPIAUCSL"}})
        return "CPI was 3.0 in 2026-10 (source: fake__get_series)."


def test_json_mode_turn():
    t = turn(ScriptedModel(), [{"role": "user", "content": "CPI?"}], tools=[SPEC])
    assert t.tool_calls and t.tool_calls[0].name == SPEC.name and t.text == ""


@pytest.fixture(scope="module")
def hub():
    pytest.importorskip("mcp")
    from misroute.tools.mcp_hub import ToolHub
    fake = {"command": sys.executable, "args": [str(HERE / "fake_mcp_server.py")]}
    h = ToolHub({"fake": fake, "fake2": fake,
                 "needs_key": {"command": "true", "env": {"K": "${SURELY_UNSET_VAR_123}"}}})
    yield h
    h.close()


def test_hub_lists_calls_and_isolates_failures(hub):
    specs = hub.specs(["fake", "needs_key", "absent"])
    assert {s.name for s in specs} == {"fake__get_series", "fake__fail"}
    assert "missing env" in hub.errors["needs_key"] and "not in .mcp.json" in hub.errors["absent"]
    assert "3.0" in hub.call("fake__get_series", {"series_id": "CPI"})
    assert hub.call("fake__fail", {}).startswith("ERROR")


def test_agent_tool_loop_with_card_scoping(hub):
    from misroute.agent import SkillAgent
    from misroute.desk import load_desk
    desk = load_desk()
    card = desk.cards["macro"].model_copy(update={"tools": ["fake"]})
    out = SkillAgent(card, ScriptedModel(), desk.skills, hub).run("US CPI last month?")
    assert out.tool_calls[0]["name"] == "fake__get_series" and "3.0" in out.text
    # an agent whose card lists no servers gets no tools at all
    assert SkillAgent(desk.cards["compliance"], ScriptedModel(), desk.skills, hub).tools() == []


class RogueModel(ScriptedModel):
    """Native-tool-calling model that names a tool it was never offered."""
    name = "rogue"

    def complete_turn(self, messages, *, system=None, tools=None, **_):
        if any(m["role"] == "tool" for m in messages):
            return Turn(text="Done.")
        return Turn(tool_calls=[ToolCall("c1", "fake__get_series", {"series_id": "CPIAUCSL"})])


def test_out_of_card_call_is_blocked_and_flagged(hub):
    from misroute.agent import AgentOutput, SkillAgent
    from misroute.desk import load_desk
    from misroute.detectors import ToolCallDetector
    from misroute.taxonomy import MisrouteType
    desk = load_desk()
    hub.specs(["fake", "fake2"])                          # both servers are running in the hub
    card = desk.cards["macro"].model_copy(update={"tools": ["fake2"]})   # but the card lists only fake2
    out = SkillAgent(card, RogueModel(), desk.skills, hub).run("US CPI last month?")
    assert out.tool_calls == [{"name": "fake__get_series", "arguments": {"series_id": "CPIAUCSL"},
                               "result_chars": out.tool_calls[0]["result_chars"], "error": True,
                               "out_of_card": True}]
    d = ToolCallDetector().detect(None, card, out)
    assert d.flagged and d.predicted_type is MisrouteType.CONTEXT and "fake__get_series" in d.reason

    det = ToolCallDetector()
    blank = AgentOutput("macro", "m", "q", "CPI was 3.0", 0.0)
    assert det.detect(None, card, blank).reason.startswith("no tools offered")      # abstains
    memory = AgentOutput("macro", "m", "q", "CPI was 3.0", 0.0, [], ["fake2__get_series"])
    assert det.detect(None, card, memory).score == 0.5 and not det.detect(None, card, memory).flagged
    strict = ToolCallDetector(flag_no_calls=True).detect(None, card, memory)
    assert strict.flagged and strict.predicted_type is MisrouteType.CAPABILITY

