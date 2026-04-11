# Claude Code Local Plugin Install Guide

This document explains how to install and use local plugins from this repository in Claude Code.

The official reference is the Anthropic Claude Code plugin documentation.

- [Discover and install prebuilt plugins through marketplaces](https://code.claude.com/docs/en/discover-plugins)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)

## Overview

Claude Code does not use arbitrary local plugin folders directly. You first add a marketplace, then install plugins from that marketplace.

The official flow is:

1. Prepare a marketplace that contains `.claude-plugin/marketplace.json`
2. Add it with `/plugin marketplace add ...`
3. Install a plugin with `/plugin install plugin-name@marketplace-name`
4. Apply it to the current session with `/reload-plugins`

## Current State Of This Repository

This repository already includes a Claude Code marketplace.

- marketplace file: [/.claude-plugin/marketplace.json](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/.claude-plugin/marketplace.json)
- `dev-kit` manifest: [/dev-kit/.claude-plugin/plugin.json](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/dev-kit/.claude-plugin/plugin.json)
- `skeleton-plugin` manifest: [/skeleton-plugin/.claude-plugin/plugin.json](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/skeleton-plugin/.claude-plugin/plugin.json)

The current marketplace name is `developjik-plugins`.

## Installation

### Option 1: Add the repository directory as a marketplace

Open Claude Code in this repository root and run:

```text
/plugin marketplace add /Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins
```

Per the official docs, a local directory can be added directly if it contains `.claude-plugin/marketplace.json`.

### Option 2: Add the marketplace file directly

You can also add the file path directly:

```text
/plugin marketplace add /Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins/.claude-plugin/marketplace.json
```

## Install A Plugin

After adding the marketplace, install the plugin you want.

Install `dev-kit`:

```text
/plugin install dev-kit@developjik-plugins
```

Install `skeleton-plugin`:

```text
/plugin install skeleton-plugin@developjik-plugins
```

Per the official docs, the default install scope is `user`, which makes the plugin available across your Claude Code environment.

If you need a different scope, use the `/plugin` UI.

- `user`
  - Available to you across all projects
- `project`
  - Shared with collaborators in the current repository
- `local`
  - Personal to this repository only

## Apply The Change To The Current Session

After installing, run:

```text
/reload-plugins
```

The official docs recommend `/reload-plugins` after install, enable, or disable so changes apply without restarting Claude Code.

## How To Verify

Use this sequence:

1. Run `/plugin marketplace list` and confirm `developjik-plugins` is present.
2. Open `/plugin` and check the `Installed` tab for `dev-kit` or `skeleton-plugin`.
3. Run `/reload-plugins` and confirm the plugin counts refresh.
4. Verify that plugin-provided skills, hooks, or MCP behavior are available.

## How Updates Work

The official docs note that installed plugins may be copied into a cache. Because of that, paths that reference files outside the plugin directory can break, and source changes may require reinstalling or reloading.

After changing a plugin, this sequence is usually safe:

1. `/plugin marketplace update developjik-plugins`
2. If needed, `/plugin uninstall dev-kit@developjik-plugins`
3. `/plugin install dev-kit@developjik-plugins`
4. `/reload-plugins`

## Troubleshooting

### `/plugin` is not available

Check your Claude Code version first:

```text
claude --version
```

If needed, update Claude Code, restart your terminal, and launch `claude` again.

### The marketplace does not load

- Confirm that the path really contains `.claude-plugin/marketplace.json`
- Check for JSON syntax errors
- Try adding the direct file path instead of the directory path

### The plugin installs but does not appear active

- Run `/reload-plugins`
- Check the `Installed` tab in `/plugin`
- Reinstall if needed

### Skills do not appear

Per the official docs, this can be a cache issue. If needed, clear the plugin cache:

```text
rm -rf ~/.claude/plugins/cache
```

Then restart Claude Code and reinstall the plugin.

### You need deeper debugging

The official docs recommend:

```text
claude --debug
```

Or validate plugin files:

```text
claude plugin validate
```

## Shortest Working Flow For This Repository

From this repository root, open Claude Code and run:

```text
/plugin marketplace add /Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins
/plugin install dev-kit@developjik-plugins
/reload-plugins
```
