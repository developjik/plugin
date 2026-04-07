---
name: planning
description: Mandatory pre-execute phase for Dev Kit. Runs after clarify, writes either a minimal or full approved `plan.md`, uses a `planner -> critic + readiness-checker` internal review bundle, proves execute readiness, and updates `.dev-kit/` state for execution.
---

# Plan Crafting

Writes a decision-complete `plan.md` from a clear work scope. Planning is the mandatory phase immediately before execute. It is the single decomposition engine for both simple and complex work, and it owns both plan quality and execute readiness before execute begins.

## Core Principle

The plan must remove implementer decisions. Even trivial work needs a minimal approved plan before execute begins. If the work needs task split, phase split, checkpoints, worktree isolation, or execution-readiness checks, planning must decide and verify all of that up front. Internally, planning uses a `planner`, `critic`, and `readiness-checker` bundle while remaining one visible phase. Execute and review consume the approved plan; they do not perform a second planning pass.

## Hard Gates

1. **Every step must be executable.** No placeholders, TODOs, or "figure it out later."
2. **Task conflicts must be explicit.** Tasks touching the same file or shared state must not be marked parallel.
3. **High-profile plans must decide execution structure.** Phase graph, checkpoints, integration gates, and worktree eligibility cannot be deferred to execute.
4. **Independent critique is mandatory.** A plan is not complete until a `critic` pass has tried to break it and the result is saved.
5. **Execute readiness must be proven independently.** A separate `readiness-checker` must verify verification commands, required dependencies, credentials, and worktree assumptions before approval.
6. **Only the orchestrator writes planning state.** `planner`, `critic`, and `readiness-checker` must not edit `.dev-kit/current.json`, `state.json`, `plan.md`, or `plan-review.md` directly.
7. **Only approved plans may advance.** `execute` begins only after planning freezes an approved plan.

## When To Use

- After `clarify` saves `brief.md`
- When resuming the mandatory pre-execute planning phase
- When the user provides a clear implementation scope and the task still needs to be materialized into an approved plan
- When ordering, verification, or split strategy matters
- When a user explicitly wants to replace an existing draft or approved plan before execution continues

## When NOT To Use

- Scope is still ambiguous
- The active session is already inside `execute` or `review-execute` and the user is not intentionally replacing the plan

## Input

This skill operates within:

```text
.dev-kit/sessions/<session-id>/
```

Session discovery order:

1. If the user provides a session path, use it
2. Otherwise, read `.dev-kit/current.json`
3. If the pointer is missing, invalid, or not resumable, use the shared session-recovery helper to scan `.dev-kit/sessions/*/state.json` for sessions with `status` in `in_progress` or `paused`
4. If no resumable session exists and the request is already concrete, materialize the clarify artifacts first by creating a session plus a concise `brief.md`, then continue with planning. Otherwise, return to `clarify`

Read:

- `.dev-kit/sessions/<session-id>/state.json`
- `.dev-kit/sessions/<session-id>/brief.md`
- any existing checkpoint JSON if the user explicitly wants to replace a prior plan after partial progress
- any existing `plan-review.md` if the current planning pass is revising an earlier draft

Canonical output paths:

```text
.dev-kit/sessions/<session-id>/plan.md
.dev-kit/sessions/<session-id>/plan-review.md
```

## Planning Workflow

Planning remains one visible phase, but internally it runs four sub-steps:

`draft -> parallel review -> revise -> freeze`

`parallel review` means the `critic` and `readiness-checker` both evaluate the same draft `plan.md` version independently before the orchestrator aggregates the result.

### Step 0: Load Session Context

Extract:

- Goal
- Scope boundaries
- Technical context
- Constraints
- Success criteria
- `execution_profile` from `state.json`
- current `plan_version` and `plan_status`

If planning was entered directly from a clear prompt with no existing session:

- create `.dev-kit/sessions/<session-id>/`
- write a concise `brief.md` covering goal, scope, constraints, and success criteria
- initialize `state.json` exactly as clarify would
- treat that brief as a materialized direct-clarify result, then continue with planning rather than bypassing clarify

If this is the first plan for the session:

- set `plan_version` to `1`

If the user explicitly restarts planning after a prior draft or approved plan:

- increment `plan_version`
- treat the new work as a fresh planning pass that supersedes the prior plan

Set `plan_status` to `drafting` before writing the new draft. Keep the same `plan_version` throughout internal revise loops; only increment `plan_version` when the user explicitly starts a new planning pass.

