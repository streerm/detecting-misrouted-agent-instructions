"""Agent cards: an agent's capability profile (capability, context scope, authority)."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

AUTHORITY_ORDER = ["read_only", "propose", "execute", "approve"]


class Capability(BaseModel):
    intents: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)


class ContextScope(BaseModel):
    domains: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    periods: str | None = None
    out_of_scope: list[str] = Field(default_factory=list)


class Authority(BaseModel):
    level: Literal["read_only", "propose", "execute", "approve"] = "read_only"
    may: list[str] = Field(default_factory=list)
    may_not: list[str] = Field(default_factory=list)

    def rank(self) -> int:
        return AUTHORITY_ORDER.index(self.level)


class AgentCard(BaseModel):
    id: str
    name: str
    description: str
    role: Literal["router", "specialist", "supervisor"] = "specialist"
    parent: str | None = None
    capability: Capability = Field(default_factory=Capability)
    context_scope: ContextScope = Field(default_factory=ContextScope)
    authority: Authority = Field(default_factory=Authority)
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    model: str = "default"

    def summary(self) -> str:
        """Compact text a router or judge model can read."""
        return (
            f"- id: {self.id}\n  description: {self.description}\n"
            f"  intents: {', '.join(self.capability.intents)}\n"
            f"  domains: {', '.join(self.context_scope.domains)}\n"
            f"  out_of_scope: {', '.join(self.context_scope.out_of_scope) or 'none'}\n"
            f"  authority: {self.authority.level}; may_not: {', '.join(self.authority.may_not) or 'none'}"
        )


def load_card(path: str | Path) -> AgentCard:
    return AgentCard.model_validate(yaml.safe_load(Path(path).read_text()))


def load_cards(directory: str | Path) -> dict[str, AgentCard]:
    cards = [load_card(p) for p in sorted(Path(directory).glob("*.yaml"))]
    ids = [c.id for c in cards]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate card ids in {directory}: {ids}")
    return {c.id: c for c in cards}


def specialists(cards: dict[str, AgentCard]) -> dict[str, AgentCard]:
    return {k: c for k, c in cards.items() if c.role != "router"}


def load_yaml(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text()) or {}
