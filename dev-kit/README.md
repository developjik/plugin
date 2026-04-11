# Dev Kit

English | [한국어](./README.ko.md)

Dev Kit is a structured development workflow plugin for Claude Code and Codex. It gives normal implementation work one official path, keeps session state under `.dev-kit/`, and leaves debugging and code-quality review as explicit standalone skills.

## When To Use Dev Kit

Use the main Dev Kit flow when you want a tracked implementation workflow:

- Start a scoped feature or refactor and keep artifacts such as `brief.md`, `plan.md`, and `review.md`
- Resume interrupted work from `.dev-kit/current.json` or a resumable session
- Keep planning, execution, and final review explicitly separated

Use the standalone skills when the task is not normal feature execution:

- `systematic-debugging` for bugs, flaky tests, and unexpected behavior
- `simplify-code` or `clean-ai-slop` for post-change cleanup and review
- `rob-pike` for performance work
- `compound` for managing the learning store in `.dev-kit/learnings/`

## Installation

If you opened this README directly, install the plugin first:

- Codex: [../docs/guides/install/codex-local-plugin-install.md](../docs/guides/install/codex-local-plugin-install.md)
- Claude Code: [../docs/guides/install/claude-code-local-plugin-install.md](../docs/guides/install/claude-code-local-plugin-install.md)

## Workflow At A Glance

Dev Kit's official implementation flow is:

`clarify -> planning -> execute -> review-execute`

What this guarantees:

- `clarify` and `planning` are materialized before normal execution begins
- Hooks are read-only and never auto-start or auto-resume phases
- `planning` owns plan quality and execute readiness
- `execute` follows the approved plan instead of redesigning it
- `review-execute` performs final verification in isolation from execution context

## Quick Start

### Normal Feature Work

1. Start the workflow explicitly:

   ```text
   Use Dev Kit for this task. Run clarify for adding CSV export to the orders page.
   ```

2. After `clarify`, expect:
   - `.dev-kit/current.json`
   - `.dev-kit/sessions/<session-id>/state.json`
   - `.dev-kit/sessions/<session-id>/brief.md`

3. Continue with planning:

   ```text
   Run planning for the active Dev Kit session.
   ```

4. After `planning`, expect:
   - `.dev-kit/sessions/<session-id>/plan.md`
   - `.dev-kit/sessions/<session-id>/plan-review.md`

5. Execute the approved plan:

   ```text
   Execute the approved Dev Kit plan.
   ```

6. After `execute`, expect code changes plus execution artifacts such as:
   - `.dev-kit/sessions/<session-id>/progress.md`
   - `.dev-kit/sessions/<session-id>/checkpoints/*.json` for phased runs
   - `.dev-kit/sessions/<session-id>/handoff.md` when context reset mode is used

7. Run final verification:

   ```text
   Run review-execute for the active Dev Kit session.
   ```

8. After `review-execute`, expect:
   - `.dev-kit/sessions/<session-id>/review.md`
   - optionally `.dev-kit/sessions/<session-id>/compound.md` when a reusable learning is extracted

### Standalone Entries

```text
Debug this failing test with systematic-debugging.
Review the changed code with simplify-code.
Refresh the Dev Kit learning store with compound refresh.
```

## How Work Starts

For new work, `clarify` is the normal entry phase. It either runs a short discovery loop or uses direct clarify when the request is already concrete.

`planning` is still the mandatory pre-execute phase, but it can materialize direct-clarify artifacts itself when all of these are true:

- there is no resumable session
- the request is already concrete enough to plan
- a concise `brief.md` can be created immediately

That means "start with `clarify`" is the default rule, while "enter through `planning`" is the documented fast path for already-clear work.

## Core Phases

| Phase | What it does | Main outputs |
|---|---|---|
| `clarify` | Locks scope, success criteria, constraints, and technical context. Scores complexity and initializes session state. | `current.json`, `state.json`, `brief.md` |
| `planning` | Writes an executable plan, runs the internal `planner -> critic + readiness-checker` review bundle, and freezes an approved plan before execution. | `plan.md`, `plan-review.md` |
| `execute` | Carries out the approved plan through worker-validator loops, checkpointing, and resume-safe state updates. | code changes, `progress.md`, optional `checkpoints/*.json`, optional `handoff.md` |
| `review-execute` | Runs final independent verification against the approved plan through an isolated reviewer path. | `review.md`, optional `compound.md` |

### `review-execute` Isolation Model

`review-execute` is more than a final checklist. The orchestrator performs session discovery and pre-flight checks, then dispatches an isolated reviewer agent. That reviewer works from `plan.md`, `plan-review.md`, `state.json`, and the codebase, without reading execution logs or worker output.

## Hooks

Dev Kit ships two read-only hooks:

- `SessionStart`
- `UserPromptSubmit`

What they do:

- resolve the workspace root
- discover the preferred session through `.dev-kit/current.json`, then fall back to scanning `.dev-kit/sessions/*/state.json`
- surface passive context about the active or resumable session

What they do not do:

