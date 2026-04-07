# Codex Local Plugin Install Guide

This document explains how to install and use a local plugin from this repository in Codex.

For the official background, see the OpenAI Codex plugin documentation.

- [Build plugins](https://developers.openai.com/codex/plugins/build?install-scope=global)

## Overview

Codex does not load local plugin folders by scanning arbitrary directories. Instead, it installs local plugins through a `marketplace.json` entry that appears in the Plugin Directory.

For local use, you need two things:

1. A Codex plugin manifest inside the plugin folder
2. A local marketplace entry that Codex can read

This repository's `dev-kit` plugin already includes a Codex manifest.

- [dev-kit/.codex-plugin/plugin.json](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/dev-kit/.codex-plugin/plugin.json)

## Installation Modes

There are two common ways to expose local plugins to Codex.

- repo-scoped marketplace
  - Visible only inside the current repository
  - Path: `$REPO_ROOT/.agents/plugins/marketplace.json`
- personal marketplace
  - Visible across your local Codex environment
  - Path: `~/.agents/plugins/marketplace.json`

For personal development, the personal marketplace is usually the simplest choice.

## 1. Verify the Plugin Layout

Your plugin folder should include at least:

```text
<plugin>/
└── .codex-plugin/
    └── plugin.json
```

Example:

```text
dev-kit/
└── .codex-plugin/
    └── plugin.json
```

## 2. Create the Marketplace File

For a personal marketplace:

```text
~/.agents/plugins/marketplace.json
```

For a repo-scoped marketplace:

```text
$REPO_ROOT/.agents/plugins/marketplace.json
```

## 3. Register the Local Plugin in `marketplace.json`

This example registers `dev-kit` from this repository in a personal marketplace.

```json
{
  "name": "local-plugins",
  "interface": {
    "displayName": "Local Plugins"
  },
  "plugins": [
    {
      "name": "dev-kit",
      "source": {
        "source": "local",
        "path": "./Library/Mobile Documents/com~apple~CloudDocs/plugins/dev-kit"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
```

Notes:

- In a personal marketplace, paths are resolved relative to your home directory.
- In a repo-scoped marketplace, paths are resolved relative to the repository root.
- Using a relative `source.path` from the marketplace file is the safest option.

For example, if you create a repo-scoped marketplace in this repository root, the `dev-kit` entry can use:

```json
{
  "source": {
    "source": "local",
    "path": "./dev-kit"
  }
}
```

## 4. Restart Codex

After creating or updating `marketplace.json`, restart Codex.

## 5. Install from the Plugin Directory

After restarting Codex:

1. Open the Plugin Directory.
2. Confirm that `Local Plugins` appears.
3. Open it and find the plugin you want, such as `dev-kit`.
4. Install the plugin.

After installation, Codex may use a cached copy of the plugin, so if you change the source later, restart Codex and verify that the updated version is being used.

## How To Verify

Use this sequence:

1. Restart Codex.
2. Check whether `Local Plugins` appears in the Plugin Directory.
3. Confirm that `dev-kit` is listed.
4. Install it and verify that its skills or plugin behavior are available in a new conversation.

## Troubleshooting

### The marketplace does not appear

- Verify the `marketplace.json` path.
- Check for JSON syntax errors.
- Make sure Codex was fully restarted.

### The plugin does not appear in the list

- Verify that the plugin folder contains `.codex-plugin/plugin.json`.
- Verify that `source.path` is correct relative to the marketplace file.

### Changes do not show up after installation

- Restart Codex.
- Reinstall or reload the plugin if needed.
- Assume Codex may still be using a cached installed copy first.

## Example In This Repository

In this repository, `dev-kit` can be exposed as a local plugin.

- Repository root: [/Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins)
- Plugin path: [/Users/developjik/Library/Mobile Documents/com~apple~CloudDocs/plugins/dev-kit](/Users/developjik/Library/Mobile%20Documents/com~apple~CloudDocs/plugins/dev-kit)
- Personal marketplace example: [/Users/developjik/.agents/plugins/marketplace.json](/Users/developjik/.agents/plugins/marketplace.json)
