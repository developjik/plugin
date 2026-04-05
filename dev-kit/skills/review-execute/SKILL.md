---
name: review-execute
description: Use after execute completes to independently verify the implementation. Reads only the plan document and inspects the codebase from scratch — information-isolated from the execution context. Produces a structured review document with PASS/FAIL verdict. Triggers when the user says "review the work", "verify the implementation", "check if the plan was executed correctly".
---

# Review Work

Independently verifies implementation results using only the plan document and the codebase. Receives no information from the execution process.

## Core Principle

The reviewer shares no memory with the executor. The plan's stated goals and the current state of the codebase — these two alone are the basis for judgment.

## Hard Gates

1. **Do not receive execution context.** No logs from execute, no worker output, no diffs, no task completion summaries, no conversation history. The only input is the plan file path.
2. **Read the plan document directly.** Read the plan file from disk — not a summary or a passed-along description.
3. **Run all tests yourself.** Do not trust previous execution results. Run the full test suite and every verification command specified in the plan.
4. **Verdict is PASS or FAIL.** No conditional passes, no "almost done", no "only minor issues remain". Binary only.
5. **Save the review document to a file.** Review results must be saved as a structured document. Never end with a verbal report alone.
6. **Do not modify code.** This skill is read-only. If issues are found, report them — do not fix them.

## When To Use

- After execute execution is complete
- When the user says "review the work", "verify the implementation", "check if the plan was executed correctly"
- When implementation is done but independent verification is needed

## When NOT To Use

- While execute is still in progress
- When no plan document exists (use `planning` first)
- When the goal is a general code review (this skill verifies "implementation against plan")

## Input

The only input to this skill is the **plan file path**.

```
docs/sessions/<session-id>/plan.md
```

### Session Discovery

- If the user or resume skill provides a plan file path or session path, use it.
- Otherwise, scan `docs/sessions/` for the most recent session where execute is completed and review-execute is not yet completed.
- Read the plan from `docs/sessions/<session-id>/plan.md`

The following must never be provided as input:

- Execution logs or task completion summaries from execute
- Output or diffs from worker subagents
- Validation results from validator subagents
- Conversation history from the execution session

## Process

### Phase 1: Load and Analyze Plan Document

1. Receive the plan file path as input
2. Read the plan document directly from disk
3. Extract the following:
   - **Goal:** What this plan implements
   - **Work Scope:** In scope / Out of scope
   - **Task List:** Each task's name, acceptance criteria, and target files
   - **File Structure Mapping:** Complete list of files to be created or modified
   - **Commit Structure:** Commit messages and scope specified in the plan
   - **Test Commands:** All test execution commands specified in the plan

Use the extracted results as the foundation for the review document.

### Phase 2: Codebase Inspection

Inspect the codebase against the files specified in the plan.

1. **File existence check:** Verify that all files specified in the plan actually exist
2. **Content alignment check:** Inspect whether each file's content matches the plan's requirements (function signatures, type definitions, logic, etc.)
3. **Residual artifact check:**
   - Placeholder code (TODO, FIXME, "implement later", stub functions)
   - Debug code (console.log, print debugging, commented-out code blocks)
   - Unexpected changes outside the plan's scope
4. **Verify acceptance criteria per task.** Check each criterion stated in the plan one by one and record whether it is met.

### Phase 3: Test Execution

1. Run all **individual test commands** specified in the plan
2. Run the **full test suite** to check for regressions
3. Record each test's result (PASS/FAIL)
4. If any test fails, record the error message

### Phase 4: Git History Verification

1. Compare the commit structure specified in the plan against the actual `git log`
2. Verify that commit messages match the plan
3. Verify that each commit's change scope is appropriate (no unrelated changes mixed into a single commit)

### Phase 5: Verdict and Review Document

Combine results from Phases 2–4 to reach a verdict.

**PASS conditions (all must be met):**

