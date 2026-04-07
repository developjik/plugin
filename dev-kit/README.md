# Dev Kit

English | [한국어](./README.ko.md)

Structured development workflow plugin for Claude Code and Codex.

## Overview

Dev Kit provides a single official development flow:

`clarify -> planning -> execute -> review-execute`

Every task passes through all four phases. Complexity still matters, but it changes phase depth rather than visible routing. `clarify` may run in direct mode when the request is already concrete, and `planning` may freeze a minimal approved plan for trivial work, but neither phase is skipped. Internally, `planning` uses a `planner`, `critic`, and `readiness-checker` bundle while remaining one visible phase. `execute` then acts as a pure execution stage, and `review-execute` verifies the final result against that approved plan.

Session recovery is built into the phase skills through a shared state helper. It is no longer a separate visible skill.
Resumable sessions include `in_progress` and `paused` states; `completed` sessions are intentionally excluded from resume selection.

The plugin stores workflow state under `.dev-kit/` at the workspace root:

- `.dev-kit/current.json` identifies the preferred resumable session when one exists
- `.dev-kit/sessions/<session-id>/state.json` is the machine-readable source of truth
- `brief.md`, `plan.md`, `plan-review.md`, and `review.md` stay beside that state for humans
- `checkpoints/` stores phase checkpoint JSON files for phased runs

This is a breaking storage change. The old Markdown session layout is no longer used and old sessions are not migrated.

## Workflow

```text
clarify -> planning -> execute -> review-execute

clarify
  - is the mandatory entry phase for every new task
  - resolves ambiguity or confirms that little ambiguity remains
  - may run interactively or in direct mode depending on request clarity
  - writes brief.md
  - initializes state.json and current.json
  - leaves planning as the next visible step

planning
  - is the mandatory pre-execute phase
  - writes either a minimal or full approved plan.md
  - drafts through a planner role, then runs independent critic and readiness-checker review
  - records the aggregated approval result in plan-review.md
  - verifies execute readiness before approval
  - freezes an approved plan before execute

execute
  - reads an approved plan
  - runs worker-validator execution and checkpointing
  - advances directly to review-execute when implementation is complete

review-execute
  - final independent verification against the approved plan
  - always writes review.md
  - returns implementation drift to execute only
```

Quality and debugging skills remain standalone and user-invoked.

## Active Session Hooks

Dev Kit ships two read-only hooks:

- `SessionStart`
- `UserPromptSubmit`

Both hooks resolve the workspace root, use the shared session-recovery helper (`.dev-kit/current.json` first, then `.dev-kit/sessions/*/state.json` scan), and print a short summary:

- `session_id`
- `current_phase`
- `status`
- `next_action`
- `execution_profile`
- `plan_status`
- `plan_version`

If no resumable session can be selected, the hook prints a one-line warning instead of mutating anything.

## Skills

### Core Pipeline

| Skill | Trigger | Description |
|---|---|---|
| **clarify** | Any new task entering the Dev Kit flow, especially vague or underspecified requests | Mandatory entry phase. Produces a Context Brief, scores complexity, and initializes `.dev-kit/` session state. Already-clear work may use direct clarify instead of a longer Q&A loop. |
| **planning** | After clarify completes, or when resuming the mandatory pre-execute planning phase | Mandatory pre-execute phase. Writes either a minimal or full approved `plan.md`, runs a `planner -> critic + readiness-checker` internal review bundle, records the aggregated result in `plan-review.md`, proves execute readiness, and updates the active session state for execution. |
| **execute** | "run the plan", "execute the plan", "let's start implementing" | Unified execution orchestrator. Executes approved plans only, runs worker-validator loops, writes checkpoint JSON for phased runs, and hands completed work to review-execute. |
| **review-execute** | "review the work", "verify the implementation", "check if the plan was executed correctly" | Final independent verification of the approved plan. |

### Debugging

| Skill | Trigger | Description |
|---|---|---|
| **systematic-debugging** | Bug, test failure, unexpected behavior | 7-phase workflow: Define -> Reproduce -> Evidence -> Isolate -> Lock -> Fix -> Verify. |

### Code Quality

| Skill | Trigger | Description |
|---|---|---|
| **karpathy** | "implement...", "modify code...", or when you notice yourself about to make changes without reading the existing code first | Surgical implementation discipline: read before write, scope tightly, verify assumptions, define success criteria. |
| **rob-pike** | "optimize", "slow", "performance", "bottleneck", "speed up", "make faster", "too slow" | Measurement-driven optimization discipline. |
| **clean-ai-slop** | "clean up", "deslop", "slop", "clean AI code" | Removes common AI-generated code smells in ordered passes. Ignores `.dev-kit/**` workflow metadata. |
| **simplify-code** | "simplify", "clean up the code", "review the changes" | Parallel diff review for reuse, quality, and efficiency issues. Excludes `.dev-kit/**` workflow metadata from review scope. |

## State Model

### Workspace Root Resolution

Dev Kit resolves the canonical workspace root in this order:

