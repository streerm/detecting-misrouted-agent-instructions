# AGENTS.md

Instructions for any coding agent (Claude Code, Codex, Cursor, Copilot, Aider…) working in this repo. `CLAUDE.md` points here.

## Ground rules

- Keep the framework model-agnostic. Nothing in `src/misroute/` outside `models/` may import a vendor SDK. Vendor SDKs are optional extras and are imported lazily inside their adapter.
- Every agent behaviour comes from its card and skills, not from hard-coded prompts in Python.
- Tests must pass offline with no API keys (`pytest -q`). Use the `echo` model in tests.
- Quote the spec exactly when naming misroute types; see `docs/spec-notes.md`.
- Never commit `.env`, any `*.env`, keys, tokens, or raw sponsor material. Secrets appear in `.mcp.json` only as `${VAR}`.
- MCP servers are configured once in `.mcp.json` and shared by Claude Code and `src/misroute/tools/mcp_hub.py`; tool access per agent comes from its card's `tools:`.
- Our own MCP servers live in `mcp_servers/` (standard library + `mcp` only, read-only, every result carries `source` and `retrieved_at`). Prefer writing a small one over adding an unvetted community server.
- Prices and financial figures in any example must come from live data or a filing, with an as-of date, never from model memory (see `skills/finance-research-rules`).

## This repo is public

- No names of team members or mentors, and nothing from private team channels. Say "the sponsor", never the sponsor's name or the names of its internal systems.
- `docs/STATUS.md` is the public status page; keep it current and honest about what has and has not been run.
- Working notes that name people live in `docs/HANDOVER.md`, which is git-ignored and stays on the author's machine.

## Commands

```bash
pip install -e ".[dev]"
pytest -q
python scripts/run_demo.py [--model NAME] [--router-model NAME] [--tools]
python scripts/check_tools.py [SERVER ...] [--smoke]
```
