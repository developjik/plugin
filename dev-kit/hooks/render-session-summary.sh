#!/bin/sh

PLUGIN_DIR="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)}}"
COMPACT_SUMMARY="${DEV_KIT_SUMMARY_COMPACT:-0}"

WORKSPACE_ROOT=""
if [ -n "${DEV_KIT_STATE_ROOT:-}" ]; then
  WORKSPACE_ROOT="$DEV_KIT_STATE_ROOT"
elif [ ! -t 0 ]; then
  HOOK_PAYLOAD="$(cat)"
  WORKSPACE_ROOT="$(
    printf '%s' "$HOOK_PAYLOAD" | python3 -c '
from __future__ import annotations

import json
import sys
import subprocess
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

start = Path(cwd).expanduser().resolve()
root = nearest_dev_kit_root(start)
if root is not None:
    print(root)
    raise SystemExit(0)

try:
    git_result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(start),
        check=True,
        capture_output=True,
        text=True,
    )
except (FileNotFoundError, subprocess.CalledProcessError):
    pass
else:
    git_root = git_result.stdout.strip()
    if git_root:
        print(git_root)
        raise SystemExit(0)

print(start)
'  
  )"
fi

if [ -n "$WORKSPACE_ROOT" ]; then
  SUMMARY_LINE="$(python3 "$PLUGIN_DIR/scripts/dev_kit_state.py" summary --workspace-root "$WORKSPACE_ROOT" 2>/dev/null || true)"
else
  SUMMARY_LINE="$(python3 "$PLUGIN_DIR/scripts/dev_kit_state.py" summary 2>/dev/null || true)"
fi

# Always print the existing summary line (backward compatible)
if [ -n "$SUMMARY_LINE" ]; then
  printf '%s\n' "$SUMMARY_LINE"
fi

# Extract session-id from the summary line (pattern: "Dev Kit: <session-id> |")
SESSION_ID="$(printf '%s' "$SUMMARY_LINE" | sed -n 's/^Dev Kit: \([^ |]*\).*/\1/p')"

# Show extended context when workspace root and session ID are available
if [ "$COMPACT_SUMMARY" = "1" ] || [ "$COMPACT_SUMMARY" = "true" ] || [ "$COMPACT_SUMMARY" = "TRUE" ]; then
  :
elif [ -n "$WORKSPACE_ROOT" ] && [ -n "$SESSION_ID" ]; then
  SESSION_DIR="$WORKSPACE_ROOT/.dev-kit/sessions/$SESSION_ID"
  PROGRESS_FILE="$SESSION_DIR/progress.md"

  # Show tail of progress.md if it exists
  if [ -f "$PROGRESS_FILE" ]; then
    printf '\nRecent Progress:\n'
    tail -n 12 "$PROGRESS_FILE" | sed 's/^/  /'
  fi

  # Show handoff.md resume point if it exists (context reset mode)
  HANDOFF_FILE="$SESSION_DIR/handoff.md"
  if [ -f "$HANDOFF_FILE" ]; then
    printf '\nHandoff Resume Point:\n'
    awk '/^## Resume Point$/{f=1;next}/^## /{f=0}f' "$HANDOFF_FILE" | head -n 8 | sed 's/^/  /'
  fi

  # Show recent git log (last 3 commits, one-line format)
  if git -C "$WORKSPACE_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    RECENT_GIT="$(git -C "$WORKSPACE_ROOT" log --oneline -3 2>/dev/null || true)"
    if [ -n "$RECENT_GIT" ]; then
      printf '\nRecent Commits:\n'
      printf '%s\n' "$RECENT_GIT" | sed 's/^/  /'
    fi
  fi
fi
