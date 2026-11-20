# Status: what is here, what is not

Last updated 20 Nov 2026. This is the public status page for the repo. It is a prototype scaffold for a student team project (Oxford Edge AI/ML Challenge, spec 41: "Detecting Misrouted Instructions in Hierarchical Agent Systems"), built in a few days. **No team decision has been made yet on direction, use case or framework**, and the quant research desk here is an example, not the project.

Read the repo as a buffet: it has more components than a six-week project will use, so the team can choose. Nothing here implements a full architecture.

## The short version

- **No request has been routed or answered by a real model.** Every test and demo run uses an offline `echo` model. The demo's perfect scores are a plumbing check, not a result: the injected faults and the keyword detector share one vocabulary.
- The data tools are real: eleven tool servers start, and ten have returned live data from direct calls.
- The wiring page (`docs/research-desk-wiring.html`) is a drawing with scripted traces. Only one of its four wirings exists in code, and only for a single hop.

## What works (tested)

| Piece | State |
| --- | --- |
| Agent cards (7), intents, scopes | Load and validate. Example desk: router, market-data, filings, news, macro, backtest, compliance. |
| Skills loader | Own skills plus Anthropic's finance skills (vendored, Apache 2.0, unmodified). |
| Routers | Keyword baseline; LLM router (any model, untested with a real one). |
| Fault injection | Four operators, one per misroute type in the spec. |
| Detectors | Capability-profile check, contrastive output (token overlap, arbitrary threshold), self-report, tool-call. Offline only, uncalibrated. |
| Evaluation | Precision, recall, per-type recall, detection latency. |
| Tool servers | 11 in `.mcp.json`; see the README table. Agents only get the servers their card lists. |
| Tests | 22 pass offline with no keys (`pytest -q`). |

## Wired but not set up

These have code and configuration but have never been run for real.

- **Model adapters:** Anthropic and any OpenAI-compatible endpoint. No model key is configured, so neither has made a call.
- **Model registry entries** for Claude, Ollama (Qwen, Llama), vLLM, OpenRouter, Groq and Together: names in a YAML file until someone supplies a key or a server.
- **Agents using tools:** the tool loop is tested against a fake server and by direct calls, not by a model deciding to call a tool.
- **Backtest runner:** passes offline tests; never run on real prices.
- **Finnhub server:** a community package whose code has not been reviewed.

## Not here

- A gate that decides between routing and deferring to a person, and any calibration or statistical guarantee. Where that sits is deliberately open.
- A decision model (for example Jev) or a text diffusion model (for example d1) as router. Named on the wiring page as candidates only.
- Peer-to-peer, per-person and second-opinion wirings. Drawn, not built.
- Research agents that collect from the web, a signal compiler, a data-analysis agent, subject-expert agents, a positions agent. Proposals on the wiring page; "Source A" to "Source C" are placeholders.
- A real request set, labelled data, traces in Langfuse, a reproduced baseline.
- A licence. Until the team picks one, the code is public to read but not licensed for reuse (the vendored skills keep their own Apache 2.0 licence).

## What it is compatible with

- **Models:** anything behind an OpenAI-compatible endpoint needs only a `base_url` and a model name in `configs/models.yaml`. That covers Ollama on a laptop and vLLM on a GPU server, including one on an AWS EC2 instance. Amazon Bedrock is not wired; it would need a small adapter or a proxy.
- **Tools:** any MCP server. `.mcp.json` is read by Claude Code and by the framework, so people and agents use the same servers.
- **Keys:** only in `.env` (git-ignored). `python scripts/set_key.py NAME` stores one from a hidden prompt.

## Next step

Agree a framework the whole team is happy to work in, and that is realistic for six weeks. Candidates: keep this small in-house code; move orchestration to LangGraph (the wiring becomes configuration, and tracing comes with it); or something else the team prefers. The parts meant to survive that choice are the cards, the misroute taxonomy, the injection operators, the detectors and the evaluation.

## Rules for this public repo

No names of team members or mentors, no sponsor-internal details, no keys. Say "the sponsor". See `AGENTS.md`.
