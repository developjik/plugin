# Plugins Workspace

English | [한국어](./README.ko.md)

This repository is a workspace for local plugins used with Codex and Claude Code. Each plugin directory stays self-contained with its own manifests, skills, hooks, scripts, tests, and documentation, while the repository root holds shared docs and marketplace metadata.

## Installation

The repository root is not itself a plugin. Install one of the plugin directories listed below with the matching platform guide.

- [Codex Local Plugin Install Guide](./docs/guides/install/codex-local-plugin-install.md)
- [Claude Code Local Plugin Install Guide](./docs/guides/install/claude-code-local-plugin-install.md)

## Current Plugin Directories

| Plugin | Purpose | Documentation |
|---|---|---|
| `dev-kit` | Structured development workflow plugin with `clarify -> planning -> execute -> review-execute`, plus debugging and code-quality support skills. | [English](./dev-kit/README.md) / [Korean](./dev-kit/README.ko.md) |
| `harness-design-kit` | Planner-generator-evaluator harness plugin for long-running application development, frontend iteration, live evaluation, and reset handoffs. | [English](./harness-design-kit/README.md) / [Korean](./harness-design-kit/README.ko.md) |
| `skeleton-plugin` | Starter template for building a plugin that supports both Codex and Claude Code. | [English](./skeleton-plugin/README.en.md) / [Korean](./skeleton-plugin/README.md) |

Use this directory list as the source of truth for what is currently present in the workspace.

## Shared Docs

| Path | Contents |
|---|---|
| [Docs Index](./docs/README.md) | Top-level guide to the repository documentation tree |
| [`docs/guides/install/`](./docs/guides/install/) | Local installation guides for Codex and Claude Code in English and Korean |
| [Anthropic Harness Series](./docs/series/anthropic-harness/README.ko.md) | Korean reading series for Anthropic and Claude harness articles |
| [OpenAI/Codex Harness Series](./docs/series/openai-codex-harness/README.ko.md) | Korean reading series for OpenAI and Codex harness articles |
| [`docs/research/`](./docs/research/) | Research notes, link collections, and repository analyses |

## Repository Layout

```text
plugins/
├── README.md
├── README.ko.md
├── .claude-plugin/
│   └── marketplace.json
├── docs/
│   ├── guides/
│   ├── research/
│   └── series/
├── dev-kit/
├── harness-design-kit/
└── skeleton-plugin/
```

Other hidden workspace directories are omitted from this simplified tree.

## Working In This Repo

1. Open the plugin directory you want to work on.
2. Read that plugin's README before editing manifests, hooks, skills, or scripts.
3. Keep plugin-specific state, schemas, tests, and assets inside the plugin directory.
4. Use `docs/` for shared guides, translated series, and research material that applies across plugins.

## Notes

- The repository root is documentation plus marketplace metadata, not an installable plugin.
- The root [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) can contain draft metadata in addition to the directories currently checked into this workspace.

## Language Notes

- The repository root uses `README.md` for English and `README.ko.md` for Korean.
- `dev-kit` and `harness-design-kit` follow the same English/Korean split.
- `skeleton-plugin` keeps English in `README.en.md` and Korean in `README.md`.
- `docs/series/` and most `docs/research/` content are currently Korean-first.
