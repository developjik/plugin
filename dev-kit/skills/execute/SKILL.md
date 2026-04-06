---
name: execute
description: Unified execution orchestrator for Dev Kit. Reads the approved canonical `plan.md`, executes either a single-phase or phased plan, enforces task validation, and manages checkpoint JSON plus resume-safe `.dev-kit/` state updates.
---

# Run Plan

Loads an approved `plan.md` and executes it using worker-validator loops. `execute` owns both the simple and high-complexity execution paths, but it is a pure execution stage rather than a second planning pass.

## Core Principle

Execute follows the approved plan faithfully. Planning already closed plan quality and execute readiness, so execute should focus on implementation, validation, and integration only. If reality still contradicts the approved plan, treat that as a planning contract violation rather than inventing a new workflow state.

## Hard Gates

1. **Read the full approved plan first.** Never start executing from a partial excerpt.
2. **Only the orchestrator writes session state.** Workers, validators, and worktree agents must not edit `.dev-kit/current.json` or `state.json`.
3. **Task validation stays isolated.** Validators receive only plan-derived task requirements, never worker output.
4. **Phase completion requires integration checks.** In phased runs, a phase is not complete until its integration gate passes and its checkpoint JSON is written.
5. **Worktree execution is conditional.** Use worktrees only for groups explicitly marked worktree-eligible in the approved plan.
6. **Execute does not redesign the plan.** If the approved plan proves structurally wrong, stop and report a planning contract violation.
7. **Normal workflow state stays simple.** Execute keeps the session `in_progress` until work is ready for review.

## When To Use

- After `planning` freezes an approved canonical `plan.md`
- When the user wants the plan carried out
- When a session is ready to resume execution

## When NOT To Use

- No canonical `plan.md` exists
- `plan_status` is not `approved`
- Work scope is still ambiguous
- The user only asked for a plan

## Input

Canonical input:

```text
.dev-kit/sessions/<session-id>/plan.md
```

Session discovery order:

1. If the user provides a session path, use it
2. Otherwise, read `.dev-kit/current.json`
3. If the pointer is missing, invalid, or not resumable, use the shared session-recovery helper to scan `.dev-kit/sessions/*/state.json`
4. If no resumable session exists, stop and tell the user to run `planning` or provide an explicit session path

Read:

- `.dev-kit/sessions/<session-id>/state.json`
- `.dev-kit/sessions/<session-id>/plan.md`
- any existing checkpoint JSON files

## Step 0: Load The Approved Plan

Before execution begins:

1. Read the entire `plan.md`
2. Confirm `state.json.plan_status` is `approved`
3. Derive the execution graph directly from the approved plan

If the approved plan contract is missing or structurally incoherent at this point, stop and report a planning contract violation rather than mutating workflow state.

## Step 1: Build The Execution Graph

Read these sections from the approved plan:

- `Execution Strategy`
- `Phase Graph`
- `Parallel Groups`
- `Write-Set Overlap Check`
- `Worktree Decision`
- `Checkpoint Plan`
- `Integration Gates`

From them, derive:

- ordered phase list
- ready-task groups for each phase
- which groups run sequentially
- which groups run in parallel
- which parallel groups are worktree-eligible

If the plan says `Split Mode: single-phase`, treat the full plan as phase `P1`.

After the graph is loaded, update `state.json`:

- set `current_phase` to `execute`
- keep `status` as `in_progress`
- keep `plan_status` as `approved`
- update `updated_at`

Refresh `.dev-kit/current.json` with the same session pointer and new `updated_at`.

## Step 2: Task Execution Cycle

Every task goes through:

1. compliance check
2. worker implementation
3. validator review

### 2-1. Compliance Check

Before launching a task:

- confirm dependencies are complete
- confirm no overlapping file group is already in progress
- confirm required predecessor artifacts exist

If any of these fail because the approved plan itself no longer makes sense, stop and report a planning contract violation.

### 2-2. Worker Implementation

Dispatch a worker subagent to execute the task exactly as written.

Worker rules:

- follow the task steps
- run the task's stated verification commands
- stay within the task's file scope unless the plan explicitly allows broader changes
- report only completion status, blockers, and verification results
- treat `.dev-kit/**` as orchestrator-owned metadata

### 2-3. Validator Review

Dispatch a separate validator subagent with only:

- task goal
- task acceptance criteria
- files to inspect
- task-level verification commands

Validator rules:

- inspect code directly from disk
- run task verification independently
- report `PASS` or `FAIL`
- on `FAIL`, describe the unmet criteria with file paths and line numbers
- do not edit `.dev-kit/**`

Retry rule:

- the same task may be retried at most 3 times
- after 3 failures, stop and escalate

## Step 3: Single-Phase Execution

If the plan is single-phase:

1. run tasks in dependency order
2. run parallel groups concurrently when marked safe
3. use worktrees only if the approved plan explicitly marks a group worktree-eligible
4. after all tasks pass validation, run the plan's highest-level verification command
5. run the full test suite for regressions

