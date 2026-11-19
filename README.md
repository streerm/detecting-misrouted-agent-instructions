# detecting-misrouted-agent-instructions

Team repo for the Oxford Edge AI/ML Challenge (the sponsor), **spec 41: "Detecting Misrouted Instructions in Hierarchical Agent Systems"**.

The framework is **model-agnostic**: every agent is a *card* (YAML) plus *skills* (`SKILL.md` folders) plus a *model* chosen by name from a registry. Claude, Llama, Qwen, Mistral or anything behind an OpenAI-compatible endpoint (Ollama, vLLM, LM Studio, Together, Groq) can play any role, and you can swap one per experiment without touching code.

## Layout

```
skills/            Reusable skills in the open Agent Skills format (SKILL.md + optional files).
                   Work with Claude natively; other models get them injected by src/misroute/skills.py.
  <name>/            Our own skills (finance research rules, cross-checking, cards, labelling).
  vendor/anthropic-financial-services/
                     Anthropic's official finance skills (comps, DCF, LBO, 3-statement, earnings,
                     IC memo, pitch deck, ...), Apache 2.0, unmodified. See NOTICE.md there.
agents/cards/      One YAML card per agent: capability, context scope, authority, skills, tools, model.
configs/           models.yaml (model registry), data_sources.yaml (which data each agent may touch).
src/misroute/      The framework.
  cards.py           AgentCard schema + loader
  skills.py          SKILL.md loader and prompt builder
  models/            ChatModel protocol + adapters: anthropic, openai_compat, offline echo
  agent.py           SkillAgent = card + model + skills
  router.py          Router interface, keyword baseline, LLM router
  taxonomy.py        Misroute types, quoted from the spec
  inject.py          Fault injection with ground truth
  detectors/         Detector interface; capability-profile check; contrastive output check
  eval.py            Precision, recall, detection latency
  trace.py           JSONL traces (field names chosen to map onto Langfuse later)
data/requests/     Example requests with gold routes.
scripts/           run_demo.py: route, inject, detect, score, all offline by default.
tests/             pytest suite, runs with no API keys.
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"            # core + pytest; add [anthropic] and/or [openai] for real models
pytest -q
python scripts/run_demo.py         # offline: uses the deterministic "echo" model
```

Real models:

```bash
cp .env.example .env               # fill in keys locally; never commit .env, never paste keys in chat
python scripts/run_demo.py --model claude-sonnet
ollama pull qwen2.5:7b && python scripts/run_demo.py --model qwen-local
python scripts/run_demo.py --model llama-local --router-model claude-sonnet   # mix models per role
```

## Adding things

- **A model:** add an entry to `configs/models.yaml`. Any OpenAI-compatible server needs only `provider: openai_compat`, `base_url` and `model`. A new provider type means one class implementing `ChatModel.complete()` in `src/misroute/models/` and one line in `registry.py`.
- **An agent:** add a card to `agents/cards/`. See `skills/agent-card-authoring/SKILL.md`.
- **A skill:** add `skills/<name>/SKILL.md` with `name` and `description` frontmatter, then list it under `skills:` in a card.
- **A detector:** subclass `Detector` in `src/misroute/detectors/` and register it in `detectors/__init__.py`.
- **A misroute type or injection:** `taxonomy.py` and `inject.py`.

## Status

Scaffold only. The use case (quant research desk) is Mark's preference and not a team decision; the cards are an example. See `docs/spec-notes.md` for the spec wording and its known gaps.
