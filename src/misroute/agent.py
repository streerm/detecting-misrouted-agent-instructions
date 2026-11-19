"""SkillAgent = card + model + skills (+ MCP tools from its card). Same class for every vendor and role."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .cards import AgentCard
from .models import ChatModel, turn
from .skills import Skill, build_system_prompt


@dataclass
class AgentOutput:
    agent_id: str
    model: str
    instruction: str
    text: str
    seconds: float
    # [{"name", "arguments", "result_chars", "error", "out_of_card"}]
    tool_calls: list[dict] = field(default_factory=list)
    tools_offered: list[str] = field(default_factory=list)  # qualified tool names the agent could call

    @property
    def refused(self) -> bool:
        return self.text.strip().startswith("OUT_OF_PROFILE:")


class SkillAgent:
    def __init__(self, card: AgentCard, model: ChatModel, skills: dict[str, Skill],
                 hub=None, max_tool_steps: int = 6):
        self.card, self.model, self.hub, self.max_tool_steps = card, model, hub, max_tool_steps
        self.system = build_system_prompt(card, skills)

    def tools(self):
        """Only the servers named in this agent's card. Access control lives here."""
        return self.hub.specs(self.card.tools) if self.hub and self.card.tools else []

    def run(self, instruction: str) -> AgentOutput:
        t0 = time.perf_counter()
        tools = self.tools()
        offered = [t.name for t in tools]
        messages: list[dict] = [{"role": "user", "content": instruction}]
        log: list[dict] = []
        text = ""
        for _ in range(self.max_tool_steps + 1):
            step = turn(self.model, messages, system=self.system, tools=tools)
            text = step.text
            if not step.tool_calls:
                break
            messages.append({"role": "assistant", "content": step.text, "tool_calls": [
                {"id": c.id, "name": c.name, "arguments": c.arguments} for c in step.tool_calls]})
            for c in step.tool_calls:
                # A model can name a tool it was never offered; the card, not the hub, decides.
                allowed = c.name in offered
                result = (self.hub.call(c.name, c.arguments) if allowed
                          else f"ERROR: tool {c.name} is not in this agent's card")
                log.append({"name": c.name, "arguments": c.arguments, "result_chars": len(result),
                            "error": result.startswith("ERROR"), "out_of_card": not allowed})
                messages.append({"role": "tool", "tool_call_id": c.id, "name": c.name, "content": result})
        else:
            text = text or "STOPPED: tool step limit reached"
        return AgentOutput(self.card.id, self.model.name, instruction, text, time.perf_counter() - t0, log, offered)


def build_agents(cards: dict[str, AgentCard], skills: dict[str, Skill], registry,
                 override_model: str | None = None, hub=None) -> dict[str, SkillAgent]:
    """override_model swaps every agent's model at once (e.g. run the whole desk on Qwen)."""
    return {cid: SkillAgent(c, registry.get(override_model or c.model), skills, hub)
            for cid, c in cards.items()}
