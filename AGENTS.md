# AGENTS.md

Instructions for any coding agent (Claude Code, Codex, Cursor, Copilot, Aider…) working in this repo. `CLAUDE.md` points here.

## Ground rules

- Keep the framework model-agnostic. Nothing in `src/misroute/` outside `models/` may import a vendor SDK. Vendor SDKs are optional extras and are imported lazily inside their adapter.
- Every agent behaviour comes from its card and skills, not from hard-coded prompts in Python.
- Tests must pass offline with no API keys (`pytest -q`). Use the `echo` model in tests.
- Quote the spec exactly when naming misroute types; see `docs/spec-notes.md`.
- Never commit `.env`, keys, tokens, or raw the sponsor material.
- Prices and financial figures in any example must come from live data or a filing, with an as-of date, never from model memory (see `skills/finance-research-rules`).

## Commands

```bash
pip install -e ".[dev]"
pytest -q
python scripts/run_demo.py [--model NAME] [--router-model NAME]
```
