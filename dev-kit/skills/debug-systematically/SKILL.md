---
name: debug-systematically
description: Use when encountering any bug, test failure, or unexpected behavior. Enforces a strict reproduce-first, root-cause-first, failing-test-first debugging workflow before fixing.
---

# Systematic Debugging

This is a strict debugging workflow for bugs, test failures, and unexpected behavior.

The goals are simple:

1. Fix the cause, not the symptom.
2. Prevent guess-based patches.
3. Lock the failure before changing code.

## Hard Gates

Follow these rules without exception:

1. Do not modify code before you can reproduce the failure or make it observable.
2. Do not modify code before you can state a root-cause hypothesis.
3. Do not modify code before you have a failing test or an equivalent failure guard.
4. Validate one hypothesis at a time.
5. Do not bundle "while I'm here" refactors into the fix.
6. If three fix attempts fail, stop patching and question the structure.

Breaking this process counts as debugging failure.

## When To Use

Use this skill when:

- A test is failing
- A local or production bug appears
- A response, state transition, render, or query result is not what you expected
- You are investigating slowdowns, timeouts, race conditions, or flaky failures
- A previous fix already failed once and the issue came back

These rationalizations are not allowed:

- "It looks simple, I can just patch it"
- "There is no time, I will fix first and investigate later"
- "It is probably this, let me just try it"

## Required Output Contract

Internally, do not consider the work complete unless all seven items exist:

1. **Problem statement:** one sentence defining what is wrong
2. **Reproduction path:** how the failure is reproduced or observed
3. **Evidence:** what was actually observed
4. **Root-cause hypothesis:** why you believe the problem occurs
5. **Failing guard:** a failing test, repro script, or log/assertion-based check
6. **Fix:** one change that addresses the root cause
7. **Verification:** results from rerunning the repro path and related tests

If any item is missing, the debugging work is not done.

## Workflow

Follow this sequence in order.

### Phase 1. Define The Problem

Compress the issue first:

- What is the expected behavior?
- What is the observed behavior?
- What is the scope of impact?
- Is it consistent or intermittent?

Use this format:

```text
Problem: <expected> but got <actual> under <condition>
```

Do not mix symptoms with guesses.

```text
Good: Product detail API returns 500 when brand is null.
Bad: Serializer is broken because brand mapping seems wrong.
```

### Phase 2. Reproduce Or Instrument

Before fixing anything, you must be able to observe the failure again.

Priority order:

1. Reproduce with an existing test
2. Reproduce with a minimal integration test
3. Reproduce with a unit test
4. Observe with a repro script or command
5. Add logging or instrumentation and observe it

Rules:

- Make the repro path as small as possible.
- Even if the bug appears in the UI, prefer reproducing it in a lower layer if possible.
- For intermittent failures, improve observability with logs, inputs, timing, and concurrency conditions.
- If you still cannot reproduce it, do not jump to a fix. Increase observability first.

If reproduction is failing, do this instead:

1. Record the exact inputs
2. Check environment differences
3. Inspect recent changes
4. Add logs at key boundaries
5. Search for a smaller condition that produces the same symptom

### Phase 3. Gather Evidence

Collect observable facts only.

Always check:

- Full error message and stack trace
- Failing input values
- Recent files or commits related to the issue
- Environment or config differences
- Call path and data flow

For multi-component issues, inspect every boundary.

Examples:

- controller -> application -> service -> repository
- client -> API -> external service
- scheduler -> batch service -> database

At each boundary, check:

- What came in
- What went out
- What values changed
- Under what condition it fails

Do not fix anything until you know where the problem actually lives.

### Phase 4. Isolate Root Cause

Form one root-cause hypothesis only.

Format:

```text
Hypothesis: <root cause> because <evidence>
```

A good hypothesis:

- points to one cause
- connects directly to observed evidence
- can be disproved with a small experiment

Bad examples:

- "There is probably some async problem somewhere"
- "Serialization in general seems unstable"

If the symptom appears deep in the stack, trace backward to the original trigger.

### Phase 5. Lock The Failure

Before changing production code, lock the failure in place.

Priority order:

1. Automated failing test
2. Regression case added to an existing test
3. Minimal repro script
4. Temporary log/assertion-based guard

Rules:

- Prefer automated tests when possible.
- It must fail before the fix.
- It must pass after the fix.
- The test name should describe exactly what broke.

If you can express the failure as a test, use `test-driven-development` alongside this skill.

### Phase 6. Implement A Single Fix

The fix addresses one hypothesis only.

Allowed:

- The minimal code change that addresses the root cause
- Minimal support changes needed for verification

Not allowed:

- Bundling multiple related-seeming fixes
- Refactoring at the same time
- Formatting, cleanup, or renaming slipped in with the fix
- Adding null guards without evidence
- Swallowing exceptions

If the fix fails, go back to Phase 1 or Phase 3. Your hypothesis was wrong or incomplete.

### Phase 7. Verify And Close

Do not finish until all of these are true:

1. The original repro path no longer fails
2. The new failing guard now passes
3. Related tests still pass
4. You can explain why the fix blocks the cause, not just the symptom

For flaky bugs, do not stop after one pass. Repeat the repro or vary the conditions.

## Stop Conditions

Reframe the work if any of these happen.

### 1. Reproduction Failed

If you still cannot reproduce it after several attempts:

- you may lack observability
- the environment may differ
- the problem statement may be wrong

Do not change code without a repro or an observable signal.

### 2. Three Failed Fixes

If three fix attempts miss:

- your understanding is wrong, or
- the issue is structural, such as shared state, boundary design, or responsibility split

At that point, stop patching and discuss structure.

### 3. No Failing Guard

If you cannot create a failing test or equivalent guard, do not declare success. At minimum, leave a reproducible command and recorded observation.

## Red Flags

If you catch yourself thinking any of these, stop and go back:

- "I can probably fix it by changing this one line"
- "I will look at logs later"
- "I will add the test after the patch"
- "I should fix a couple of related things while I am here"
- "The error disappeared, so the cause does not matter"

## Minimal Checklist

- [ ] Defined the problem in one sentence
- [ ] Reproduced the failure or made it observable
- [ ] Collected evidence
- [ ] Formed one root-cause hypothesis
- [ ] Created a failing guard before the fix
- [ ] Applied one fix only
- [ ] Verified the same repro path after the fix

## Completion Standard

Debugging is complete only when:

- the problem statement is clear
- the failure was locked before the fix
- the fix connects directly to the cause
- verification evidence remains

If any of these are missing, the debugging work is not done.