If all succeed:

- set `current_phase` to `review`
- keep `status` as `in_progress`
- keep `plan_status` as `approved`
- set `next_action` to `Run review. Read .dev-kit/sessions/<session-id>/plan.md.`
- update `updated_at`

Refresh `.dev-kit/current.json` with the new `updated_at`.

## Step 4: Phased Execution

If the plan is multi-phase, execute a phase loop:

`phase -> ready groups -> task validation -> integration gate -> checkpoint`

### 4-1. Start Phase

At phase start:

- mark that phase as `executing` in `state.json.phase_status`
- update `updated_at`

### 4-2. Run Ready Groups

For each ready group in the phase:

- run sequentially if not marked parallel-safe
- run concurrently if parallel-safe
- run in worktrees only when the approved plan explicitly marked the group `worktree-eligible`

### 4-3. Worktree Orchestration

When using worktrees:

- create one worktree per eligible group
- set `DEV_KIT_STATE_ROOT` so each worktree points back to the canonical workspace state store
- the group worker owns only its assigned files
- validator runs inside the same worktree context
- after all eligible groups pass validation, merge back in the merge order specified by the plan
- after each merge, run at least the relevant integration checks

If merge conflict or post-merge integration failure occurs:

- stop the phase
- do not write a checkpoint
- if the issue is an implementation defect within the approved plan, re-run the affected groups
- if the issue proves the approved plan structurally wrong, stop and report a planning contract violation

### 4-4. Integration Gate

After all groups in the phase pass task validation:

- run the phase's integration gate commands from `Integration Gates`
- verify boundary assumptions called out in the approved plan:
  - interface compatibility
  - shared type alignment
  - config/schema compatibility
  - end-to-end boundary behavior for the completed phases

If the integration gate fails:

- if the failure is an implementation defect within the approved plan, re-run the affected tasks
- if the failure proves the approved plan structurally wrong, stop and report a planning contract violation

### 4-5. Write Checkpoint

Only after the integration gate passes, write:

```text
.dev-kit/sessions/<session-id>/checkpoints/P<N>-<name>.json
```

Checkpoint format:

```json
{
  "schema_version": 1,
  "phase": "P1",
  "name": "foundation",
  "status": "passed",
  "created_at": "YYYY-MM-DDTHH:MM:SS+TZ",
  "verified_scope": ["..."],
  "validation": ["..."],
  "integration_gate": {
    "command": "...",
    "result": "PASS"
  },
  "files_changed": ["path/to/file"],
  "interfaces_established": ["..."],
  "resume_notes": ["..."]
}
```

Then update `state.json`:

- mark that phase as `completed` in `phase_status`
- update `updated_at`

### 4-6. Complete Execute

After the final phase checkpoint:

- run the highest-level verification command again on the integrated system
- run the full test suite
- set `current_phase` to `review`
- keep `status` as `in_progress`
- keep `plan_status` as `approved`
- set `next_action` to `Run review. Read .dev-kit/sessions/<session-id>/plan.md.`
- update `updated_at`

Refresh `.dev-kit/current.json` with the new `updated_at`.

## Recovery

On re-entry after interruption:

1. resolve the preferred session from the shared recovery helper
2. read `state.json`
3. inspect `phase_status`
4. inspect existing checkpoint JSON
5. find the last fully checkpointed phase

Resume rules:

- if no checkpoint exists, restart the current phase from the beginning
- if a phase checkpoint exists, do not re-run that phase unless the user explicitly requests rollback
- if merge or integration stopped before checkpoint but the plan still stands, re-enter that phase in `executing` state

## Failure Response

Escalate to the user when:

- a task fails validation 3 times
- a worktree merge assumption is invalid
- phase integration fails twice for different attempted fixes
- the approved plan contract is missing critical information
- the environment cannot run required verification

When escalating, report whether the next action should be:

- return to `execute` after a targeted fix
- use `systematic-debugging` for deeper failure analysis
- return to `planning` because the approved plan violated its own planning contract

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Letting workers update `.dev-kit/` state | Creates race conditions and resume corruption |
| Treating task validation as phase completion | Misses integration failures between groups |
| Writing checkpoints before integration passes | Makes resume trust an invalid state |
| Using worktrees without plan approval | Hidden overlap and merge errors |
| Silently reopening planning inside execute | Breaks the frozen-plan contract |
| Skipping final review because execute already validated tasks | Removes the independent final verification step |

## Minimal Checklist

- [ ] Was the full approved plan read before execution?
- [ ] Did `plan_status` already equal `approved` before execute began?
- [ ] Did only the orchestrator update `.dev-kit/current.json` and `state.json`?
- [ ] Did every task pass isolated validation?
- [ ] Did each phase pass its integration gate before checkpointing?
- [ ] Does `next_action` point to `review` when execute completes?

## Transition

After execute finishes:

- proceed to `review`
- if repeated failures point to an unclear bug, use `systematic-debugging`
- if the approved plan proves structurally wrong, stop and report a planning contract violation