### Step 1: Discover Verification

Before decomposing work, discover the highest-value verification strategy:

1. Existing e2e
2. Integration tests
3. Project verification skill or agent
4. Broad project test suite
5. Build + lint

#### Tool Detection Guidance

For each verification level, inspect these signals to determine availability:

**Level 1 — E2E:**

- config files: `playwright.config.{ts,js}`, `cypress.config.{ts,js,mjs}`, `wdio.conf.{ts,js}`
- package scripts containing `e2e`, `playwright`, `cypress`
- Python: `pyproject.toml` or `setup.cfg` entries for `pytest-playwright`, `selenium`
- dev server availability: package.json `dev`/`start`/`serve` scripts, `docker-compose` with app service
- a working dev server is a prerequisite for browser-based e2e

**Level 2 — Integration tests:**

- directories: `tests/integration`, `__tests__/integration`, `test/integration`
- package scripts containing `test:integration`
- API test artifacts: `*.postman_collection.json`, `*.http`, `*.rest`, curl test scripts
- Python: pytest markers for integration, conftest fixtures with database/network setup

**Level 3 — Project verification skill or agent:**

- `.claude/` or `.dev-kit/` verification skill references
- Makefile or Taskfile targets named `verify`, `check`, `validate`

**Level 4 — Broad test suite:**

- package `test` scripts, `pytest.ini`, `jest.config.*`, `vitest.config.*`
- Go: `*_test.go` files, Rust: `#[cfg(test)]` modules, Java: `src/test/`

**Level 5 — Build + lint:**

- package `build`/`lint` scripts, `tsc --noEmit`, eslint/prettier config
- Go: `go build ./...`, Rust: `cargo check`, Python: mypy/ruff config

Map the highest available level to the plan's Verification Strategy. When multiple levels exist, record the highest as primary and the next as fallback.

If only level 5 exists, add a task that creates minimal verification infrastructure before implementation tasks.

### Step 2: Discover Execution Constraints

Map the implementation surface before writing tasks:

- candidate files to create or modify
- shared state boundaries such as schemas, contracts, core config, shared types
- interfaces that downstream tasks depend on
- likely independent work streams
- environment, credentials, and dependencies required for execute to start cleanly
- worktree and parallel assumptions that must already hold before execute

This mapping is the basis for all split and worktree decisions.

### Step 3: Draft The Plan

The `planner` produces the canonical draft `plan.md`. The planner sees:

- `brief.md`
- `state.json`
- repo exploration findings
- any previous aggregated findings from `plan-review.md` for the same planning pass

Use the execution profile from clarify, then confirm or override it based on the actual file and dependency map.

For low-profile or trivial work, the plan may stay compact, but it still must become an explicit approved plan before execute. Minimal plans still need scope, verification, execution mode, and readiness decisions recorded.

Required decisions:

- `Split Mode`: `single-phase | multi-phase`
- `Isolation Mode`: `inline | parallel-subagents | conditional-worktrees`
- `Checkpoint Mode`: `final-only | per-phase`
- `Context Reset`: `disabled | enabled` — whether execute prepares handoff artifacts for clean resumption after context compression (medium/high-profile concern only)
- `Why this mode fits the task`
- exact verification commands
- exact readiness checks planning must prove before approval

Decision rules:

- **Low profile**
  - default to `single-phase`
  - a minimal approved plan is acceptable when the task is trivial and bounded; use the Low-Profile Minimal Plan template below
  - use `inline` or small parallel groups only when clearly safe
  - checkpoints may remain `final-only`
  - context reset stays `disabled` (single-session expected)
- **Medium profile**
  - task split is expected when dependency depth is non-trivial
  - use `parallel-subagents` for disjoint groups
  - use `final-only` checkpoints unless integration risk is notable
  - set context reset to `enabled` when estimated execution exceeds 2 phases or the task count exceeds 8
- **High profile**
  - planning must explicitly evaluate `single-phase` versus `multi-phase`
  - planning must produce `Parallel Groups`, `Worktree Decision`, `Checkpoint Plan`, and `Integration Gates`
  - worktrees are optional, never automatic
  - default context reset to `enabled` unless the work fits comfortably in a single context window

### Step 4: Parallel Independent Review

After the draft is written:

- set `plan_status` to `in_review`
- run `critic` and `readiness-checker` against the same draft `plan.md`
- do not let the `critic` see the planner's internal reasoning or the readiness result
- do not let the `readiness-checker` see the critic result before its first verdict
- have the `critic` check feasibility, dependency ordering, integration risk, verification coverage, and parallel/write-set safety
- have the `readiness-checker` confirm that chosen verification commands can run and that required env vars, credentials, services, dependencies, and worktree assumptions hold
- have the `readiness-checker` verify that tool detection results from Step 1 still hold: config files exist, detected tools are installed, and any dev server referenced in the verification strategy can start
- aggregate the two verdicts in `plan-review.md`

The aggregated review output must say either:

- `PASS` — both `critic` and `readiness-checker` passed, so the plan can be frozen for execute
- `FAIL` — at least one reviewer failed, so the plan must be revised before execute

Do not persist partial reviewer output. If planning is interrupted during `in_review`, rerun both reviewers against the canonical draft when the session resumes.

### Step 5: Revise The Draft

If the aggregated review fails:

- set `plan_status` to `revising`
- normalize the `critic` and `readiness-checker` findings into one revision checklist
- update `plan.md` to address every blocking finding
- rerun both reviewers against the revised draft
- repeat until both reviewers pass, up to 3 review cycles for the same planning pass

If 3 consecutive review cycles still fail, stop and escalate the planning blockage to the user. Planning does not hand a non-passing review bundle to execute.

### Step 6: Freeze And Approve

Once the aggregated review passes:

- freeze the approved `plan.md`
- keep `plan-review.md` as the human-readable aggregated approval record for the planning pass
- set `plan_status` to `approved`
- set `current_phase` to `execute`
- keep `status` as `in_progress`
- set `next_action` to `Run execute. Read .dev-kit/sessions/<session-id>/plan.md.`

## Canonical Plan Structure

Write `plan.md` with this structure:

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]
**Execution Profile:** [low | medium | high]
**Plan Version:** [integer]

**Work Scope:**
- **In scope:** [Included work]
- **Out of scope:** [Excluded work]

**Verification Strategy:**
- **Level:** [e2e | integration | skill/agent | test-suite | build-only]
- **Command:** [exact command]
- **What it validates:** [what passing proves]
- **Detected Tools:** [tool names and config paths found during discovery, or "none detected — manual command"]

## File Structure Mapping

- `path/to/file` — [responsibility]

## Execution Strategy

- **Split Mode:** [single-phase | multi-phase]
- **Isolation Mode:** [inline | parallel-subagents | conditional-worktrees]
- **Checkpoint Mode:** [final-only | per-phase]
- **Context Reset:** [disabled | enabled]
- **Rationale:** [why]

## Phase Graph

- **P1:** [goal]
- **P2:** [goal]

## Parallel Groups

- **Group A:** [tasks that can run together]
- **Group B:** [tasks that can run together]

## Write-Set Overlap Check

| Task or Group | Files Touched | Overlap Risk | Parallel Safe |
|---|---|---|---|
| Task 1 | `...` | Low | Yes |

## Worktree Decision

- **Eligible groups:** [list or none]
- **Not eligible:** [list or none]
- **Reasoning:** [disjoint write sets, shared state, validation independence]

## Checkpoint Plan

- [When checkpoints are written]
- [What each checkpoint records]

## Integration Gates

- [Commands and boundary checks to run between phases]

## Tasks

### Task 1: [Name]

**Phase:** [P1]
**Task Goal:** [behavior this task makes true]
**Acceptance Criteria:**
- [ ] [criterion]
- [ ] [criterion]
**Dependencies:** [None or predecessor tasks]
**Files:**
- Create: `path`
- Modify: `path`
- Test: `path`

**Steps:**
1. [Concrete action]
2. [Concrete action]
3. [Verification action]
```

### Low-Profile Minimal Plan

When `execution_profile` is `low`, the plan MAY use this reduced template. Sections not listed here are omitted — they apply only to medium and high profiles.

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence]
**Execution Profile:** low
**Plan Version:** [integer]

**Work Scope:**
- **In scope:** [Included work]
- **Out of scope:** [Excluded work]

**Verification Strategy:**
- **Level:** [level]
- **Command:** [exact command]
- **What it validates:** [what passing proves]

## File Structure Mapping

- `path/to/file` — [responsibility]

## Execution Strategy

- **Split Mode:** single-phase
- **Isolation Mode:** inline
- **Checkpoint Mode:** final-only
- **Context Reset:** disabled
- **Rationale:** [why]

## Tasks

### Task 1: [Name]

**Task Goal:** [behavior this task makes true]
**Acceptance Criteria:**
- [ ] [criterion]
**Files:**
- Create/Modify: `path`

**Steps:**
1. [Concrete action]
2. [Verification action]
```