1. `DEV_KIT_STATE_ROOT`
2. git top-level
3. current working directory

All state paths stored in JSON are relative to that root.

### `.dev-kit/current.json`

```json
{
  "schema_version": 1,
  "session_id": "2026-04-06T16-30-auth-refactor",
  "session_path": ".dev-kit/sessions/2026-04-06T16-30-auth-refactor",
  "updated_at": "2026-04-06T16:45:00+09:00"
}
```

### `.dev-kit/sessions/<session-id>/state.json`

Required fields:

- `schema_version`
- `session_id`
- `title`
- `feature_slug`
- `status`
- `current_phase`
- `execution_profile`
- `plan_status`
- `plan_version`
- `next_action`
- `artifacts`
- `phase_status`
- `created_at`
- `updated_at`

Optional field:

- `failure_reason`

The bundled schema lives at `schema/state.schema.json`.

### Status Semantics

- `in_progress` — the session is actively inside `clarify`, `planning`, `execute`, or `review-execute`
- `completed` — final successful state after `review-execute` passes
- `failed` — execution drift, repeated validator failure, or unrecoverable workflow failure has been recorded
- `paused` — waiting for an external dependency or user decision; resume is expected after remediation

`failure_reason` should be null unless status is `failed` or `paused`, and must be a non-empty string when those states are used.

If an approved plan still proves impossible to execute, that is treated as a planning contract violation to fix outside the normal state graph.

### Plan Status Semantics

- `not_started` — clarify is complete enough to enter planning, but no draft exists yet
- `drafting` — planning is actively shaping `plan.md`
- `in_review` — the `critic` and `readiness-checker` are evaluating the current draft plan
- `revising` — planning is updating the draft in response to critique or readiness findings
- `approved` — the plan is frozen and may advance to `execute`

### Phase Status Semantics

- `pending` — the planned phase has not started yet
- `executing` — the phase is currently running
- `completed` — the phase finished successfully

### Human-Readable Artifacts

Each session directory may contain:

- `brief.md`
- `plan.md`
- `plan-review.md` — aggregated planning approval record, not raw reviewer transcripts
- `review.md`
- `progress.md` — append-only execution progress log, not tracked in `state.json`
- `handoff.md` — consolidated resume snapshot for context reset mode, not tracked in `state.json`
- `checkpoints/*.json`

Those documents are for humans. `state.json` remains the machine-readable source of truth.

## Key Design Principles

**One Visible Flow** — every task traverses `clarify -> planning -> execute -> review-execute`; complexity changes phase depth, not user-facing routing.

**Planning Owns Plan Quality** — `planning` must draft, critique, readiness-check, revise, and freeze the plan before `execute` begins.

**Planning Closes Execute Readiness** — environment, verification, dependency, and worktree assumptions must be proven in planning, not deferred to execute.

**Planning Uses Internal Role Isolation** — `planner`, `critic`, and `readiness-checker` stay independent; only the orchestrator aggregates their results and writes `.dev-kit` state or artifacts.

**Pure Execute Stage** — `execute` consumes an approved plan and performs implementation plus verification; it does not reopen planning or invent new workflow states.

**Clarify And Planning Always Exist** — already-clear work uses direct clarify, and trivial work uses a minimal approved plan, but execute never starts without both upstream phases being materialized.

**Review-Execute Verifies Results Only** — `review-execute` compares the final codebase against the approved plan and returns implementation drift to execute when needed.

**JSON Source Of Truth** — `state.json` is canonical; Markdown artifacts are human-readable derivatives.

**Shared Session Recovery** — planning, execute, and review-execute all use the same `.dev-kit/current.json` plus session-scan helper instead of a separate `resume` skill.

**Worker-Validator Isolation** — task validators remain isolated from worker output; final review remains isolated from execution context.

**Single Writer State** — only the orchestrator updates session JSON, especially during phased or worktree-based execution.

**Checkpointed Recovery** — phased execution records checkpoint JSON after integration gates pass so interrupted work can restart cleanly without a separate recovery stage.

## Quick Start

```text
"Clarify this task, create a plan, execute it, and run review-execute on the result."
"Debug this failing test with systematic root-cause analysis."
"Review and simplify the changed code for quality issues."
```

## Project Structure

```text
dev-kit/
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
├── .mcp.json
├── .app.json
├── hooks/
│   ├── hooks.json
│   ├── session-start.sh
│   └── user-prompt-submit.sh
├── schema/
│   └── state.schema.json
├── scripts/
│   └── dev_kit_state.py
├── tests/
│   └── test_dev_kit_state.py
├── README.md
├── README.ko.md
├── assets/
│   ├── icon.png
│   └── logo.png
└── skills/
    ├── clarify/SKILL.md
    ├── planning/SKILL.md
    ├── execute/SKILL.md
    ├── review-execute/SKILL.md
    ├── systematic-debugging/
    ├── karpathy/SKILL.md
    ├── rob-pike/SKILL.md
    ├── clean-ai-slop/SKILL.md
    └── simplify-code/SKILL.md
```

## License

MIT
