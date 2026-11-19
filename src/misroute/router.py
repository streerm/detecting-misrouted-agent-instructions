"""Routers choose one specialist per instruction. Swap freely; detectors don't care which you use."""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .cards import AgentCard, specialists
from .models import ChatModel


@dataclass
class RouteDecision:
    agent_id: str
    confidence: float
    reason: str = ""


class Router(ABC):
    @abstractmethod
    def route(self, instruction: str, cards: dict[str, AgentCard]) -> RouteDecision: ...


def match_intents(instruction: str, intent_keywords: dict[str, list[str]]) -> dict[str, int]:
    """Keyword hits per intent. A cheap, transparent baseline signal."""
    text = instruction.lower()
    hits = {}
    for intent, kws in intent_keywords.items():
        n = sum(1 for kw in kws if re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", text))
        if n:
            hits[intent] = n
    return hits


class KeywordRouter(Router):
    def __init__(self, intent_keywords: dict[str, list[str]]):
        self.intent_keywords = intent_keywords

    def route(self, instruction, cards):
        hits = match_intents(instruction, self.intent_keywords)
        scores = {cid: sum(hits.get(i, 0) for i in c.capability.intents)
                  for cid, c in specialists(cards).items()}
        best = max(scores, key=lambda k: scores[k])
        total = sum(scores.values())
        conf = scores[best] / total if total else 0.0
        return RouteDecision(best, conf, f"keyword hits {hits}")


class LLMRouter(Router):
    """Any ChatModel as router. Falls back to `fallback` if the reply can't be parsed."""

    def __init__(self, model: ChatModel, fallback: Router | None = None):
        self.model, self.fallback = model, fallback

    def route(self, instruction, cards):
        spec = specialists(cards)
        system = ("You route instructions to exactly one agent. Agents:\n"
                  + "\n".join(c.summary() for c in spec.values())
                  + '\nReply with JSON only: {"agent": "<id>", "confidence": <0..1>, "reason": "<short>"}')
        reply = self.model.complete([{"role": "user", "content": instruction}], system=system)
        m = re.search(r"\{.*\}", reply, re.S)
        try:
            data = json.loads(m.group(0)) if m else {}
            if data.get("agent") in spec:
                return RouteDecision(data["agent"], float(data.get("confidence", 0.5)), data.get("reason", ""))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        if self.fallback:
            d = self.fallback.route(instruction, cards)
            return RouteDecision(d.agent_id, d.confidence, f"fallback ({self.model.name} unparsable): {d.reason}")
        raise ValueError(f"router {self.model.name} returned no valid agent: {reply[:200]}")
