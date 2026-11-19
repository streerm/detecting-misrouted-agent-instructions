---
name: agent-card-authoring
description: How to write or review an agent card (agents/cards/*.yaml) describing an agent's capability, context scope and authority. Use when adding an agent, changing what an agent may do, or checking whether an instruction fits an agent.
---

# Agent card authoring

An agent card is the agent's **capability profile**. The spec never defines what a capability profile contains; this is our definition. Keep it small enough that a detector (or a person) can check an instruction against it.

## Fields

```yaml
id: filings                     # unique, kebab-case
name: Filings analyst
description: One sentence a router would read.
role: specialist                # router | specialist | supervisor
parent: router                  # who routes to this agent (builds the hierarchy)

capability:                     # WHAT it can do: verbs on objects
  intents: [extract_figure, compare_sections, summarise_filing]
  inputs:  [ticker, cik, filing_type, period, section]
  outputs: [table, quote_with_citation]

context_scope:                  # WHAT it can see / knows about
  domains: [sec_filings]
  data_sources: [sec_edgar]     # keys in configs/data_sources.yaml
  periods: "fiscal, as reported in filings"
  out_of_scope: [live_prices, macro_series]

authority:                      # WHAT it may change or approve
  level: read_only              # read_only | propose | execute | approve
  may: [read_filings]
  may_not: [place_orders, approve_trades, send_external]

skills: [finance-research-rules, source-cross-check]   # folders in skills/
tools: []                       # MCP server or function names
model: default                  # name in configs/models.yaml; override per experiment
```

## Rules

- `capability.intents` are verbs from a shared vocabulary. Add new intents to `agents/intents.yaml` so detectors can compare them.
- Put the things an agent must **not** do in `out_of_scope` and `authority.may_not`. Detectors use the negatives more than the positives.
- One card per agent. No prompts in Python: behaviour comes from card + skills.
- `model` is a *name*, not a vendor. Swapping Claude for Qwen is a config change.

## Mapping to the spec's misroute types

| Spec type | Card field it violates |
| --- | --- |
| capability mismatch | `capability.intents` / `inputs` |
| context mismatch | `context_scope` |
| authority mismatch | `authority` |
| semantic misinterpretation | none directly: the right agent, wrong reading. Needs the output detector. |
