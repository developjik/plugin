---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior. Enforces a strict reproduce-first, root-cause-first, failing-test-first debugging workflow before fixing.
---

# Systematic Debugging

A strict debugging workflow. Use when dealing with bugs, test failures, or unexpected behavior.

Core objectives:

1. Fix the cause, not the symptom.
2. Prevent guess-based fixes.
3. Lock failures with tests before fixing.

## Hard Gates

These rules have no exceptions.

1. **Do not fix until you can reproduce or observe the failure.**
2. **Do not fix until you state a root-cause hypothesis.**
3. **Do not fix until you create a failing test or equivalent reproduction device.**
4. **Verify one hypothesis at a time.**
5. **No "while I'm here" refactoring during a fix.**
6. **After 3 failed fix attempts, suspect a structural problem before patching further.**

Violating this process constitutes a debugging failure.

## When To Use

Use this skill when:

- A test fails
- A bug occurs in production or locally
- Responses, state, rendering, or query results differ from expectations
- Investigating performance degradation, timeouts, race conditions, or intermittent failures
- Something breaks again after being fixed once or more

The following excuses are not accepted:

- "It looks simple enough to just fix"
- "No time, let's just patch it"
- "I think it's this, let me just change it"

## Required Output Contract

When using this skill, the following items must be locked down internally:

1. **Problem statement**: One-sentence definition of what is wrong
2. **Reproduction path**: How to reproduce or observe the failure
3. **Evidence**: Actual observation results
4. **Root-cause hypothesis**: Why this problem is believed to occur
5. **Failing guard**: A failing test, reproduction script, or log assertion
6. **Fix**: A single change targeting the cause
7. **Verification**: Post-fix reproduction path and related test results

If any of these 7 items are missing, the work is not done.

## Workflow

Follow this order strictly.

### Phase 1. Define The Problem

First, distill the problem:

- What is the expected behavior?
- What is the observed behavior?
- What is the blast radius?
- Is it always reproducible or intermittent?

Output format:

```text
Problem: <expected> but got <actual> under <condition>
```

Do not mix symptoms with speculation.

```text
Good: Product detail API returns 500 when brand is null.
Bad: Serializer is broken because brand mapping seems wrong.
```

### Phase 2. Reproduce Or Instrument

Before fixing, you must be able to see the failure again.

Priority:

1. Reproduce with an existing test
2. Reproduce with a minimal integration test
3. Reproduce with a unit test
4. Observe via a reproduction script or command
5. Observe by adding logging/instrumentation

Rules:

- Make the reproduction path as small as possible.
- If a bug only appears in the UI but can be reproduced at a lower layer, prefer the lower layer.
- For intermittent failures, add logging, input capture, timing, and concurrency context to improve observability.
- If it cannot be reproduced, do not proceed to fixing — increase observability instead.

When reproduction is not possible:

1. Record input values
2. Check environment differences
3. Check recent changes
4. Add logs at each boundary
5. Search for a smaller condition that produces the same symptom

### Phase 3. Gather Evidence

Collect only observable facts.

Always check:

- Full error message and stack trace
- Failing input values
- Recently changed files or commits
- Environment/configuration differences
- Call paths and data flow

For multi-component problems, check at every boundary.

Examples:

- controller -> application -> service -> repository
- client -> API -> external service
- scheduler -> batch service -> database

At each boundary, check:

- What came in?
- What went out?
- What values were transformed?
- Under what conditions does it break?

Do not fix until the problem location is pinpointed.

### Phase 4. Isolate Root Cause

Pose exactly one cause candidate.

Format:

```text
Hypothesis: <root cause> because <evidence>
```

A good hypothesis:

- Points to a single cause
- Connects to observed evidence
- Is falsifiable with a small experiment

Bad hypothesis examples:

- "There seems to be an async problem somewhere"
- "The whole serialization layer seems unstable"

Trace the cause back to its source. If the error appears deep in the stack, trace the input's origin rather than treating the symptom.

### Phase 5. Lock The Failure

Lock the failure before fixing.

Priority:

1. Automated failing test
2. Regression case added to an existing test
3. Minimal reproduction script
4. Temporary verification via log/assertion

Rules:

- Create an automated test when possible.
- It must fail before the fix.
- It must pass via the same path after the fix.
- The test name must reveal what broke.

Write the test using a TDD approach: the test must fail before the fix and pass after.

### Phase 6. Implement A Single Fix

The fix addresses one hypothesis only.

Allowed:

- Minimal code change directly addressing the cause
- Minimal auxiliary changes needed for verification

Prohibited:

- Bundling multiple "seems related" fixes
- Refactoring combined with fixing
- Sneaking in formatting/cleanup/renaming
- Adding null-guards without evidence
- Swallowing exceptions

If the fix fails, immediately return to Phase 1 or Phase 3. The previous hypothesis was wrong.

### Phase 7. Verify And Close

All of the following must be satisfied to conclude:

1. The original reproduction path no longer fails.
2. The new failing guard passes.
3. Related tests are not broken.
4. You can explain how the fix blocks the cause, not just the symptom.

For intermittent bugs, a single pass is not enough. Verify with repeated execution or under varied conditions.

## Stop Conditions

Stop and reframe in the following situations.

### 1. Reproduction Failed

If reproduction fails after multiple attempts:

- Check whether observability is insufficient.
- Check for environment differences.
- Check whether the problem definition is wrong.

Changing code without reproduction is prohibited.

### 2. Three Failed Fixes

If three consecutive fixes miss the mark, conclude that:

- Your current understanding is wrong, or
- The problem is likely a structural issue — shared state, boundary design, responsibility separation

From this point, what's needed is a structural discussion, not a "fourth patch."

### 3. No Failing Guard

If you cannot create a failing test or equivalent reproduction device, do not declare completion. At minimum, leave behind a reproduction command and observation results.

## Red Flags

If any of these thoughts occur, stop immediately and return to an earlier phase:

- "Let me just change this one line"
- "I'll check the logs later, let me try fixing first"
- "I'll add tests later"
- "Let me fix this and that at the same time"
- "The error is gone, so the cause doesn't matter"

## Minimal Checklist

During execution, self-verify against this checklist:

- [ ] Problem defined in one sentence
- [ ] Failure reproduced or made observable
- [ ] Evidence collected
- [ ] Single root-cause hypothesis formulated
- [ ] Failing guard created before fix
- [ ] Only a single fix applied
- [ ] Verified via the same path after fix

## Completion Standard

This skill's completion standard is not "the code changed."

Completion requires:

- Problem definition is clear
- Failure was locked before fixing
- Fix is connected to the cause
- Verification results are documented

Without all four, debugging is not complete.
