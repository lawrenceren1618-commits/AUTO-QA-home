#!/usr/bin/env python3
"""Check AutoQA env vars exist without printing secrets."""

from __future__ import annotations

import os
from pathlib import Path

KEYS = ("SELLERSPRITE_SECRET_KEY", "SIF_SECRET_KEY")
OPTIONAL = ("SORFTIME_MCP_KEY",)


def _from_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _present(name: str, dotenv: dict[str, str]) -> str:
    os_val = os.environ.get(name, "").strip()
    file_val = dotenv.get(name, "").strip()
    if os_val:
        return "os"
    if file_val:
        return "dotenv-only"
    return "missing"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    dotenv = _from_dotenv(root / "env" / ".env")
    worst = 0
    for k in KEYS:
        state = _present(k, dotenv)
        if state == "os":
            print(f"{k}: set in Windows/process env (MCP can see this after Cursor restart)")
        elif state == "dotenv-only":
            print(f"{k}: filled in .env but NOT in process env — MCP will still fail until you set the User env var and restart Cursor")
            worst = max(worst, 2)
        else:
            print(f"{k}: missing")
            worst = max(worst, 1)
    for k in OPTIONAL:
        print(f"{k}: {_present(k, dotenv)} (optional)")
    return 1 if worst == 1 else 0


if __name__ == "__main__":
    raise SystemExit(main())
