"""Spec: "a capability-profile consistency check between instruction intent and the
receiving agent's profile". Intent extraction is pluggable: keywords by default, any ChatModel optionally."""
from __future__ import annotations

import json
import re

from ..router import match_intents
from ..taxonomy import MisrouteType
from .base import Detection, Detector


class CapabilityProfileCheck(Detector):
    name, stage = "capability_profile_check", "pre"

    def __init__(self, intent_keywords: dict, scopes: dict, intent_model=None):
        self.intent_keywords, self.scopes, self.intent_model = intent_keywords, scopes, intent_model

    def intents(self, instruction: str) -> set[str]:
        if self.intent_model is None:
            return set(match_intents(instruction, self.intent_keywords))
        system = ("Label the instruction with every intent it requires, from this list only: "
                  + ", ".join(self.intent_keywords) + '. Reply JSON: {"intents": [...]}')
        reply = self.intent_model.complete([{"role": "user", "content": instruction}], system=system)
        m = re.search(r"\{.*\}", reply, re.S)
        try:
            return {i for i in json.loads(m.group(0))["intents"] if i in self.intent_keywords}
        except Exception:
            return set(match_intents(instruction, self.intent_keywords))

    def detect(self, case, card, output=None, context=None) -> Detection:
        need = self.intents(case.instruction)
        have = set(card.capability.intents)
        if need and not need & have:
            return Detection(self.name, True, 1.0, MisrouteType.CAPABILITY, self.stage,
                             f"needs {sorted(need)}; card has {sorted(have)}")
        forbidden = need & set(card.authority.may_not)
        if forbidden:
            return Detection(self.name, True, 0.9, MisrouteType.AUTHORITY, self.stage,
                             f"needs {sorted(forbidden)}, which card forbids")
        oos = {i for s in card.context_scope.out_of_scope for i in self.scopes.get(s, {}).get("intents", [])}
        if need & oos:
            return Detection(self.name, True, 0.8, MisrouteType.CONTEXT, self.stage,
                             f"needs {sorted(need & oos)}, outside context scope")
        return Detection(self.name, False, 0.0, None, self.stage, f"intents {sorted(need)} fit card")
