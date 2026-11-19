"""SkillAgent = card + model + skills. Same class for every vendor and every role."""
from __future__ import annotations

import time
from dataclasses import dataclass

from .cards import AgentCard
from .models import ChatModel
from .skills import Skill, build_system_prompt


@dataclass
class AgentOutput:
    agent_id: str
    model: str
    instruction: str
    text: str
    seconds: float

    @property
    def refused(self) -> bool:
        return self.text.strip().startswith("OUT_OF_PROFILE:")


class SkillAgent:
    def __init__(self, card: AgentCard, model: ChatModel, skills: dict[str, Skill]):
        self.card, self.model = card, model
        self.system = build_system_prompt(card, skills)

    def run(self, instruction: str) -> AgentOutput:
        t0 = time.perf_counter()
        text = self.model.complete([{"role": "user", "content": instruction}], system=self.system)
        return AgentOutput(self.card.id, self.model.name, instruction, text, time.perf_counter() - t0)


def build_agents(cards: dict[str, AgentCard], skills: dict[str, Skill], registry,
                 override_model: str | None = None) -> dict[str, SkillAgent]:
    """override_model swaps every agent's model at once (e.g. run the whole desk on Qwen)."""
    return {cid: SkillAgent(c, registry.get(override_model or c.model), skills)
            for cid, c in cards.items()}
