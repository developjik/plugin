#!/bin/sh

PLUGIN_HOME="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}}"
python3 "$PLUGIN_HOME/scripts/harness_state.py" append-event user_prompt_submitted '{"hook":"UserPromptSubmit"}' >/dev/null 2>&1 || true
python3 "$PLUGIN_HOME/scripts/harness_run.py" check-reset >/dev/null 2>&1 || true
python3 "$PLUGIN_HOME/scripts/harness_state.py" summary 2>/dev/null || true
