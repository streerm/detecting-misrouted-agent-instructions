"""Tiny .env loader (no dependency). Existing environment variables win over the file."""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import REPO_ROOT

_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def load_dotenv(path: str | Path = REPO_ROOT / ".env") -> dict[str, str]:
    path = Path(path)
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip().removeprefix("export ").strip(), val.strip()
        if val[:1] in "\"'" and val[:1] and val[:1] in val[1:]:      # quoted: keep everything inside
            val = val[1:].split(val[0], 1)[0]
        else:                                                    # unquoted: drop "  # comment"
            val = re.split(r"(?:^|\s+)#", val, maxsplit=1)[0].strip()
        if key and val and key not in os.environ:
            os.environ[key] = val
            loaded[key] = val
    return loaded


def expand(value: str) -> str:
    """Expand ${VAR} and ${VAR:-default}, the same syntax Claude Code uses in .mcp.json."""
    def sub(m: re.Match) -> str:
        return os.environ.get(m.group(1), m.group(2) if m.group(2) is not None else "")
    return _VAR.sub(sub, value)


def missing_vars(value: str) -> list[str]:
    return [m.group(1) for m in _VAR.finditer(value) if m.group(2) is None and not os.environ.get(m.group(1))]
