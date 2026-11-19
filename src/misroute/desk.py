"""Load everything for a desk (cards, skills, models, vocab) from the repo layout in one call."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import REPO_ROOT
from .agent import SkillAgent, build_agents
from .cards import AgentCard, load_cards, load_yaml
from .env import load_dotenv
from .models import ModelRegistry
from .skills import Skill, load_skills


@dataclass
class Desk:
    cards: dict[str, AgentCard]
    skills: dict[str, Skill]
    registry: ModelRegistry
    intents: dict[str, list[str]]
    scopes: dict
    agents: dict[str, SkillAgent]
    hub: object = None


def load_desk(root: str | Path = REPO_ROOT, model: str | None = None, tools: bool = False,
              hub=None) -> Desk:
    """tools=True starts the MCP servers named in cards (from .mcp.json). Off by default: offline."""
    root = Path(root)
    load_dotenv(root / ".env")
    cards = load_cards(root / "agents/cards")
    skills = load_skills(root / "skills")
    registry = ModelRegistry(root / "configs/models.yaml")
    intents = load_yaml(root / "agents/intents.yaml")
    for c in cards.values():
        unknown = set(c.capability.intents) - set(intents)
        if unknown:
            raise ValueError(f"card {c.id}: intents {unknown} not in agents/intents.yaml")
    if tools and hub is None:
        from .tools.mcp_hub import ToolHub, load_mcp_config
        hub = ToolHub(load_mcp_config(root / ".mcp.json"))
    return Desk(cards, skills, registry, intents, load_yaml(root / "agents/scopes.yaml"),
                build_agents(cards, skills, registry, model, hub), hub)


def load_requests(path: str | Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
