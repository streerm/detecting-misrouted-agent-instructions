"""Spec: "an output anomaly detector using contrastive scoring against what a correctly-routed
agent would produce". Reference = the gold agent run on the original instruction (in practice a
separate reference model). Similarity is pluggable: token Jaccard by default; swap in embeddings
or an LLM judge. The threshold must be calibrated (e.g. conformally) before any claim is made."""
from __future__ import annotations

import re
from typing import Callable

from ..taxonomy import MisrouteType
from .base import Detection, Detector


def jaccard(a: str, b: str) -> float:
    ta, tb = set(re.findall(r"[a-z0-9]+", a.lower())), set(re.findall(r"[a-z0-9]+", b.lower()))
    return len(ta & tb) / len(ta | tb) if ta | tb else 1.0


class ContrastiveOutputDetector(Detector):
    name, stage = "contrastive_output", "post"

    def __init__(self, reference_fn: Callable, similarity: Callable[[str, str], float] = jaccard,
                 threshold: float = 0.05):
        self.reference_fn, self.similarity, self.threshold = reference_fn, similarity, threshold

    def detect(self, case, card, output=None, context=None) -> Detection:
        if output is None:
            raise ValueError("contrastive detector needs the agent output")
        ref = self.reference_fn(case)
        score = 1.0 - self.similarity(output.text, ref.text)
        flagged = score > self.threshold
        return Detection(self.name, flagged, score, MisrouteType.SEMANTIC if flagged else None,
                         self.stage, f"distance {score:.3f} vs threshold {self.threshold}")


class SelfReportDetector(Detector):
    """The agent itself says OUT_OF_PROFILE (its system prompt asks it to). Cheap; unreliable alone."""
    name, stage = "self_report", "post"

    def detect(self, case, card, output=None, context=None) -> Detection:
        hit = bool(output and output.refused)
        return Detection(self.name, hit, float(hit), None, self.stage, output.text[:120] if hit else "")
