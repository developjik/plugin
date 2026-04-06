---
name: review-execute
description: Final independent verification for the unified Dev Kit workflow. Although the internal skill name remains review-execute during migration, user-facing flow and session state should refer to this step as review.
---

# Review Work

Independently verifies the final result of the approved `plan.md`. This is the only user-visible review step in the workflow.

## Core Principle

Review is isolated from execution context. The reviewer judges the current codebase against the approved plan and verification criteria, not against execution logs or worker narratives. Review verifies results; it does not reopen planning.

## Hard Gates

1. **Do not receive execution context.** No worker output, no execution summaries, no task-level validator results.
2. **Read `plan.md` directly.** Review uses the canonical approved plan, not a summary.
3. **Run verification independently.** Re-run stated verification commands and the full test suite yourself.
4. **Do not modify code.** Review reports findings only.
5. **Verdict is PASS or FAIL.** No conditional pass.
6. **State and user-facing text say `review`.** The internal skill id may remain `review-execute`, but the session phase is `review`.
7. **Do not route review failures back to planning.** Planning quality was closed before execute.

## When To Use

- After `execute` completes
- When the user asks to review or verify the implementation
- When final independent verification is needed before calling a session complete

## When NOT To Use

- While execute is still in progress
- When no canonical approved `plan.md` exists
- When `plan_status` is not `approved`
- For general diff review unrelated to plan execution

## Input

Canonical input:

```text
.dev-kit/sessions/<session-id>/plan.md
```

Session discovery order:

1. If the user provides a session path, use it
2. Otherwise, read `.dev-kit/current.json`
3. If the pointer is missing, invalid, or not resumable, use the shared session-recovery helper to scan `.dev-kit/sessions/*/state.json`
4. If no resumable session exists, stop and tell the user to run `execute` or provide an explicit session path

Read:

- `.dev-kit/sessions/<session-id>/state.json`
- `.dev-kit/sessions/<session-id>/plan.md`
- `.dev-kit/sessions/<session-id>/plan-review.md`

## Review Process

### Step 1: Load The Approved Plan

Read `plan.md` directly and extract:

- goal
- scope
- file structure mapping
- tasks and acceptance criteria
- verification strategy
- execution strategy sections that affect expected final state

Confirm that:

- `plan_status` is `approved`
- `plan-review.md` exists as the record of the final planning critique
- the approved plan contract is present enough for review to judge the result

If the approved plan contract is missing, contradictory, or unverifiable at review time, stop and report a planning contract violation rather than mutating the normal workflow state model.

### Step 2: Inspect Code Against Plan

Verify:

1. all planned files exist where expected
2. planned behavior is reflected in the code
3. no placeholder or debug artifacts remain
4. no unexpected changes outside plan scope materially alter the result
5. `.dev-kit/**` workflow metadata is ignored except for reading state
6. final behavior matches the plan's acceptance basis

### Step 3: Run Verification

Run:

1. all explicit verification commands from the plan
2. the highest-level verification strategy command
3. the full test suite for regressions

### Step 4: Reach Verdict

**PASS** only if all are true:

- plan goals are met
- acceptance criteria are satisfied at the final system level
- all required verification passes
- no regressions are found
- no placeholder or debug artifacts remain

Otherwise, verdict is **FAIL** due implementation drift from the approved plan.

## Review Artifact

Write:

```text
.dev-kit/sessions/<session-id>/review.md
```

Use this structure:

```markdown
# [Feature Name] Review

**Date:** YYYY-MM-DD HH:MM
**Plan Document:** `.dev-kit/sessions/<session-id>/plan.md`
**Plan Version:** [integer]
**Verdict:** PASS / FAIL

## 1. Scope Verification

| Planned Area | Result | Notes |
|---|---|---|
| `...` | PASS / FAIL | ... |

## 2. Verification Results

| Command | Result | Notes |
|---|---|---|
| `...` | PASS / FAIL | ... |

## 3. Code Hygiene

- [ ] No placeholders
- [ ] No debug code
- [ ] No commented-out blocks
- [ ] No material drift outside plan scope

## 4. Findings

- [file path and line references for failures]

## 5. Overall Assessment

[Why the verdict is PASS or FAIL]
```

## State Update

After saving `review.md`, update `.dev-kit/sessions/<session-id>/state.json`:

- set `artifacts.review` to `.dev-kit/sessions/<session-id>/review.md`
- update `updated_at`

Then set state according to the verdict:

- If `PASS`:
  - `status`: `completed`
  - `current_phase`: `review`
  - `plan_status`: `approved`
  - `next_action`: `Session complete.`
- If `FAIL` due implementation drift from the approved plan:
  - `status`: `in_progress`
  - `current_phase`: `execute`
  - `plan_status`: `approved`
  - `next_action`: `Run execute. Address review findings against .dev-kit/sessions/<session-id>/plan.md.`

Review does not write any exceptional workflow state.

Then update `.dev-kit/current.json` according to the outcome:

- If `PASS`, remove `.dev-kit/current.json` if it still points at this now-completed session
- If `FAIL`, refresh `.dev-kit/current.json` with the same pointer and new `updated_at`

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Reading execute logs to help review | Breaks isolation |
| Trusting previous verification results | Final review must verify current state |
| Treating `.dev-kit/**` as product code | Workflow metadata is not part of implementation scope |
| Recording the phase as `review-execute` in state | User-facing state should say `review` |
| Sending review failures back to planning | Review verifies output, not plan quality |

## Minimal Checklist

- [ ] Was `plan.md` read directly?
- [ ] Was review isolated from execute context?
- [ ] Were required verification commands re-run?
- [ ] Was `review.md` saved?
- [ ] Does state now point to completion or execute?

## Transition

- PASS -> session is complete
- FAIL due implementation drift -> return to `execute`
- planning contract violation -> stop and report the issue outside the normal workflow state model
