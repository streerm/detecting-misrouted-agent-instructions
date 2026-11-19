"""Tool-call log as a misroute signal (not one of the spec's two detectors; an extra of ours).

Reads AgentOutput.tool_calls and AgentOutput.tools_offered, both recorded by SkillAgent.run:

1. The agent tried to call a tool outside its card. SkillAgent blocks the call, and this detector
   flags it. We map it to "context mismatch" because the card's data sources are part of its
   context scope; that mapping is our choice, not the spec's.
2. The agent was offered tools, did not refuse, and answered without calling any of them, i.e. from
   model memory. Example: a revenue question sent to the market-data agent, which has no
   financial statements. Scored 0.5 but only flagged when flag_no_calls=True, because a correctly
   routed agent may also answer without a call. The score is uncalibrated.
3. Every call errored: scored 0.3, never flagged (a network fault looks the same).

Abstains (score 0, not flagged) when the agent was offered no tools.
"""
from __future__ import annotations

from ..taxonomy import MisrouteType
from .base import Detection, Detector


class ToolCallDetector(Detector):
    name, stage = "tool_calls", "post"

    def __init__(self, flag_no_calls: bool = False):
        self.flag_no_calls = flag_no_calls

    def detect(self, case, card, output=None, context=None) -> Detection:
        if output is None:
            raise ValueError("tool-call detector needs the agent output")
        calls = output.tool_calls
        outside = sorted({c["name"] for c in calls if c.get("out_of_card")})
        if outside:
            return Detection(self.name, True, 1.0, MisrouteType.CONTEXT, self.stage,
                             f"called tools outside card {card.id}: {outside}")
        if not output.tools_offered:
            return Detection(self.name, False, 0.0, None, self.stage, "no tools offered; abstain")
        if not calls and not output.refused:
            return Detection(self.name, self.flag_no_calls, 0.5,
                             MisrouteType.CAPABILITY if self.flag_no_calls else None, self.stage,
                             "answered without calling any offered tool (from model memory)")
        if calls and all(c.get("error") for c in calls):
            return Detection(self.name, False, 0.3, None, self.stage, f"all {len(calls)} tool calls errored")
        return Detection(self.name, False, 0.0, None, self.stage, f"{len(calls)} in-card tool calls")
