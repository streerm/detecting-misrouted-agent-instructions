from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..taxonomy import MisrouteType


@dataclass
class Detection:
    detector: str
    flagged: bool
    score: float                         # higher = more likely misrouted
    predicted_type: MisrouteType | None
    stage: str                           # "pre" (before the agent runs) or "post" (needs output)
    reason: str = ""


class Detector(ABC):
    name: str = "detector"
    stage: str = "pre"

    @abstractmethod
    def detect(self, case, card, output=None, context=None) -> Detection: ...
