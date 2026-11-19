---
name: misroute-labelling
description: Protocol for labelling a routed instruction as correct or as a specific misroute type, for building ground truth or judging traces. Use when annotating requests, reviewing traces, or acting as an LLM judge.
---

# Misroute labelling protocol

## Inputs

The instruction, the agent it was sent to (with its card), the gold agent if known, and the output.

## Decide in this order

1. **Was it sent to the gold agent?** If yes and the output answers what was asked, label `correct`. If yes but the output answers a different reading of the instruction, label `semantic_misinterpretation`.
2. If not sent to the gold agent, compare the instruction with the receiving card:
   - needs an intent or input the agent lacks → `capability_mismatch`
   - needs data, a domain or a period outside `context_scope` → `context_mismatch`
   - asks for an action above `authority.level` or in `may_not` → `authority_mismatch`
3. If more than one applies, record all and mark the **first** in the order above as primary.
4. If you cannot tell, label `unsure` with a one-line reason. Never guess to fill a gap.

## Output (one JSON object per item)

```json
{"id": "...", "label": "context_mismatch", "secondary": [], "evidence": "card filings: out_of_scope includes live_prices; instruction asks for today's close", "confidence": 0.8}
```

## Quality

- Two labellers per item for the gold set; disagreements go to a third.
- Report Cohen's kappa per type.
- Keep a short rationale; the rationale is what lets us audit LLM judges later.
- Spec wording for the four types is in `docs/spec-notes.md`; use those names exactly.
