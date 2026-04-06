---
name: planning
description: Use after clarify or when a scope is already clear. Writes the canonical `plan.md`, runs an independent critique, proves execute readiness, freezes an approved plan, and updates `.dev-kit/` state for execution.
---

# Plan Crafting

Writes a decision-complete `plan.md` from a clear work scope. Planning is the single decomposition engine for both simple and complex work, and it owns both plan quality and execute readiness before execute begins.

## Core Principle

The plan must remove implementer decisions. If the work needs task split, phase split, checkpoints, worktree isolation, or execution-readiness checks, planning must decide and verify all of that up front. Execute and review consume the approved plan; they do not perform a second planning pass.

## Hard Gates

1. **Every step must be executable.** No placeholders, TODOs, or "figure it out later."
2. **Task conflicts must be explicit.** Tasks touching the same file or shared state must not be marked parallel.
3. **High-profile plans must decide execution structure.** Phase graph, checkpoints, integration gates, and worktree eligibility cannot be deferred to execute.
4. **Independent critique is mandatory.** A plan is not complete until a critique pass has tried to break it and the result is saved.
5. **Execute readiness must be proven before approval.** Verification commands, required dependencies, credentials, and worktree assumptions must be checked in planning.
6. **Only approved plans may advance.** `execute` begins only after planning freezes an approved plan.

## When To Use

- After `clarify` saves `brief.md`
- When the user provides a clear implementation scope and wants a real plan
- When ordering, verification, or split strategy matters
- When a user explicitly wants to replace an existing draft or approved plan before execution continues

## When NOT To Use

- Scope is still ambiguous
- The task is a single obvious edit that does not benefit from a formal plan
- The user explicitly says to skip planning

## Input

This skill operates within:

```text
.dev-kit/sessions/<session-id>/
```

Session discovery order:

1. If the user provides a session path, use it
2. Otherwise, read `.dev-kit/current.json`
3. If the pointer is missing, invalid, or not resumable, use the shared session-recovery helper to scan `.dev-kit/sessions/*/state.json`
4. If no resumable session exists and the request is already concrete, initialize a new session plus `brief.md` before writing the plan. Otherwise, return to `clarify`

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

Planning remains one visible phase, but internally it runs four serialized sub-steps:

`draft -> critique -> revise -> freeze`

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
- initialize `state.json` exactly as clarify would, then continue with planning

If this is the first plan for the session:

- set `plan_version` to `1`

If the user explicitly restarts planning after a prior draft or approved plan:

- increment `plan_version`
- treat the new work as a fresh planning pass that supersedes the prior plan

Set `plan_status` to `drafting` before writing the new draft.

### Step 1: Discover Verification

Before decomposing work, discover the highest-value verification strategy:

1. Existing e2e
2. Integration tests
3. Project verification skill or agent
4. Broad project test suite
5. Build + lint

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

Use the execution profile from clarify, then confirm or override it based on the actual file and dependency map.

Required decisions:

- `Split Mode`: `single-phase | multi-phase`
- `Isolation Mode`: `inline | parallel-subagents | conditional-worktrees`
- `Checkpoint Mode`: `final-only | per-phase`
- `Why this mode fits the task`
- exact verification commands
- exact readiness checks planning must prove before approval

Decision rules:

- **Low profile**
  - default to `single-phase`
  - use `inline` or small parallel groups only when clearly safe
  - checkpoints may remain `final-only`
- **Medium profile**
  - task split is expected when dependency depth is non-trivial
  - use `parallel-subagents` for disjoint groups
  - use `final-only` checkpoints unless integration risk is notable
- **High profile**
  - planning must explicitly evaluate `single-phase` versus `multi-phase`
  - planning must produce `Parallel Groups`, `Worktree Decision`, `Checkpoint Plan`, and `Integration Gates`
  - worktrees are optional, never automatic

### Step 4: Independent Critique

After the draft is written:

- set `plan_status` to `in_review`
- critique the draft as if execute and review will never repair plan quality later
- check feasibility, dependency ordering, integration risk, verification coverage, worktree assumptions, and execute-readiness coverage
- confirm that the chosen verification commands actually run
- confirm that required env vars, credentials, services, and dependencies are present
- record the critique outcome in `plan-review.md`

The critique output must say either:

- `PASS` — the plan can be frozen for execute
- `FAIL` — the plan must be revised before execute

### Step 5: Revise The Draft

If critique fails:

- set `plan_status` to `revising`
- update `plan.md` to address every critique finding
- rerun the critique
- repeat until the critique passes

Planning does not hand a non-passing critique to execute.

### Step 6: Freeze And Approve

Once critique passes:

- freeze the approved `plan.md`
- keep `plan-review.md` as the human-readable record of the final critique pass
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

## File Structure Mapping

- `path/to/file` — [responsibility]

## Execution Strategy

- **Split Mode:** [single-phase | multi-phase]
- **Isolation Mode:** [inline | parallel-subagents | conditional-worktrees]
- **Checkpoint Mode:** [final-only | per-phase]
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

Write `plan-review.md` with this structure:

```markdown
# [Feature Name] Plan Review

**Plan Version:** [integer]
**Verdict:** PASS / FAIL

## 1. Structural Checks

- [dependency ordering]
- [verification coverage]
- [integration gates]
- [worktree eligibility]

## 2. Execute Readiness

- [verification command runs successfully]
- [required env vars and credentials are present]
- [required services and dependencies are available]
- [parallel/worktree assumptions hold in the current repo]

## 3. Findings

- [issue]

## 4. Decision

[Why the plan is frozen or why it must be revised]
```

## State Update

After the final critique passes and the plan is frozen, update `.dev-kit/sessions/<session-id>/state.json`:

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
| Leaving phase or checkpoint decisions to execute | Execution should not redesign the plan |
| Marking shared-file tasks as parallel | Causes conflicts and invalid merge assumptions |
| Marking a group worktree-eligible without overlap analysis | Produces brittle merges and hidden integration failures |
| Advancing to execute before critique passes | Pushes planning defects into later phases |
| Approving a plan before readiness checks pass | Forces execute to become a second planning stage |

## Minimal Checklist

- [ ] Does the plan use `.dev-kit/sessions/<session-id>/plan.md`?
- [ ] Was `plan-review.md` written?
- [ ] Did the independent critique pass?
- [ ] Were execute-readiness checks completed?
- [ ] Is the execution strategy explicit?
- [ ] Are phase graph and integration gates present when needed?
- [ ] Is worktree eligibility justified or explicitly rejected?
- [ ] Does the final task verify the entire plan?

## Transition

After plan approval:

- proceed to `execute`
- if ambiguity is discovered before approval, stay in `planning` and revise

This skill does not execute the work. It owns plan quality and execute readiness, freezes the approved plan, and prepares the active session for `execute`.