Omitted for low-profile: Architecture, Tech Stack, Phase Graph, Parallel Groups, Write-Set Overlap Check, Worktree Decision, Checkpoint Plan, Integration Gates, Context Reset. These are required for medium and high profiles.

## Worktree Policy

Mark a group `worktree-eligible` only if all are true:

- write sets are disjoint
- no shared schema, contract, or core config mutation
- each group can be validated without the other group's unfinished work
- merge order is obvious

Worktree use is forbidden when:

- tasks edit the same core file
- tasks reshape shared types, shared contracts, or schema together
- one group's output determines another group's design

When worktrees are used, keep `.dev-kit/` anchored to the canonical workspace root. If needed, export `DEV_KIT_STATE_ROOT` so worktree agents read the same state store instead of creating local copies.

## Plan Review Artifact

Write `plan-review.md` as an aggregated approval record, not as raw reviewer transcripts:

```markdown
# [Feature Name] Plan Review

**Plan Version:** [integer]
**Review Round:** [integer]
**Verdict:** PASS / FAIL

## 1. Critic Verdict

- **Verdict:** PASS / FAIL
- [dependency ordering]
- [verification coverage]
- [integration gates]
- [parallel/write-set safety]

## 2. Execute Readiness

- **Verdict:** PASS / FAIL
- [verification command runs successfully]
- [required env vars and credentials are present]
- [required services and dependencies are available]
- [parallel/worktree assumptions hold in the current repo]

## 3. Consolidated Findings

- [issue]

## 4. Decision

[Why the plan is frozen or why it must be revised]
```

Keep `plan-review.md` concise. Preserve the latest blocking findings and final approval basis, but do not store raw reviewer scratch notes or partial single-reviewer output.

## State Update

After the final aggregated review passes and the plan is frozen, update `.dev-kit/sessions/<session-id>/state.json`:

- set `current_phase` to `execute`
- keep `status` as `in_progress`
- set `plan_status` to `approved`
- keep `plan_version` at the approved version
- set `next_action` to `Run execute. Read .dev-kit/sessions/<session-id>/plan.md.`
- set `artifacts.plan` to `.dev-kit/sessions/<session-id>/plan.md`
- set `artifacts.plan_review` to `.dev-kit/sessions/<session-id>/plan-review.md`
- replace `phase_status` with each planned phase marked `pending` when the plan is phased
- update `updated_at`

Also refresh `.dev-kit/current.json` with the same `session_id`, `session_path`, and a new `updated_at`.

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Treating planning as optional for trivial work | Execute still needs an approved plan, even if it is minimal |
| Leaving phase or checkpoint decisions to execute | Execution should not redesign the plan |
| Marking shared-file tasks as parallel | Causes conflicts and invalid merge assumptions |
| Marking a group worktree-eligible without overlap analysis | Produces brittle merges and hidden integration failures |
| Advancing to execute before both reviewers pass | Pushes planning defects into later phases |
| Approving a plan before readiness checks pass | Forces execute to become a second planning stage |
| Persisting partial reviewer output | Makes review recovery ambiguous and couples resumability to half-finished reviewer state |
| Letting reviewers write `.dev-kit` files directly | Breaks single-writer state and makes planning recovery unreliable |

## Minimal Checklist

- [ ] Does the plan use `.dev-kit/sessions/<session-id>/plan.md`?
- [ ] Was `plan-review.md` written?
- [ ] Did both `critic` and `readiness-checker` pass?
- [ ] Were execute-readiness checks completed?
- [ ] Is the execution strategy explicit?
- [ ] Are phase graph and integration gates present when needed?
- [ ] Is worktree eligibility justified or explicitly rejected?
- [ ] Does the final task verify the entire plan?

## Transition

After plan approval:

- proceed to `execute`
- if ambiguity is discovered before approval, stay in `planning` and revise

Planning is always the phase immediately before execute. This skill does not execute the work. It owns plan quality and execute readiness, freezes the approved plan, and prepares the active session for `execute`.
