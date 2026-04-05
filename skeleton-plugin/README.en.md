# Plugin Skeleton

Unified plugin skeleton that supports both Codex and Claude Code platforms. All common components are included but intentionally minimal.

## Purpose

This plugin is a starting template. It includes the standard files and folders needed to build a plugin that works on both Codex and Claude Code, while leaving implementation details empty or marked with placeholders.

## Platform Support

| Component | Codex | Claude Code | Notes |
|-----------|:-----:|:-----------:|-------|
| `skills/` | O | O | Same format (`SKILL.md`) |
| `commands/` | O | O | Slash commands (`.md`) |
| `hooks/hooks.json` | O | O | Same format (compatible) |
| `.mcp.json` | O | O | Same format |
| `.app.json` | O | - | Codex only |
| `.codex-plugin/` | O | - | Codex manifest |
| `.claude-plugin/` | - | O | Claude Code manifest |

## Included pieces

### Platform Manifests

- `.codex-plugin/plugin.json`
  - Required Codex plugin manifest.
  - Defines plugin name, metadata, UI-facing interface data (`interface` block), and relative paths to bundled components.

- `.claude-plugin/plugin.json`
  - Claude Code plugin manifest.
  - Defines plugin name, metadata, and relative paths to bundled components.
  - More concise than the Codex manifest — no `interface` block.

### Shared Components (Cross-platform)

- `skills/`
  - Holds bundled skills. Each skill lives in its own folder with a `SKILL.md`.
  - Use for reusable workflow instructions inside the plugin.

- `commands/`
  - Holds slash commands as `.md` files (e.g., `help.md` → `/skeleton:help`).
  - Use for user-invocable commands.

- `hooks/hooks.json`
  - Hook configuration file. Both platforms use the same format.
  - Included hook types:
    - `SessionStart` — on session start/resume
    - `PreToolUse` — before tool execution
    - `PostToolUse` — after tool execution
    - `PostToolUseFailure` — on tool failure (Claude Code)
    - `UserPromptSubmit` — on prompt submission
    - `Notification` — on notification events (Claude Code)
    - `Stop` — on session stop
    - `SubagentStop` — on subagent stop (Claude Code)

- `hooks/*.sh`
  - Placeholder shell scripts for hook entrypoints.
  - Path references use `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-.}}` to support both platform environment variables.

- `.mcp.json`
  - Placeholder for MCP server definitions.

### Codex-only Components

- `.app.json`
  - Placeholder for app or connector mappings.

### Shared Directories

- `scripts/` — Local helper scripts for the plugin or bundled skills.
- `assets/` — Icons, logos, screenshots, and other visual files.

## Recommended next steps

1. Replace `[TODO: ...]` placeholders in the target platform manifest(s).
   - Codex only: `.codex-plugin/plugin.json`
   - Claude Code only: `.claude-plugin/plugin.json`
   - Both: update both files
2. Replace the starter skill in `skills/` with real workflow skills.
3. Replace or add commands in `commands/`.
4. Keep only the hooks you need; remove the rest.
5. Add MCP servers, app mappings, scripts, and assets only as needed.

## Notes

- This is a full skeleton, not a finished plugin.
- Empty directories are preserved with `.gitkeep` files.
- The hook format is compatible across both platforms, so a single `hooks.json` serves both.
- If targeting only one platform, you may delete the unused manifest directory.
