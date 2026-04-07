---
name: review-execute
description: Final independent verification for the unified Dev Kit workflow stage `review-execute`.
---

# Review-Execute Work

Independently verifies the final result of the approved `plan.md`. This is the final `review-execute` stage in the mandatory `clarify -> planning -> execute -> review-execute` workflow.

## Core Principle

Review is isolated from execution context. The reviewer judges the current codebase against the approved plan and verification criteria, not against execution logs or worker narratives. Review verifies results; it does not reopen planning.

## Hard Gates

1. **Do not receive execution context.** No worker output, no execution summaries, no task-level validator results.
2. **Read `plan.md` directly.** Review uses the canonical approved plan, not a summary.
3. **Run verification independently.** Re-run stated verification commands and the full test suite yourself.
4. **Do not modify code.** Review reports findings only.
5. **Verdict is PASS or FAIL.** No conditional pass.
6. **State and user-facing text say `review-execute`.** Use `review-execute` consistently for the pipeline step, session phase, and skill invocation text.
7. **Do not route review failures back to planning.** Planning quality was closed before execute.

## When To Use

- After `execute` completes
- After the upstream `clarify` and `planning` phases have already materialized the approved plan consumed by execute
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
3. If the pointer is missing, invalid, or not resumable, use the shared session-recovery helper to scan `.dev-kit/sessions/*/state.json` for sessions with `status` in `in_progress` or `paused`
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

### Evaluator Calibration

Calibration anchors the verdict to the approved plan's acceptance criteria. The examples below are generic patterns; apply them to the specific plan being reviewed.

**PASS examples** — these patterns warrant PASS when the plan's acceptance criteria are satisfied:

- all planned behavior works as specified, even if the implementation approach differs from what the plan described, as long as acceptance criteria are met
- minor cosmetic differences (whitespace, variable naming style) that do not affect behavior or violate plan requirements
- additional defensive code (error handling, input validation) beyond what the plan specified, provided it does not alter the planned behavior
- test coverage that exceeds plan requirements

**FAIL examples** — these patterns warrant FAIL because acceptance criteria are not met:

- a planned endpoint or function exists but returns incorrect results for the documented scenarios
- verification commands specified in the plan do not pass
- placeholder implementations (TODO comments, stub functions, hardcoded values standing in for real logic)
- missing files that the plan explicitly lists as deliverables
- regressions in existing functionality detected by the test suite

**NOT grounds for FAIL** — these observations fall outside the plan's acceptance criteria:

- "the code could be more efficient" when no performance criterion exists in the plan
- "this module should also be refactored" when the module is outside the plan's scope boundary
- "the UI could look better" when no visual design criterion exists in the plan
- "additional tests should be written" when the plan's verification strategy is already satisfied
- style preferences not codified in the project's linter or the plan's acceptance criteria

**Boundary cases** — when the evidence is ambiguous, apply these tiebreakers:

1. re-read the plan's acceptance criteria literally — if the criterion says "endpoint returns 200 on valid input," verify exactly that, not whether the response body is optimally structured
2. if a verification command intermittently fails, re-run it — a consistent failure is FAIL; a transient environment issue is not grounds for FAIL if the underlying behavior is correct
3. out-of-scope changes that are present but harmless do not cause FAIL unless they materially alter planned behavior or introduce regressions

### Step 4: Reach Verdict

Consult the Evaluator Calibration section above before applying the verdict criteria.

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

### Low-Profile Compact Review

When `execution_profile` is `low`, the review artifact MAY use this compact format:

```markdown
# [Feature Name] Review

**Verdict:** PASS / FAIL
**Plan Version:** [integer]

## Verification Results

| Command | Result |
|---|---|
| `...` | PASS / FAIL |

## Assessment

[1-3 sentences: why PASS or FAIL]
```

The compact review omits: Scope Verification table, Code Hygiene checklist, detailed Findings. These are required for medium and high profiles. If the verdict is FAIL, the compact review MUST still include file path and line references for the failure.

## State Update

After saving `review.md`, update `.dev-kit/sessions/<session-id>/state.json`:

- set `artifacts.review` to `.dev-kit/sessions/<session-id>/review.md`
- update `updated_at`

Then set state according to the verdict:

- If `PASS`:
  - `status`: `completed`
  - `current_phase`: `review-execute`
  - `plan_status`: `approved`
  - `next_action`: `Session complete.`

Recommended state write pattern:

```bash
python3 ./scripts/dev_kit_state.py write-json --path ".dev-kit/sessions/<session-id>/state.json" <<'JSON'
{...}
```

`failure_reason` should remain `null` on PASS.

- If `FAIL` due implementation drift from the approved plan:
  - `status`: `in_progress`
  - `current_phase`: `execute`
  - `plan_status`: `approved`
  - `next_action`: `Run execute. Address review findings against .dev-kit/sessions/<session-id>/plan.md.`
  - `failure_reason`: `null`

- If `FAIL` due infra or external blocker requiring user action (max retry or contract violation):
  - `status`: `paused`
  - `current_phase`: `review-execute`
  - `plan_status`: `approved`
  - `next_action`: `Resume from the same review point after dependency is restored.`
  - `failure_reason`: `...` (required)

Review does not write any exceptional workflow state.

Then update `.dev-kit/current.json` according to the outcome:

- If `PASS`, remove `.dev-kit/current.json` if it still points at this now-completed session
- Otherwise, refresh `.dev-kit/current.json` with the same pointer and new `updated_at`

Use the helper command to avoid races:

```bash
python3 ./scripts/dev_kit_state.py clear-current --session-id <session-id>
python3 ./scripts/dev_kit_state.py write-json --path ".dev-kit/current.json" <<'JSON'
{...}
```
```

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Reading execute logs to help review | Breaks isolation |
| Trusting previous verification results | Final review must verify current state |
| Treating `.dev-kit/**` as product code | Workflow metadata is not part of implementation scope |
| Recording the phase as `review` in state | The canonical session phase is `review-execute` |
| Sending review failures back to planning | Review verifies output, not plan quality |
| Failing based on subjective quality beyond plan criteria | Review judges against the approved plan, not ideal code |

## Minimal Checklist

- [ ] Was `plan.md` read directly?
- [ ] Was review isolated from execute context?
- [ ] Were required verification commands re-run?
- [ ] Was `review.md` saved?
- [ ] Were FAIL verdicts grounded in plan acceptance criteria, not subjective quality?
- [ ] Does state now point to completion or execute?

## Transition

- PASS -> session is complete
- FAIL due implementation drift -> return to `execute`
- planning contract violation -> stop and report the issue outside the normal workflow state model

This stage never replaces the upstream flow. It is the final verifier for work that has already passed through `clarify`, `planning`, and `execute`.
