"""Spec metrics: precision, recall and detection latency against injected ground truth."""
from __future__ import annotations

from collections import defaultdict
from statistics import mean

from .taxonomy import MisrouteType


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
            "tp": tp, "fp": fp, "fn": fn}


def score(results) -> dict:
    tp = sum(r.flagged and r.case.misrouted for r in results)
    fp = sum(r.flagged and not r.case.misrouted for r in results)
    fn = sum(not r.flagged and r.case.misrouted for r in results)
    out = {"overall": prf(tp, fp, fn), "by_type": {}, "latency": {}}

    by = defaultdict(lambda: [0, 0])  # type -> [detected, total]
    typed = defaultdict(lambda: [0, 0])  # type -> [type correct, detected]
    for r in results:
        if r.case.label:
            by[r.case.label][1] += 1
            if r.flagged:
                by[r.case.label][0] += 1
                typed[r.case.label][1] += 1
                typed[r.case.label][0] += r.predicted_type == r.case.label
    for t in MisrouteType:
        d, n = by[t]
        c, k = typed[t]
        out["by_type"][t.value] = {"recall": d / n if n else None, "n": n,
                                   "type_accuracy": c / k if k else None}

    hits = [r for r in results if r.flagged and r.case.misrouted]
    out["latency"] = {
        "mean_steps": mean(r.detected_at_step for r in hits) if hits else None,
        "mean_ms": 1000 * mean(r.seconds_to_detect for r in hits) if hits else None,
    }
    return out


def format_report(s: dict) -> str:
    o = s["overall"]
    lines = [f"overall  precision {o['precision']:.2f}  recall {o['recall']:.2f}  f1 {o['f1']:.2f}"
             f"  (tp {o['tp']}, fp {o['fp']}, fn {o['fn']})", "", f"{'type':30} {'n':>3} {'recall':>7} {'type acc':>9}"]
    for t, v in s["by_type"].items():
        rec = "-" if v["recall"] is None else f"{v['recall']:.2f}"
        acc = "-" if v["type_accuracy"] is None else f"{v['type_accuracy']:.2f}"
        lines.append(f"{t:30} {v['n']:>3} {rec:>7} {acc:>9}")
    lat = s["latency"]
    if lat["mean_steps"] is not None:
        lines += ["", f"detection latency: mean {lat['mean_steps']:.2f} steps, {lat['mean_ms']:.1f} ms"]
    return "\n".join(lines)
