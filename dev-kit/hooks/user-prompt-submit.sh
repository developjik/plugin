#!/bin/sh

PLUGIN_DIR="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)}}"

DEV_KIT_SUMMARY_COMPACT=1 exec bash "$PLUGIN_DIR/hooks/render-session-summary.sh"
