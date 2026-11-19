"""Route sample requests, inject one misroute of each type, detect, and score. Offline by default.

  python scripts/run_demo.py                                  # all agents on the echo model
  python scripts/run_demo.py --model qwen-local               # whole desk on Qwen via Ollama
  python scripts/run_demo.py --router-model claude-sonnet     # LLM router, agents per their cards
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from misroute import REPO_ROOT
from misroute.desk import load_desk, load_requests
from misroute.detectors import CapabilityProfileCheck, ContrastiveOutputDetector, SelfReportDetector
from misroute.eval import format_report, score
from misroute.inject import build_cases
from misroute.pipeline import run_case
from misroute.router import KeywordRouter, LLMRouter
from misroute.trace import Tracer


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="override every agent's model (name in configs/models.yaml)")
    ap.add_argument("--router-model", help="use an LLM router with this model; default keyword router")
    ap.add_argument("--reference-model", help="model for the contrastive reference agent")
    ap.add_argument("--requests", default=str(REPO_ROOT / "data/requests/sample.jsonl"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tools", action="store_true", help="start MCP servers from .mcp.json for agents' cards")
    ap.add_argument("--trace", default=str(REPO_ROOT / f"traces/demo-{int(time.time())}.jsonl"))
    args = ap.parse_args()

    desk = load_desk(model=args.model, tools=args.tools)
    reqs = load_requests(args.requests)
    keyword = KeywordRouter(desk.intents)
    router = LLMRouter(desk.registry.get(args.router_model), fallback=keyword) if args.router_model else keyword
    routed = {r["id"]: router.route(r["instruction"], desk.cards).agent_id for r in reqs}
    print(f"router: {type(router).__name__}; clean routing accuracy "
          f"{sum(routed[r['id']] == r['gold_agent'] for r in reqs)}/{len(reqs)}")

    ref_agents = load_desk(model=args.reference_model or args.model).agents
    detectors = [
        CapabilityProfileCheck(desk.intents, desk.scopes),
        ContrastiveOutputDetector(lambda c: ref_agents[c.gold_agent].run(c.instruction)),
        SelfReportDetector(),
    ]
    cases = build_cases(reqs, desk.cards, routed, desk.scopes, seed=args.seed)
    tracer = Tracer(args.trace)
    results = [run_case(c, desk.agents, detectors, tracer) for c in cases]
    print(f"cases: {len(cases)} ({sum(c.label is not None for c in cases)} injected)\n")
    print(format_report(score(results)))
    print("\nNOTE: with the keyword detector, injections and detection share one vocabulary, so these\n"
          "scores are a plumbing check, not a result. Real numbers need LLM intent extraction,\n"
          "held-out paraphrased requests, and real model outputs.")
    print(f"\ntraces: {args.trace}")
    if desk.hub:
        if desk.hub.errors:
            print(f"tool servers not started: {desk.hub.errors}")
        desk.hub.close()


if __name__ == "__main__":
    main()
