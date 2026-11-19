# Spec 41 notes

Quote the spec; do not paraphrase type names.

From the Scope:

> A taxonomy of misrouting failure modes — capability mismatch, context mismatch, authority mismatch, semantic misinterpretation

Detectors named in the spec:

- "a capability-profile consistency check between instruction intent and the receiving agent's profile" → `src/misroute/detectors/capability_check.py`
- "an output anomaly detector using contrastive scoring against what a correctly-routed agent would produce" → `src/misroute/detectors/contrastive.py`

Evaluation: precision, recall and detection latency against injected ground truth → `src/misroute/eval.py`.

Known gaps in the spec:

- The Overview and deliverables list three injected types and omit authority mismatch. We keep all four.
- It never defines what an agent's capability profile contains. Our definition is the agent card (`skills/agent-card-authoring/SKILL.md`): capability, context scope, authority.

Baseline to beat (from own web search, not yet read in full): "When Agentic Executions Fail" (arXiv 2608.14680), which injects agent-misroute faults into LangGraph, CrewAI and AutoGen and detects with a zero-shot LLM over traces.
