---
name: execute
description: Explicitly invoked execution orchestrator for Dev Kit. Reads the approved canonical `plan.md`, executes either a single-phase or phased plan, enforces task validation, and manages checkpoint JSON plus resume-safe `.dev-kit/` state updates.
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
7. **Normal workflow state stays simple.** Execute keeps the session `in_progress` until work is ready for `review-execute`.

## When To Use

- After the user explicitly runs `planning` and it freezes an approved canonical `plan.md`
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
3. If the pointer is missing, invalid, or not resumable, use the shared session-recovery helper to scan `.dev-kit/sessions/*/state.json` for sessions with `status` in `in_progress` or `paused`
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

### 2-3a. Git Commit Guidance (SHOULD)

These are recommended practices, not hard gates. The orchestrator SHOULD commit after a task passes validation and before appending the progress log entry.

**Timing:**

- SHOULD commit after validator PASS, before the progress log append
- the progress log entry then records the commit SHA rather than "uncommitted"

**Message format:**

- `[<session-id>] Task <N>: <task-name>`
- example: `[2026-04-06T16-30-auth-refactor] Task 2: Add JWT generation`

**Scope:**

- only files within the task's declared file scope from the approved plan
- do not commit `.dev-kit/**` session metadata in task commits

**On validator FAIL:**

- do not commit
- if retrying the task, the previous attempt's changes remain in the working tree for the worker to fix or reset as appropriate

**Worktree execution:**

- workers commit within their worktree
- when merging worktrees back, commits arrive on the main branch in merge order
- after merge, the orchestrator does not create additional squash or merge commits

**Low-profile exception:**

- for low-profile tasks, a single commit at execute completion is acceptable instead of per-task commits
- use message format: `[<session-id>] Execute complete: <feature-slug>`

### 2-4. Append Progress Log

After each task completes validation (PASS or FAIL), the orchestrator appends a timestamped entry to:

```text
.dev-kit/sessions/<session-id>/progress.md
```

Progress log rules:

- `progress.md` is NOT tracked in `state.json` artifacts — it is a pure file artifact with no schema impact
- only the orchestrator writes this file (consistent with Hard Gate #2)
- create the file with a header block on the first append if it does not already exist
- in worktree-parallel execution, buffer task results and append them after the merge step, not from within worktrees

Header block (written once at creation):

```markdown
# Execution Progress Log

**Session:** <session-id>
**Plan Version:** <integer>
**Started:** <ISO timestamp>
```

Entry template (appended after each task validation):

```markdown
### Task <N>: <Name> — <PASS|FAIL> (<timestamp>)
- Phase: P<N>
- Files: <changed files>
- Duration: <elapsed>
- Commit: <short SHA or "uncommitted">
- Notes: <one-line summary or failure reason>
```

When the git commit guidance (Step 2-3a) is followed, the Commit field records the actual short SHA. When commits are deferred (e.g., low-profile single commit), record "uncommitted" until the deferred commit is made; do not retroactively update earlier entries.

#### Low-Profile Progress Entries

When `execution_profile` is `low`, progress entries MAY use a one-line format:

```markdown
- Task <N>: <Name> — <PASS|FAIL> (<timestamp>) — <short SHA or "uncommitted"> — <one-line note>
```

The header block is still required. The full multi-line entry format remains required for medium and high profiles.

## Step 3: Single-Phase Execution

Low-profile tasks are always single-phase. The phased execution path (Step 4) does not apply to low-profile work.

If the plan is single-phase:

1. run tasks in dependency order
2. run parallel groups concurrently when marked safe
3. use worktrees only if the approved plan explicitly marks a group worktree-eligible
4. when `Context Reset: enabled`, write `handoff.md` after every 4th task completion within the single phase
5. after all tasks pass validation, run the plan's highest-level verification command
6. run the full test suite for regressions

If all succeed:

- set `current_phase` to `review-execute`
- keep `status` as `in_progress`
- keep `plan_status` as `approved`
- set `next_action` to `Run review-execute. Read .dev-kit/sessions/<session-id>/plan.md.`
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
  "resume_notes": ["..."],
  "tasks_completed": [
    {
      "task_id": 1,
      "name": "...",
      "status": "passed",
      "commit_sha": "abc1234"
    }
  ],
  "next_phase": "P2",
  "next_task": {
    "task_id": 4,
    "name": "...",
    "phase": "P2"
  }
}
```

The `tasks_completed`, `next_phase`, and `next_task` fields are added when the approved plan sets `Context Reset: enabled`. When context reset is disabled, omit these fields — the checkpoint stays backward-compatible.

Then update `state.json`:

- mark that phase as `completed` in `phase_status`
- update `updated_at`

### 4-5a. Write Handoff Artifact (Context Reset Mode)

When the approved plan's Execution Strategy sets `Context Reset: enabled`, the orchestrator writes a consolidated handoff artifact after each checkpoint:

```text
.dev-kit/sessions/<session-id>/handoff.md
```

Handoff artifact rules:

- `handoff.md` is NOT tracked in `state.json` artifacts — it follows the same pattern as `progress.md`
- only the orchestrator writes this file (consistent with Hard Gate #2)
- the file is overwritten (not appended) on each write — it always reflects the latest resumable state
- when context reset is disabled, this file is not written

Handoff template:

```markdown
# Handoff: [Feature Name]

