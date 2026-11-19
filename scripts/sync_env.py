"""Rebuild .env from .env.template, keeping every value already set in .env. Never prints values.

  python scripts/sync_env.py        # run again whenever .env.template gains new lines
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINE = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def parse(path: Path) -> dict[str, str]:
    vals = {}
    if path.exists():
        for line in path.read_text().splitlines():
            m = LINE.match(line)
            if m and not line.lstrip().startswith("#"):
                v = m.group(3).strip()
                v = v if v[:1] in "\"'" else re.split(r"(?:^|\s+)#", v, maxsplit=1)[0].strip()
                if v:
                    vals[m.group(2)] = v
    return vals


def main() -> None:
    env, tpl = ROOT / ".env", ROOT / ".env.template"
    old = parse(env)
    out, used = [], set()
    for line in tpl.read_text().splitlines():
        m = LINE.match(line)
        if m and m.group(2) in old:
            comment = re.search(r"\s+#.*$", m.group(3))
            out.append(f"{m.group(2)}={old[m.group(2)]}" + (f"   {comment.group(0).strip()}" if comment else ""))
            used.add(m.group(2))
        else:
            out.append(line)
    extra = [k for k in old if k not in used]
    if extra:
        out += ["", "# ---- Other (kept from previous .env) ----"] + [f"{k}={old[k]}" for k in extra]
    if env.exists():
        shutil.copy2(env, ROOT / ".env.bak")
    env.write_text("\n".join(out) + "\n")
    env.chmod(0o600)
    print(f".env rebuilt from template; kept values for: {sorted(old) or 'none'}")


if __name__ == "__main__":
    main()
