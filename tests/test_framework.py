from pathlib import Path

import pytest

from misroute import REPO_ROOT
from misroute.cards import AgentCard
from misroute.desk import load_desk, load_requests
from misroute.detectors import CapabilityProfileCheck, ContrastiveOutputDetector
from misroute.eval import score
from misroute.inject import build_cases
from misroute.models import PROVIDERS, EchoModel, ModelRegistry
from misroute.pipeline import run_case
from misroute.router import KeywordRouter, LLMRouter
from misroute.skills import build_system_prompt, parse_skill
from misroute.taxonomy import MisrouteType


@pytest.fixture(scope="module")
def desk():
    return load_desk()


def test_spec_wording_is_exact():
    assert [t.value for t in MisrouteType] == [
        "capability mismatch", "context mismatch", "authority mismatch", "semantic misinterpretation"]


def test_all_skills_parse_and_match_folder():
    from misroute.skills import load_skills
    skills = load_skills(REPO_ROOT / "skills")
    assert {"finance-research-rules", "dcf-model", "comps-analysis", "lbo-model",
            "3-statement-model", "earnings-analysis", "ic-memo", "pitch-deck"} <= set(skills)
    assert all(len(s.description) > 20 for s in skills.values())


def test_cards_reference_known_skills_and_models(desk):
    for c in desk.cards.values():
        assert set(c.skills) <= set(desk.skills)
        desk.registry.resolve(c.model) in desk.registry.specs


def test_system_prompt_includes_skill_bodies(desk):
    prompt = build_system_prompt(desk.cards["filings"], desk.skills)
    assert "Finance research rules" in prompt and "OUT_OF_PROFILE" in prompt


def test_registry_lists_open_models_and_lazy_imports():
    reg = ModelRegistry(REPO_ROOT / "configs/models.yaml")
    assert {"qwen-local", "llama-local", "claude-sonnet"} <= set(reg.specs)
    assert isinstance(reg.get("echo"), EchoModel)
    assert {"anthropic", "openai_compat", "echo"} <= set(PROVIDERS)


def test_new_provider_plugs_in(tmp_path):
    class Fixed:
        def __init__(self, name, **_):
            self.name = name

        def complete(self, messages, **_):
            return '{"agent": "macro", "confidence": 0.9}'

    PROVIDERS["fixed"] = Fixed
    cfg = tmp_path / "m.yaml"
    cfg.write_text("default: f\nmodels:\n  f: {provider: fixed}\n")
    try:
        router = LLMRouter(ModelRegistry(cfg).get("f"))
        assert router.route("anything", load_desk().cards).agent_id == "macro"
    finally:
        PROVIDERS.pop("fixed")


def test_llm_router_falls_back_on_garbage(desk):
    r = LLMRouter(EchoModel(), fallback=KeywordRouter(desk.intents))
    assert r.route("Give me US CPI for 2025", desk.cards).agent_id == "macro"


def test_capability_check_types(desk):
    det = CapabilityProfileCheck(desk.intents, desk.scopes)
    from misroute.inject import Case
    mk = lambda text, to: Case("x", text, "filings", to, text, None)
    assert det.detect(mk("Compare Item 1A in the 10-K", "macro"), desk.cards["macro"]).predicted_type == MisrouteType.CAPABILITY
    assert det.detect(mk("Compare Item 1A in the 10-K and then place an order for 5 shares", "filings"),
                      desk.cards["filings"]).predicted_type == MisrouteType.AUTHORITY
    assert det.detect(mk("Compare Item 1A in the 10-K and include today's closing share price", "filings"),
                      desk.cards["filings"]).predicted_type == MisrouteType.CONTEXT
    assert not det.detect(mk("Compare Item 1A in the 10-K", "filings"), desk.cards["filings"]).flagged


def test_end_to_end_offline(desk):
    reqs = load_requests(REPO_ROOT / "data/requests/sample.jsonl")
    router = KeywordRouter(desk.intents)
    routed = {r["id"]: router.route(r["instruction"], desk.cards).agent_id for r in reqs}
    dets = [CapabilityProfileCheck(desk.intents, desk.scopes),
            ContrastiveOutputDetector(lambda c: desk.agents[c.gold_agent].run(c.instruction))]
    cases = build_cases(reqs, desk.cards, routed, desk.scopes)
    results = [run_case(c, desk.agents, dets) for c in cases]
    s = score(results)
    assert {c.label for c in cases if c.label} == set(MisrouteType)
    assert 0 <= s["overall"]["precision"] <= 1 and s["latency"]["mean_steps"] is not None