**Session:** <session-id>
**Written At:** <ISO timestamp>
**Plan:** .dev-kit/sessions/<session-id>/plan.md
**Last Checkpoint:** P<N>-<name>

## Resume Point

- **Current Phase:** P<N> — <phase-name>
- **Phase Status:** [executing | next pending phase]
- **Completed Tasks This Phase:** [list with short SHA]
- **Next Task:** Task <N>: <name>
- **Remaining Tasks This Phase:** [count]
- **Remaining Phases:** [list]

## Completed Phase Summary

| Phase | Checkpoint | Tasks | Key Interfaces |
|---|---|---|---|
| P1 | P1-<name>.json | <count> passed | <interfaces> |

## Active Context

- **Working Branch:** <branch name>
- **Uncommitted Changes:** [yes/no — if yes, list files]
- **Integration State:** [last integration gate result]
- **Known Blockers:** [none or description]

## Recovery Instructions

1. Read this file and the approved plan.md
2. Read the latest checkpoint JSON
3. Read progress.md for task-level detail
4. Resume from Task <N> in Phase P<N>
5. Do not re-run completed phases unless explicitly requested
```

The orchestrator also writes `handoff.md` in these additional situations:

- after every 4th consecutive task completion within a phase (even before the phase checkpoint)
- when the user explicitly requests context reset preparation
- before escalating to the user for a failure that may cause a long pause

### 4-6. Complete Execute

After the final phase checkpoint:

- run the highest-level verification command again on the integrated system
- run the full test suite
- set `current_phase` to `review-execute`
- keep `status` as `in_progress`
- keep `plan_status` as `approved`
- set `next_action` to `Run review-execute. Read .dev-kit/sessions/<session-id>/plan.md.`
- update `updated_at`

Refresh `.dev-kit/current.json` with the new `updated_at`.

## Recovery

On re-entry after interruption:

1. resolve the preferred session from the shared recovery helper
2. read `state.json`
3. if `handoff.md` exists, read it for a consolidated resume snapshot including the current task position and integration state
4. inspect `phase_status`
5. inspect existing checkpoint JSON
6. find the last fully checkpointed phase
7. read `progress.md` if it exists to identify the last validated task within the current phase

Resume rules:

- if no checkpoint exists, restart the current phase from the beginning
- if a phase checkpoint exists, do not re-run that phase unless the user explicitly requests rollback
- if merge or integration stopped before checkpoint but the plan still stands, re-enter that phase in `executing` state
- if `progress.md` shows a task within the current phase as PASS but the phase has no checkpoint, resume from the next incomplete task in that phase rather than restarting the entire phase
- if `handoff.md` exists and is newer than the latest checkpoint, use its Resume Point section to identify the exact next task rather than scanning `progress.md`

## Failure Response

Escalate to the user when:

- a task fails validation 3 times
- a worktree merge assumption is invalid
- phase integration fails twice for different attempted fixes
- the approved plan contract is missing critical information
- the environment cannot run required verification
- a git commit fails due to unexpected repository state (dirty index, merge conflict from parallel work)

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
| Skipping final `review-execute` because execute already validated tasks | Removes the independent final verification step |
| Writing progress.md from workers or validators | Breaks single-writer state; only the orchestrator appends |
| Writing handoff.md from workers or validators | Same as progress.md — single-writer state; only the orchestrator writes |
| Writing handoff.md when context reset is disabled | Unnecessary artifact noise for sessions that do not need it |

## Minimal Checklist

- [ ] Was the full approved plan read before execution?
- [ ] Did `plan_status` already equal `approved` before execute began?
- [ ] Did only the orchestrator update `.dev-kit/current.json` and `state.json`?
- [ ] Did every task pass isolated validation?
- [ ] Did each phase pass its integration gate before checkpointing?
- [ ] Was each task result appended to `progress.md`?
- [ ] Were task commits created following the SHOULD-level git commit guidance?
- [ ] Was `handoff.md` written at each checkpoint when context reset is enabled?
- [ ] Does `next_action` point to `review-execute` when execute completes?

## Transition

After execute finishes:

- proceed to `review-execute`
- if repeated failures point to an unclear bug, use `systematic-debugging`
- if the approved plan proves structurally wrong, stop and report a planning contract violation
