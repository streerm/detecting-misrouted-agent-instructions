"""Store one secret in .env without it ever appearing on screen, in shell history or in a chat.

  python scripts/set_key.py ALPHAVANTAGE_API_KEY     # paste the key at the hidden prompt, press Enter
  python scripts/set_key.py --status                 # which variables are set (names only)
"""
from __future__ import annotations

import getpass
import re
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / ".env"
NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


def value_of(line: str) -> str:
    return re.split(r"(?:^|\s+)#", line.split("=", 1)[1].strip(), maxsplit=1)[0].strip()


def status() -> None:
    for line in ENV.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            print(f"{'set  ' if value_of(line) else 'empty'}  {line.split('=', 1)[0].strip()}")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--status":
        return status()
    name = sys.argv[1]
    if not NAME.match(name):
        sys.exit(f"{name!r} is not a variable name like ALPHAVANTAGE_API_KEY")
    value = getpass.getpass(f"Paste {name} (hidden), then Enter: ").strip()
    if not value or any(c in value for c in "\n\r"):
        sys.exit("nothing stored")
    lines = ENV.read_text().splitlines() if ENV.exists() else []
    for i, line in enumerate(lines):
        if re.match(rf"^\s*{name}=", line):
            lines[i] = f"{name}={value}"
            break
    else:
        lines.append(f"{name}={value}")
    ENV.write_text("\n".join(lines) + "\n")
    print(f"stored {name} ({len(value)} characters) in .env")


if __name__ == "__main__":
    main()
