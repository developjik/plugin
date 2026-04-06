#!/bin/sh

PLUGIN_DIR="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)}}"

WORKSPACE_ROOT=""
if [ ! -t 0 ]; then
  HOOK_PAYLOAD="$(cat)"
  WORKSPACE_ROOT="$(
    printf '%s' "$HOOK_PAYLOAD" | python3 -c '
from __future__ import annotations

import json
import sys
from pathlib import Path


def nearest_dev_kit_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        state_root = candidate / ".dev-kit"
        if (state_root / "current.json").is_file():
            return candidate
        if (state_root / "sessions").is_dir():
            return candidate
    return None


raw = sys.stdin.read()
if not raw.strip():
    raise SystemExit(0)

try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    raise SystemExit(0)

cwd = payload.get("cwd")
if not isinstance(cwd, str) or not cwd:
    raise SystemExit(0)

root = nearest_dev_kit_root(Path(cwd).expanduser().resolve())
if root is not None:
    print(root)
'
  )"
fi

if [ -n "$WORKSPACE_ROOT" ]; then
  python3 "$PLUGIN_DIR/scripts/dev_kit_state.py" summary --workspace-root "$WORKSPACE_ROOT" || true
else
  python3 "$PLUGIN_DIR/scripts/dev_kit_state.py" summary || true
fi
