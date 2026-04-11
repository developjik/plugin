---
name: evaluator-calibration
description: Tighten or rebalance evaluator behavior with explicit thresholds, anti-patterns, and few-shot examples when the evaluator is too generous or inconsistent.
---

# Evaluator Calibration

Use this skill when the evaluator keeps missing obvious problems, is too generous with mediocre work, or drifts away from the quality bar you actually care about.

## Core Principle

Do not ask the generator to become its own harsh critic. Make the evaluator better at skepticism instead.

## Calibration Workflow

### 1. Collect Misses

Gather examples where a human judgment and evaluator judgment diverged.

Common misses:

- obvious UI bugs dismissed as acceptable
- generic design scored too highly
- "works in theory" behavior counted as done without live verification
- broad praise without concrete evidence

### 2. Turn Taste Into Criteria

For subjective work, rewrite taste as explicit principles.

Examples:

- "beautiful" becomes coherence, originality, craft, and usability
- "serious QA" becomes reproducible bugs, threshold gating, and evidence from actual interaction

### 3. Add Thresholds

Avoid evaluators that only narrate.

Require:

- numeric or ordinal scores
- hard fail conditions
- explicit reproduction steps for bugs
- a recommendation to refine, pivot, or accept

### 4. Add Examples

Use a few calibrated examples to show what high, medium, and low quality look like.

- keep examples short and discriminative
- include both good and bad cases
- show why the score was earned

Use the bundled fixtures as a starting point:

- `fixtures/calibration/frontend-good.md`
- `fixtures/calibration/frontend-bad.md`
- `fixtures/calibration/qa-good.md`
- `fixtures/calibration/qa-bad.md`

When calibrating QA, compare evaluator output against artifacts captured by `scripts/live_eval.py`.

### 5. Re-test

Run the evaluator on known examples and check whether it now catches the right failures.

## Session Notes

Write calibration updates into `evaluation.md` under a `Calibration` section so future rounds know what changed and why.
