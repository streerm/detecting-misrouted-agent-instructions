"""Misroute types. Values quote spec 41's Scope exactly:
"A taxonomy of misrouting failure modes — capability mismatch, context mismatch,
authority mismatch, semantic misinterpretation"
"""
from enum import Enum


class MisrouteType(str, Enum):
    CAPABILITY = "capability mismatch"
    CONTEXT = "context mismatch"
    AUTHORITY = "authority mismatch"
    SEMANTIC = "semantic misinterpretation"


# Which card field each type violates (see skills/agent-card-authoring).
VIOLATED_FIELD = {
    MisrouteType.CAPABILITY: "capability",
    MisrouteType.CONTEXT: "context_scope",
    MisrouteType.AUTHORITY: "authority",
    MisrouteType.SEMANTIC: None,  # right agent, wrong reading: needs an output-side detector
}
