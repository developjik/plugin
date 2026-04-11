#!/bin/sh
# SessionStart hook for the dev-kit plugin.
# Builds passive additionalContext from session summary, progress, handoff,
# and compound learnings without steering workflow entry or resume behavior.

set -euo pipefail

PLUGIN_DIR="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)}}"

# ── 1. Resolve workspace root ──

WORKSPACE_ROOT=""
HOOK_PAYLOAD=""
if [ -n "${DEV_KIT_STATE_ROOT:-}" ]; then
  WORKSPACE_ROOT="$DEV_KIT_STATE_ROOT"
elif [ ! -t 0 ]; then
  HOOK_PAYLOAD="$(cat)"
  WORKSPACE_ROOT="$(
    printf '%s' "$HOOK_PAYLOAD" | python3 "$PLUGIN_DIR/scripts/dev_kit_state.py" resolve-workspace-root 2>/dev/null || true
  )"
fi

# ── 2. Query session summary ──

SUMMARY_LINE=""
if [ -n "$WORKSPACE_ROOT" ]; then
  SUMMARY_LINE="$(python3 "$PLUGIN_DIR/scripts/dev_kit_state.py" summary --workspace-root "$WORKSPACE_ROOT" 2>/dev/null || true)"
else
  SUMMARY_LINE="$(python3 "$PLUGIN_DIR/scripts/dev_kit_state.py" summary 2>/dev/null || true)"
fi

# ── 2a. Gather extended session context ──

EXTENDED_CONTEXT=""
HAS_ACTIVE_SESSION=0
case "$SUMMARY_LINE" in
  *" | "*)
    HAS_ACTIVE_SESSION=1
    ;;
esac

SESSION_ID=""
if [ "$HAS_ACTIVE_SESSION" -eq 1 ]; then
  SESSION_ID="$(printf '%s' "$SUMMARY_LINE" | sed -n 's/^Dev Kit: \([^ |]*\).*/\1/p')"
fi

if [ -n "$WORKSPACE_ROOT" ] && [ -n "$SESSION_ID" ]; then
  SESSION_DIR="$WORKSPACE_ROOT/.dev-kit/sessions/$SESSION_ID"

  PROGRESS_FILE="$SESSION_DIR/progress.md"
  if [ -f "$PROGRESS_FILE" ]; then
    EXTENDED_CONTEXT="${EXTENDED_CONTEXT}

Recent Progress:
$(tail -n 12 "$PROGRESS_FILE" | sed 's/^/  /')"
  fi

  HANDOFF_FILE="$SESSION_DIR/handoff.md"
  if [ -f "$HANDOFF_FILE" ]; then
    HANDOFF_SECTION="$(awk '/^## Resume Point$/{f=1;next}/^## /{f=0}f' "$HANDOFF_FILE" | head -n 8 | sed 's/^/  /')"
    if [ -n "$HANDOFF_SECTION" ]; then
      EXTENDED_CONTEXT="${EXTENDED_CONTEXT}

Handoff Resume Point:
${HANDOFF_SECTION}"
    fi
  fi
fi

# ── 2b. Gather compound learnings context ──

LEARNINGS_CONTEXT=""
if [ -n "$WORKSPACE_ROOT" ] && [ -f "$WORKSPACE_ROOT/.dev-kit/learnings/index.json" ]; then
  LEARNINGS_CONTEXT="$(python3 "$PLUGIN_DIR/scripts/dev_kit_state.py" learnings-summary --workspace-root "$WORKSPACE_ROOT" 2>/dev/null || true)"
fi

# ── 3. Build session-aware context ──

if [ "$HAS_ACTIVE_SESSION" -eq 1 ]; then
  SESSION_BLOCK="## Active Session

$SUMMARY_LINE$EXTENDED_CONTEXT"
else
  SESSION_BLOCK="## No Active Session

No active Dev Kit session found in this workspace."
fi

if [ -n "$LEARNINGS_CONTEXT" ]; then
  SESSION_BLOCK="$SESSION_BLOCK

## Compound Learnings

$LEARNINGS_CONTEXT

Use these learnings as passive context during explicitly invoked clarify and planning phases."
fi

# ── 4. Output JSON with additionalContext ──

ESCAPED_CONTEXT="$(printf '%s' "$SESSION_BLOCK" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$ESCAPED_CONTEXT"
