---
name: harness-orchestrator
description: Run planner-generator-evaluator loops for long-running application development with sprint contracts, file-based handoffs, and explicit reset-vs-compaction decisions.
---

# Harness Orchestrator

Use this skill when a short app prompt needs to become a durable, multi-step build workflow instead of a one-shot coding attempt.

This skill packages the core lessons from Anthropic's March 24, 2026 engineering article, "Harness design for long-running application development."

## Hard Rules

1. Separate planning, generation, and evaluation. Do not let the builder silently grade its own work as the main gate.
2. Make the planner ambitious on product scope and design direction, but conservative about premature low-level implementation commitments.
3. Before each sprint, the generator and evaluator must agree on a testable sprint contract.
4. Prefer file-based artifacts under `.harness-design-kit/` over long conversational state.
5. Use evaluator gating by default for subjective quality or capability-boundary work. Turn it down only for trivial, deterministic tasks.
6. Decide explicitly between compaction and context reset. Do not drift into resets accidentally.
7. Treat `events.jsonl` as append-only.

## Session Contract

Use this directory layout at the workspace root:

```text
.harness-design-kit/
├── current.json
└── sessions/
    └── <session-id>/
        ├── state.json
        ├── events.jsonl
        ├── product-spec.md
        ├── design-brief.md
        ├── sprint-contract.md
        ├── evaluation.md
        ├── progress.md
        └── handoff.md
```

Initialize a session when one does not exist:

```bash
python3 "${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-.}}/scripts/harness_state.py" init "<goal>" app
```

Inspect the current runtime state at any point:

```bash
python3 "${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-.}}/scripts/harness_run.py" status
```

## Choosing The Harness

Start by deciding three things and recording them in `state.json`.

- `mode`
  - `app` for full-stack application work
  - `frontend` for design-heavy UI iteration
- `execution_mode`
  - `continuous` when the current model can stay coherent with compaction
  - `reset` when context anxiety, drift, or repeated forgetting makes a clean-slate handoff safer
  - `auto` when the harness should begin continuous and promote itself to reset if degradation appears
- `evaluator_mode`
  - `always` for subjective quality, QA-heavy, or capability-boundary work
  - `final-pass` when full evaluation is only needed at the end of a larger chunk
  - `edge-only` when evaluator time should be spent mainly near the model's capability boundary
  - `off` only for small deterministic tasks

## Workflow

### 1. Plan

- use the `planner` agent to expand the short prompt into `product-spec.md`
- capture target user, workflow, design direction, non-goals, AI features if useful, and sprint candidates
- keep implementation notes high-level enough that downstream agents can adapt

### 2. Define The First Contract

- the `generator` writes `sprint-contract.md`
- treat `sprint-contract.md` as the active work contract even if the unit is larger than a classic sprint
- the contract must include:
  - sprint objective
  - deliverables
  - out-of-scope items
  - verification steps
  - pass or fail exit criteria
- the evaluator reviews the contract before coding begins

### 3. Build

- the `generator` implements only the agreed sprint
- update `progress.md` with actual changes, verification evidence, and known risks
- do a short self-check before asking for evaluation

### 4. Evaluate

- use `qa-evaluator` for application work
- test the real system: UI flows, API behavior, and storage where relevant
- prefer `python3 .../scripts/live_eval.py run --url <app-url>` before recording the evaluation when a live URL exists
- score each sprint on:
  - product depth
  - functionality
  - visual design
  - code quality
- if any criterion misses threshold, fail the sprint and write the reasons to `evaluation.md`

### 5. Iterate

- feed the evaluation back to the `generator`
- revise the contract if the failure exposed scope ambiguity
- repeat until the sprint passes or the user chooses to stop
- use `python3 .../scripts/harness_run.py advance` to move the recorded phase forward once the current gate is satisfied

### 6. Reset When Needed

- if the task starts drifting, use `context-reset-handoff`
- write `handoff.md` with enough state for a fresh agent to resume cleanly
- then continue from the new session context instead of trying to rescue a degraded one indefinitely
- if the session is running in `execution_mode=auto`, `python3 .../scripts/harness_run.py check-reset` can promote it into `handoff`

## When To Skip Or Soften Evaluation

Full evaluator involvement is optional only when all of these are true:

- the task is small and deterministic
- correctness is easy to verify directly
- the model is comfortably above the task's difficulty
- the extra loop would mostly add latency and cost

If one of those stops being true, move to `edge-only`, `final-pass`, or `always`.

Runtime notes:

- `always`
  - `build` advances directly into `evaluate`
- `final-pass`
  - request the evaluator gate with `python3 .../scripts/harness_state.py request-final-pass "reason"` before advancing from `build`
- `edge-only`
  - request the evaluator gate with `python3 .../scripts/harness_state.py request-evaluation "reason"` only when the work reaches the boundary
- `off`
  - `build` skips evaluation and advances immediately

## Done When

- [ ] `product-spec.md` exists and matches the user's request
- [ ] the active sprint contract is explicit and testable
- [ ] `evaluation.md` records the latest verdict
- [ ] `progress.md` explains what changed and what remains risky
- [ ] `handoff.md` is empty or clearly states the next restart point