- start `clarify`, `planning`, `execute`, or `review-execute`
- change session state
- pick a new phase automatically

`SessionStart` adds passive `additionalContext`. Depending on available artifacts, that context can include:

- session summary
- recent progress
- handoff resume point
- compound learnings summary

`UserPromptSubmit` prints a compact summary line for the active session, for example:

```text
Dev Kit: 2026-04-06T16-30-auth-refactor | phase=planning | status=in_progress | next=Run planning. Read .dev-kit/sessions/2026-04-06T16-30-auth-refactor/brief.md. | profile=medium | plan=not_started/v0 | compound=none
```

Seeing that line means the hook found session state. It does not mean a phase started automatically.

## How Resume Works

Session recovery is shared by the phase skills and hooks.

- Preferred pointer: `.dev-kit/current.json`
- Fallback search: `.dev-kit/sessions/*/state.json`
- Resumable statuses: `in_progress`, `paused`
- Non-resumable status: `completed`

If multiple resumable sessions exist and no valid `current.json` resolves the ambiguity, Dev Kit returns a warning and requires an explicit pointer instead of guessing.

## Session Files

All session state lives under `.dev-kit/` at the workspace root.

| Path | Purpose |
|---|---|
| `.dev-kit/current.json` | Preferred pointer to the active or resumable session |
| `.dev-kit/sessions/<session-id>/state.json` | Canonical machine-readable session state |
| `.dev-kit/sessions/<session-id>/brief.md` | Clarified scope, constraints, success criteria, and complexity |
| `.dev-kit/sessions/<session-id>/plan.md` | Canonical approved execution plan |
| `.dev-kit/sessions/<session-id>/plan-review.md` | Aggregated planning verdict from critic and readiness checking |
| `.dev-kit/sessions/<session-id>/review.md` | Final verification result from `review-execute` |
| `.dev-kit/sessions/<session-id>/progress.md` | Append-only execution progress log written by the orchestrator |
| `.dev-kit/sessions/<session-id>/handoff.md` | Resume snapshot used when context reset mode is enabled |
| `.dev-kit/sessions/<session-id>/checkpoints/*.json` | Phase checkpoints for phased execution |
| `.dev-kit/sessions/<session-id>/compound.md` | Session-local learning extracted from the work |
| `.dev-kit/learnings/index.json` | Global learning index |
| `.dev-kit/learnings/<id>.md` | Reusable learning entries referenced by future sessions |

## State Helper CLI

`scripts/dev_kit_state.py` is the shared contract used by hooks and phase skills.

Common commands:

- `summary`: print the preferred resumable session summary
- `resolve-workspace-root`: resolve the canonical workspace root for the current invocation
- `write-json`: safely update `.dev-kit` JSON files
- `learnings-summary`: print a compact summary of relevant compound learnings
- `bump-learning`: update reference counters for a learning that was actually used
- `clear-current`: remove `current.json` only if it still points to the target session

## Workspace Root Resolution

Dev Kit resolves the canonical workspace root in this order:

1. `DEV_KIT_STATE_ROOT`
2. the nearest existing `.dev-kit` root
3. git top-level
4. current working directory

All paths stored in JSON must stay relative to that root.

## Supporting Skills

### Workflow Support

| Skill | Purpose |
|---|---|
| `compound` | Extract, refresh, and list reusable learnings in `.dev-kit/learnings/`. Extraction can be done from completed or in-progress work when the user wants to preserve a reusable insight. |

### Debugging

| Skill | Purpose |
|---|---|
| `systematic-debugging` | Seven-step debugging workflow: Define -> Reproduce -> Evidence -> Isolate -> Lock -> Fix -> Verify |

### Code Quality

| Skill | Purpose |
|---|---|
| `karpathy` | Read-before-write implementation discipline |
| `rob-pike` | Measurement-driven performance discipline |
| `clean-ai-slop` | Remove common AI-generated code smells |
| `simplify-code` | Review changed code for reuse, quality, and efficiency issues |

## Contributor Reference

Core implementation and reference files:

- [skills/clarify/SKILL.md](./skills/clarify/SKILL.md)
- [skills/planning/SKILL.md](./skills/planning/SKILL.md)
- [skills/execute/SKILL.md](./skills/execute/SKILL.md)
- [skills/review-execute/SKILL.md](./skills/review-execute/SKILL.md)
- [skills/compound/SKILL.md](./skills/compound/SKILL.md)
- [scripts/dev_kit_state.py](./scripts/dev_kit_state.py)
- [hooks/hooks.json](./hooks/hooks.json)
- [schema/state.schema.json](./schema/state.schema.json)
- [schema/learnings-index.schema.json](./schema/learnings-index.schema.json)
- [tests/test_dev_kit_state.py](./tests/test_dev_kit_state.py)

## Project Structure

```text
dev-kit/
├── .claude-plugin/
├── .codex-plugin/
├── .mcp.json
├── .app.json
├── assets/
├── hooks/
├── schema/
├── scripts/
├── skills/
├── tests/
├── README.md
└── README.ko.md
```

## License

MIT
