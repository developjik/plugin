# Plugins Workspace

English | [한국어](./README.ko.md)

This repository contains local plugins used with Codex and Claude Code. Each plugin lives in its own directory and keeps its own manifests, skills, hooks, scripts, and documentation.

For local installation in Codex, see the separate guide.

- [Codex Local Plugin Install Guide](./docs/codex-local-plugin-install.md)

For local installation in Claude Code, see the separate guide.

- [Claude Code Local Plugin Install Guide](./docs/claude-code-local-plugin-install.md)

## Included Plugins

| Plugin | Purpose | Documentation |
|---|---|---|
| `dev-kit` | Structured development workflow plugin with the visible flow `clarify -> planning -> execute -> review-execute`. | [English](./dev-kit/README.md) / [Korean](./dev-kit/README.ko.md) |
| `skeleton-plugin` | Starter template for building a plugin that supports both Codex and Claude Code. | [English](./skeleton-plugin/README.en.md) / [Korean](./skeleton-plugin/README.md) |

## Repository Layout

```text
plugins/
├── README.md
├── README.ko.md
├── docs/
├── dev-kit/
└── skeleton-plugin/
```

## How To Use This Repository

1. Open the plugin directory you want to work on.
2. Read that plugin's README before editing manifests, hooks, or skills.
3. Treat each plugin as an independent package with its own lifecycle and release surface.

## Notes

- The repository root is documentation and organization only. It is not itself a plugin.
- Plugin-specific state, schemas, tests, and assets stay inside each plugin directory.
- Language policy in this repository is:
  - `README.md` for English when present at the repository root or inside `dev-kit`
  - `README.ko.md` for Korean when present at the repository root or inside `dev-kit`
  - `skeleton-plugin` currently keeps English in `README.en.md` and Korean in `README.md`
