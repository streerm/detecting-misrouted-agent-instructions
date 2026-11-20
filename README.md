# detecting-misrouted-agent-instructions

Prototype scaffold for a student team project in the Oxford Edge AI/ML Challenge, **spec 41: "Detecting Misrouted Instructions in Hierarchical Agent Systems"**.

> **Status, 20 Nov 2026: a scaffold, not a result.** No request has been routed or answered by a real model yet; tests and the demo run on an offline `echo` model. The data tools are real and return live data. The team has not yet chosen a direction, a use case or a framework, and this repo holds more components than the project will use. See [`docs/STATUS.md`](docs/STATUS.md) for what works, what is wired but not set up, and what is missing, and [`docs/research-desk-wiring.html`](docs/research-desk-wiring.html) for a drawing of the example desk under four wirings.

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
mcp_servers/       Small MCP servers of our own (catalogue, dbnomics, arxiv, sanctions, companies_house,
                   backtest, news): standard library + mcp, read-only, every result has source and time.
.mcp.json          The 11 MCP tool servers. Read by Claude Code AND by our framework, so
                   Claude and the experimental agents (Llama, Qwen, ...) use the same tools.
src/misroute/      The framework.
  cards.py           AgentCard schema + loader
  skills.py          SKILL.md loader and prompt builder
  models/            ChatModel protocol + adapters: anthropic, openai_compat, offline echo
  agent.py           SkillAgent = card + model + skills + the MCP servers its card lists
  tools/             MCP hub (starts servers, exposes tools to any model) and neutral tool types
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
cp .env.template .env              # one file for every key; fill in what you use; never commit it
python scripts/run_demo.py --model claude-sonnet
ollama pull qwen2.5:7b && python scripts/run_demo.py --model qwen-local
python scripts/run_demo.py --model llama-local --router-model claude-sonnet   # mix models per role
```

## Data tools (MCP)

| Server | Gives | Needs in `.env` | Used by card |
| --- | --- | --- | --- |
| `edgartools` | SEC filings, XBRL financials, notes, insider and fund data (13 tools) | `EDGAR_IDENTITY="Name email"` | `filings` |
| `companies_house` (ours) | UK company search, profile, officers, filing history | `COMPANIES_HOUSE_API_KEY` | `filings` |
| `alphavantage` | Prices, fundamentals, FX, commodities (official local server) | `ALPHAVANTAGE_API_KEY` | `market-data` |
| `finnhub` | Quotes, estimates, ownership, calendars (community server) | `FINNHUB_API_KEY` | `market-data` |
| `news` (ours) | Company headlines (Finnhub) and earnings call transcripts (Alpha Vantage) | both keys above | `news` |
| `fred` | 800,000+ FRED macro series (3 tools) | `FRED_API_KEY` | `macro` |
| `dbnomics` (ours) | Non-US macro: ECB, Eurostat, BoE, OECD, IMF | none | `macro` |
| `backtest` (ours) | Moving-average crossover on prices the caller supplies | none | `backtest` |
| `sanctions` (ours) | US Treasury OFAC SDN name screening | none | `compliance` |
| `catalogue` (ours) | What data the desk has and which agent may use it | none | `router` |
| `arxiv` (ours) | Paper search and abstracts | none | no card yet |

Store a key without it appearing on screen: `python scripts/set_key.py ALPHAVANTAGE_API_KEY`.

```bash
pip install -e ".[mcp]"                        # plus: uv (for uvx) and Node 18+ (for npx)
python scripts/check_tools.py --smoke          # starts every server, lists tools, makes one real call each
python scripts/run_demo.py --tools --model qwen-local
```

- **Access control:** an agent sees only the servers listed under `tools:` in its card. A tool call outside the card is itself evidence of a misroute.
- **Any model:** Claude and OpenAI-compatible servers use native tool calling. Models without it (many small local ones) use a JSON protocol; set `tool_mode: json` for that model in `configs/models.yaml`.
- **Claude Code** picks up `.mcp.json` automatically (it asks once to trust project servers) and expands `${VAR}` from your shell, not from `.env`: start it with `set -a; source .env; set +a; claude`.
- **Provenance:** `edgartools` is the official server of the edgartools library (dgunning/edgartools, MIT). `fred` is the npm package `fred-mcp-server` by Stefano Amorelli (AGPL-3.0; we only run it, we don't modify or ship it). Versions are pinned in `.mcp.json`. The `sh -c realpath` wrapper works around a bug in 1.2.0, which exits silently when launched through npx's symlink.
- **Secrets:** keys go in `.env` (git-ignored, as is any `*.env`). Never in `.mcp.json`, never in chat.

## Adding things

- **A model:** add an entry to `configs/models.yaml`. Any OpenAI-compatible server needs only `provider: openai_compat`, `base_url` and `model`. A new provider type means one class implementing `ChatModel.complete()` in `src/misroute/models/` and one line in `registry.py`.
- **An agent:** add a card to `agents/cards/`. See `skills/agent-card-authoring/SKILL.md`.
- **A skill:** add `skills/<name>/SKILL.md` with `name` and `description` frontmatter, then list it under `skills:` in a card.
- **A data server:** add it to `.mcp.json` (secrets as `${VAR}`), add the variable to `.env.template`, list the server under `tools:` in the cards that may use it, and add a smoke call to `scripts/check_tools.py`.
- **A detector:** subclass `Detector` in `src/misroute/detectors/` and register it in `detectors/__init__.py`.
- **A misroute type or injection:** `taxonomy.py` and `inject.py`.

## Working with Claude Code

`CLAUDE.md` loads `AGENTS.md` and `docs/HANDOVER.md` (project state, outstanding work, gotchas). Personal preferences go in `CLAUDE.local.md`, which is git-ignored.

## Status

Scaffold only. The use case (quant research desk) is Mark's preference and not a team decision; the cards are an example. See `docs/spec-notes.md` for the spec wording and its known gaps.
