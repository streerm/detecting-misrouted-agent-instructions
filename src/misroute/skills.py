"""Load skills in the open Agent Skills format (skills/<name>/SKILL.md) for ANY model.

Claude loads SKILL.md natively. For other models (Llama, Qwen, ...) we do the same job here:
the card lists its skills, and their bodies are placed in the system prompt.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .cards import AgentCard


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    path: Path


def parse_skill(path: str | Path) -> Skill:
    path = Path(path)
    text = path.read_text()
    if not text.startswith("---"):
        raise ValueError(f"{path}: SKILL.md must start with YAML frontmatter")
    _, front, body = text.split("---", 2)
    meta = yaml.safe_load(front) or {}
    for key in ("name", "description"):
        if not meta.get(key):
            raise ValueError(f"{path}: frontmatter needs '{key}'")
    return Skill(meta["name"], meta["description"], body.strip(), path.parent)


def load_skills(directory: str | Path) -> dict[str, Skill]:
    skills = {}
    for p in sorted(Path(directory).glob("*/SKILL.md")):
        s = parse_skill(p)
        if s.name != p.parent.name:
            raise ValueError(f"{p}: name '{s.name}' must match folder '{p.parent.name}'")
        skills[s.name] = s
    return skills


def build_system_prompt(card: AgentCard, skills: dict[str, Skill], *, full: bool = True) -> str:
    """System prompt for a card. full=False gives descriptions only (progressive disclosure)."""
    missing = [s for s in card.skills if s not in skills]
    if missing:
        raise KeyError(f"card '{card.id}' lists unknown skills: {missing}")
    parts = [
        f"You are {card.name} (id: {card.id}). {card.description}",
        f"Your capabilities: {', '.join(card.capability.intents)}.",
        f"Your context scope: {', '.join(card.context_scope.domains)}. "
        f"Out of scope: {', '.join(card.context_scope.out_of_scope) or 'none'}.",
        f"Your authority: {card.authority.level}. You must not: {', '.join(card.authority.may_not) or 'n/a'}.",
        "If an instruction is outside your capability, scope or authority, say so in one line "
        "starting with 'OUT_OF_PROFILE:' and do not attempt it.",
    ]
    for name in card.skills:
        s = skills[name]
        parts.append(f"\n## Skill: {s.name}\n{s.body if full else s.description}")
    return "\n".join(parts)
