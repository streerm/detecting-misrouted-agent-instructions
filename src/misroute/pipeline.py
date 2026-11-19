"""Run one case: pre-execution detectors, then (if nothing fired) the agent, then post detectors."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .detectors import Detection, Detector
from .inject import Case


@dataclass
class CaseResult:
    case: Case
    detections: list[Detection] = field(default_factory=list)
    flagged: bool = False
    predicted_type: object = None
    detected_at_step: int | None = None      # 0 = before the agent ran, 1 = after its output
    seconds_to_detect: float | None = None
    output_text: str | None = None


def run_case(case: Case, agents: dict, detectors: list[Detector], tracer=None) -> CaseResult:
    t0 = time.perf_counter()
    card = agents[case.routed_to].card
    res = CaseResult(case)

    def fire(step: int) -> bool:
        hit = next((d for d in res.detections if d.flagged), None)
        if hit and not res.flagged:
            res.flagged, res.predicted_type = True, hit.predicted_type
            res.detected_at_step, res.seconds_to_detect = step, time.perf_counter() - t0
        return res.flagged

    for d in (x for x in detectors if x.stage == "pre"):
        res.detections.append(d.detect(case, card))
    if not fire(0):
        out = agents[case.routed_to].run(case.delivered)
        res.output_text = out.text
        for d in (x for x in detectors if x.stage == "post"):
            res.detections.append(d.detect(case, card, out))
        fire(1)
    if tracer:
        tracer.span(case.id, "case", input=case.instruction, output=res.output_text,
                    routed_to=case.routed_to, gold=case.gold_agent,
                    label=case.label.value if case.label else None,
                    flagged=res.flagged, predicted=getattr(res.predicted_type, "value", None),
                    detections=[d.__dict__ for d in res.detections])
    return res