- All files specified in the plan exist
- Each task's acceptance criteria are met
- All tests pass
- No regressions
- No placeholder or debug code remains

**FAIL (if any of the following apply):**

- A file specified in the plan is missing
- A test fails
- A regression is found
- Placeholder code remains
- The plan's goal is not achieved

After reaching a verdict, write and save the review document.

## Review Document

### Save Location

```
docs/sessions/<session-id>/review.md
```

(User preferences for review location override this default.)

### Document Structure

```markdown
# [Feature Name] Review

**Date:** YYYY-MM-DD HH:MM
**Plan Document:** `docs/sessions/<session-id>/plan.md`
**Verdict:** PASS / FAIL

---

## 1. File Inspection Against Plan

| Planned File | Status | Notes |
|---|---|---|
| `path/to/file` | OK / Missing / Mismatch | Details |

## 2. Test Results

| Test Command | Result | Notes |
|---|---|---|
| `pytest tests/...` | PASS / FAIL | Error details if failed |

**Full Test Suite:** PASS / FAIL (N passed, M failed)

## 3. Code Quality

- [ ] No placeholders
- [ ] No debug code
- [ ] No commented-out code blocks
- [ ] No changes outside plan scope

**Findings:**
- (Describe with file path and line number)

## 4. Git History

| Planned Commit | Actual Commit | Match |
|---|---|---|
| `feat: add X` | `abc1234 feat: add X` | OK / Mismatch |

## 5. Overall Assessment

(Summary of the overall judgment. If FAIL, describe specifically which items failed and why.)

## 6. Follow-up Actions

- (If FAIL: list of items that need to be fixed)
- (If PASS: record improvement suggestions if any)
```

### State Update

After the review document is saved, update the session index (`docs/sessions/<session-id>/index.md`):

1. **Files table:** Add row `review.md | review-execute | created`
2. **Pipeline Progress:** Check the `review-execute` checkbox
3. **Execution Log:** Add entry `review-execute-completed | Verdict: PASS/FAIL`
4. **Status and Next Action:**
   - If **PASS:** Update Status to `completed`, Next Action to `"Session complete. Consider simplify-code for a final quality pass."`
   - If **FAIL:** Keep Status as `in-progress`, Next Action to `"Fix issues and re-run execute, then review-execute."`
5. **Last Updated:** Update the timestamp

## When To Stop

Stop immediately and notify the user in the following situations:

- The plan file does not exist or cannot be read
- The test execution environment is not ready (e.g., dependencies not installed)
- The plan document format cannot be parsed

**When in doubt, do not guess — ask the user.**

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Reading execute execution logs to verify | Information isolation violation. Anchors on the executor's framing |
| Trusting previous test results instead of running tests | Environment may have changed after execution. Not independent verification |
| Finding issues and fixing them directly | Violates separation of reviewer and implementer roles |
| Giving a "close enough, PASS" verdict | No conditional passes. If criteria are not met, it is FAIL |
| Delivering review results verbally without saving a document | No verification record remains. Untraceable |
| Judging by criteria not in the plan | The reviewer judges only by the plan's criteria. Adding arbitrary standards is prohibited |
| Receiving a plan summary and verifying from that | Information is lost during summarization. The original must be read directly |

## Minimal Checklist

Self-check when review is complete:

- [ ] Read the plan document directly from disk
- [ ] Did not receive execute execution results as input
- [ ] Ran all tests myself
- [ ] Inspected all tasks in the plan
- [ ] Verdict is either PASS or FAIL
- [ ] Saved the review document to a file

## Transition

After review is complete:

- **PASS** → Report results to the user and suggest next steps (PR creation, deployment, etc.)
- **FAIL** → Report failure items to the user. If fixes are needed, suggest transitioning to the `execute` or `systematic-debugging` skill
- If the plan itself has issues → suggest returning to the `planning` skill to revise the plan

This skill itself **does not invoke the next skill.** It saves the review document, reports results, and lets the user decide the next step.
