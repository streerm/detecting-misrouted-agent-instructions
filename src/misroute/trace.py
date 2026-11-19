"""Minimal JSONL tracing. Field names follow Langfuse's trace/span shape so a later exporter is trivial."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path


class Tracer:
    def __init__(self, path: str | Path | None):
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def span(self, trace_id: str, name: str, input=None, output=None, **metadata) -> None:
        if not self.path:
            return
        rec = {"id": uuid.uuid4().hex, "trace_id": trace_id, "name": name, "timestamp": time.time(),
               "input": input, "output": output, "metadata": metadata}
        with self.path.open("a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
